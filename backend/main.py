from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import settings
from backend.database import Base, engine
from backend.middleware import AuthMiddleware
from backend.routers.auth_routers import router as auth_router
from backend.routers.bd_routers import router as bd_router
from backend.routers.ficha_routers import router as ficha_router
from backend.routers.orcamento_routers import router as orcamento_router
from backend.routers.relatorio_routers import router as relatorio_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Cria tabelas se não existirem (dev/primeiro deploy)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="ERP de orçamentação para engenharia viária — Alta Noroeste Sinalização Viária",
    lifespan=lifespan,
)

# CORS — em produção, substituir "*" pelo domínio real via variável de ambiente
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# AuthMiddleware deve vir APÓS o CORSMiddleware
app.add_middleware(AuthMiddleware)

app.include_router(auth_router,      prefix="/api/v1")
app.include_router(bd_router,        prefix="/api/v1")
app.include_router(ficha_router,     prefix="/api/v1")
app.include_router(orcamento_router, prefix="/api/v1")
app.include_router(relatorio_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "version": settings.APP_VERSION}


@app.get("/", tags=["health"])
def root():
    return {"app": settings.APP_NAME, "version": settings.APP_VERSION, "status": "ok"}


# Serve o frontend como arquivos estáticos — deve vir por último para não
# sobrepor as rotas da API. Só monta se o diretório existir (dev sem build).
_FRONTEND = Path(__file__).parent.parent / "frontend"
if _FRONTEND.exists():
    app.mount("/", StaticFiles(directory=str(_FRONTEND), html=True), name="frontend")
