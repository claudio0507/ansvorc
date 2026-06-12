"""
Middleware de autenticação + RBAC por papel — ASGI puro com Response do Starlette.

Todas as rotas /api/v1/* são protegidas, exceto /api/v1/auth/* e health check.

Matriz de acesso:
  /api/v1/bd-*        → gestor_bd, sponsor
  /api/v1/fichas-*    → parametrizador, sponsor
  /api/v1/clientes*   → orcamentista, parametrizador, gestor_bd, sponsor
  /api/v1/orcamentos* → orcamentista, parametrizador, sponsor
"""

import jwt
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from backend.config import settings

_ALGORITMO = "HS256"

_TODOS_PAPEIS = frozenset({"orcamentista", "parametrizador", "gestor_bd", "sponsor"})

_RBAC: list[tuple[str, frozenset[str]]] = [
    ("/api/v1/bd-", frozenset({"gestor_bd", "sponsor"})),
    ("/api/v1/fichas-", frozenset({"parametrizador", "sponsor"})),
    (
        "/api/v1/clientes",
        frozenset({"orcamentista", "parametrizador", "gestor_bd", "sponsor"}),
    ),
    ("/api/v1/orcamentos", frozenset({"orcamentista", "parametrizador", "sponsor"})),
    ("/api/v1/dashboard", _TODOS_PAPEIS),
    ("/api/v1/unidades-medida", _TODOS_PAPEIS),
    ("/api/v1/parametros", frozenset({"parametrizador", "sponsor"})),
    ("/api/v1/componentes", frozenset({"parametrizador", "sponsor"})),
    ("/api/v1/produtos", frozenset({"parametrizador", "sponsor"})),
    ("/api/v1/item-fichas", frozenset({"parametrizador", "sponsor"})),
    # Orçamentistas e config: LEITURA ampla (proposta/dropdown). Escrita é restrita
    # em _RBAC_ESCRITA abaixo (parametrizador/sponsor apenas).
    ("/api/v1/orcamentistas", frozenset({"orcamentista", "parametrizador", "sponsor"})),
    ("/api/v1/config", _TODOS_PAPEIS),
]

# Override por método: prefixos cujas mutações (POST/PUT/PATCH/DELETE) exigem papéis
# mais restritos que a leitura. Consultado só em requisições mutantes.
_METODOS_MUTANTES = frozenset({"POST", "PUT", "PATCH", "DELETE"})
_RBAC_ESCRITA: list[tuple[str, frozenset[str]]] = [
    ("/api/v1/orcamentistas", frozenset({"parametrizador", "sponsor"})),
    ("/api/v1/config", frozenset({"parametrizador", "sponsor"})),
]

# Paths que exigem startswith
_PUBLICAS_PREFIX = ("/api/v1/auth/",)
# /docs, /redoc, /openapi.json só são públicos quando DEBUG=True (desabilitados em prod)
_PUBLICAS_PREFIX_DEBUG = ("/docs", "/redoc")
_PUBLICAS_EXACT_DEBUG = ("/openapi.json",)
# Paths que exigem match exato sempre
_PUBLICAS_EXACT = ("/", "/health")

# Extensões de arquivos estáticos — sempre públicas
_EXTENSOES_ESTATICAS = (
    ".css",
    ".js",
    ".ico",
    ".png",
    ".jpg",
    ".svg",
    ".woff2",
    ".woff",
    ".ttf",
)


def _eh_publica(path: str) -> bool:
    if path in _PUBLICAS_EXACT:
        return True
    if any(path.endswith(ext) for ext in _EXTENSOES_ESTATICAS):
        return True
    if any(path.startswith(p) for p in _PUBLICAS_PREFIX):
        return True
    # Frontend SPA: assets e rotas de aplicação (não-API) são servidos
    # estaticamente; a autenticação ocorre no cliente e nas chamadas /api/v1/*.
    if not path.startswith("/api/v1/"):
        return True
    if settings.DEBUG:
        if path in _PUBLICAS_EXACT_DEBUG:
            return True
        if any(path.startswith(p) for p in _PUBLICAS_PREFIX_DEBUG):
            return True
    return False


def _papeis_permitidos(path: str, metodo: str) -> frozenset[str] | None:
    # Mutações: regra de escrita mais restrita tem precedência, se houver.
    if metodo in _METODOS_MUTANTES:
        for prefixo, papeis in _RBAC_ESCRITA:
            if path.startswith(prefixo):
                return papeis
    for prefixo, papeis in _RBAC:
        if path.startswith(prefixo):
            return papeis
    return None


class AuthMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        path = request.url.path

        if _eh_publica(path):
            await self.app(scope, receive, send)
            return

        auth = request.headers.get("authorization", "")

        if not auth.startswith("Bearer "):
            resp = JSONResponse(
                {"detail": "Token não fornecido."},
                status_code=401,
                headers={"WWW-Authenticate": "Bearer"},
            )
            await resp(scope, receive, send)
            return

        token = auth.removeprefix("Bearer ").strip()

        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[_ALGORITMO])
        except jwt.ExpiredSignatureError:
            resp = JSONResponse(
                {"detail": "Token expirado."},
                status_code=401,
                headers={"WWW-Authenticate": "Bearer"},
            )
            await resp(scope, receive, send)
            return
        except jwt.InvalidTokenError:
            resp = JSONResponse(
                {"detail": "Token inválido."},
                status_code=401,
                headers={"WWW-Authenticate": "Bearer"},
            )
            await resp(scope, receive, send)
            return

        papel = payload.get("papel", "")
        papeis_ok = _papeis_permitidos(path, scope.get("method", "GET"))

        if papeis_ok is None and path.startswith("/api/v1/"):
            # Rota /api/v1/* não registrada no RBAC — nega por padrão
            resp = JSONResponse(
                {"detail": "Rota não autorizada."},
                status_code=403,
            )
            await resp(scope, receive, send)
            return

        if papeis_ok is not None and papel not in papeis_ok:
            resp = JSONResponse(
                {
                    "detail": f"Acesso negado. Seu papel '{papel}' não tem permissão nesta rota."
                },
                status_code=403,
            )
            await resp(scope, receive, send)
            return

        scope.setdefault("state", {})
        scope["state"]["usuario_id"] = int(payload["sub"])
        scope["state"]["papel"] = papel

        await self.app(scope, receive, send)
