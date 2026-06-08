from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.database import Base, engine
from backend.routers.bd_routers import router as bd_router

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

app.include_router(bd_router, prefix="/api/v1")


@app.get("/", tags=["health"])
def root():
    return {"app": settings.APP_NAME, "version": settings.APP_VERSION, "status": "ok"}
