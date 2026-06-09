from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.middleware import AuthMiddleware
from backend.routers.auth_routers import router as auth_router
from backend.routers.bd_routers import router as bd_router
from backend.routers.ficha_routers import router as ficha_router
from backend.routers.orcamento_routers import router as orcamento_router
from backend.routers.relatorio_routers import router as relatorio_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="ERP de orçamentação para engenharia viária — Alta Noroeste Sinalização Viária",
)

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


@app.get("/", tags=["health"])
def root():
    return {"app": settings.APP_NAME, "version": settings.APP_VERSION, "status": "ok"}
