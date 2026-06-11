from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

from backend.config import settings
from backend.database import Base, engine
from backend.middleware import AuthMiddleware
from backend.routers.auth_routers import _limiter
from backend.routers.auth_routers import router as auth_router
from backend.routers.bd_routers import router as bd_router
from backend.routers.extra_routers import router as extra_router
from backend.routers.ficha_routers import router as ficha_router
from backend.routers.orcamento_routers import router as orcamento_router
from backend.routers.param_routers import router as param_router
from backend.routers.produto_routers import router as produto_router
from backend.routers.relatorio_routers import router as relatorio_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="ERP de orçamentação para engenharia viária — Alta Noroeste Sinalização Viária",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)

# Rate limiter state
app.state.limiter = _limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS — restrito ao domínio de produção via env; dev permite localhost
_cors_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)

# AuthMiddleware deve vir APÓS o CORSMiddleware
app.add_middleware(AuthMiddleware)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(bd_router, prefix="/api/v1")
app.include_router(ficha_router, prefix="/api/v1")
app.include_router(orcamento_router, prefix="/api/v1")
app.include_router(param_router, prefix="/api/v1")
app.include_router(produto_router, prefix="/api/v1")
app.include_router(extra_router, prefix="/api/v1")
app.include_router(relatorio_router, prefix="/api/v1")


# Estáticos do backend (logo da empresa, etc.)
_STATIC = Path(__file__).parent / "static"
_STATIC.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(_STATIC)), name="static")


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "version": settings.APP_VERSION}


# Serve o frontend SPA (React Router, build estático). Os assets têm hash e
# vivem em /assets; rotas de aplicação (deep links) caem no fallback index.html.
# Deve vir por último para não sobrepor as rotas da API.
#
# Resolve o diretório do build em dois cenários:
#   - dev local: `frontend/build/client` (saída do `npm run build`)
#   - container: `frontend/` (Dockerfile copia build/client → /app/frontend)
_FRONTEND_ROOT = Path(__file__).parent.parent / "frontend"
_FRONTEND_DEV = _FRONTEND_ROOT / "build" / "client"
_FRONTEND = _FRONTEND_DEV if (_FRONTEND_DEV / "index.html").exists() else _FRONTEND_ROOT
_INDEX = _FRONTEND / "index.html"

if _INDEX.exists():
    _ASSETS = _FRONTEND / "assets"
    if _ASSETS.exists():
        app.mount("/assets", StaticFiles(directory=str(_ASSETS)), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_fallback(full_path: str):
        # Arquivo estático na raiz (favicon, .well-known, etc.)?
        if full_path:
            candidate = (_FRONTEND / full_path).resolve()
            if _FRONTEND.resolve() in candidate.parents and candidate.is_file():
                return FileResponse(str(candidate))
        # SPA: qualquer outra rota (incl. "/") devolve o index.html
        return FileResponse(str(_INDEX))

else:
    # Sem build do frontend (dev/API pura): mantém status JSON na raiz.
    @app.get("/", tags=["health"])
    def root():
        return {
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "ok",
        }
