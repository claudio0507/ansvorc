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

_RBAC: list[tuple[str, frozenset[str]]] = [
    ("/api/v1/bd-",        frozenset({"gestor_bd", "sponsor"})),
    ("/api/v1/fichas-",    frozenset({"parametrizador", "sponsor"})),
    ("/api/v1/clientes",   frozenset({"orcamentista", "parametrizador", "gestor_bd", "sponsor"})),
    ("/api/v1/orcamentos", frozenset({"orcamentista", "parametrizador", "sponsor"})),
]

# Prefixos que exigem startswith
_PUBLICAS_PREFIX = ("/api/v1/auth/", "/docs", "/redoc")
# Paths que exigem match exato
_PUBLICAS_EXACT  = ("/", "/openapi.json")


def _eh_publica(path: str) -> bool:
    if path in _PUBLICAS_EXACT:
        return True
    return any(path.startswith(p) for p in _PUBLICAS_PREFIX)


def _papeis_permitidos(path: str) -> frozenset[str] | None:
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
        papeis_ok = _papeis_permitidos(path)

        if papeis_ok is not None and papel not in papeis_ok:
            resp = JSONResponse(
                {"detail": f"Acesso negado. Seu papel '{papel}' não tem permissão nesta rota."},
                status_code=403,
            )
            await resp(scope, receive, send)
            return

        scope.setdefault("state", {})
        scope["state"]["usuario_id"] = int(payload["sub"])
        scope["state"]["papel"]      = papel

        await self.app(scope, receive, send)
