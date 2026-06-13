"""Routers v2: orçamentistas, configuração do sistema (nome empresa / logo PNG)."""

from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.extra_models import ConfigSistema, UsuarioOrcamentista
from backend.schemas.extra_schemas import (
    ConfigSistemaRead,
    ConfigSistemaUpdate,
    OrcamentistaCreate,
    OrcamentistaRead,
    OrcamentistaUpdate,
)

router = APIRouter()

_STATIC_DIR = Path(__file__).parent.parent / "static"
_LOGO_PATH = _STATIC_DIR / "logo.png"
_MAX_LOGO_BYTES = 500 * 1024  # 500 KB


def _get_or_404(db: Session, model, pk: int):
    obj = db.get(model, pk)
    if not obj:
        raise HTTPException(status_code=404, detail="Não encontrado")
    return obj


def _get_config(db: Session) -> ConfigSistema:
    # Singleton: sempre o menor id, para ser determinístico se houver linha duplicada.
    cfg = db.query(ConfigSistema).order_by(ConfigSistema.id).first()
    if not cfg:
        cfg = ConfigSistema(nome_empresa="ALTA NOROESTE")
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return cfg


# ── Orçamentistas ────────────────────────────────────────────────────────────


@router.get(
    "/orcamentistas", response_model=list[OrcamentistaRead], tags=["orcamentistas"]
)
def listar_orcamentistas(db: Session = Depends(get_db)):
    return db.query(UsuarioOrcamentista).all()


@router.post(
    "/orcamentistas",
    response_model=OrcamentistaRead,
    status_code=status.HTTP_201_CREATED,
    tags=["orcamentistas"],
)
def criar_orcamentista(payload: OrcamentistaCreate, db: Session = Depends(get_db)):
    obj = UsuarioOrcamentista(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put(
    "/orcamentistas/{id}", response_model=OrcamentistaRead, tags=["orcamentistas"]
)
def atualizar_orcamentista(
    id: int, payload: OrcamentistaUpdate, db: Session = Depends(get_db)
):
    obj = _get_or_404(db, UsuarioOrcamentista, id)
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete(
    "/orcamentistas/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["orcamentistas"],
)
def deletar_orcamentista(id: int, db: Session = Depends(get_db)):
    db.delete(_get_or_404(db, UsuarioOrcamentista, id))
    db.commit()


# ── Config do sistema (nome empresa + logo) ──────────────────────────────────


@router.get("/config", response_model=ConfigSistemaRead, tags=["config"])
def obter_config(db: Session = Depends(get_db)):
    return _get_config(db)


@router.put("/config", response_model=ConfigSistemaRead, tags=["config"])
def atualizar_config(payload: ConfigSistemaUpdate, db: Session = Depends(get_db)):
    cfg = _get_config(db)
    # exclude_unset: grava só o que veio no JSON (inclui null para limpar);
    # campos omitidos não são tocados. Corrige o bug "não dá pra limpar campo".
    dados = payload.model_dump(exclude_unset=True)
    if "nome_empresa" in dados and dados["nome_empresa"] is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="nome_empresa não pode ser nulo.",
        )
    for campo, valor in dados.items():
        setattr(cfg, campo, valor)
    db.commit()
    db.refresh(cfg)
    return cfg


@router.post("/config/logo", response_model=ConfigSistemaRead, tags=["config"])
async def upload_logo(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """BLOCO 2.2 — upload de logo PNG (≤500KB). Salvo em backend/static/logo.png."""
    conteudo = await file.read()
    if len(conteudo) > _MAX_LOGO_BYTES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Logo excede 500 KB.",
        )
    # Valida pela assinatura real do arquivo (content_type do cliente não é confiável).
    if conteudo[:8] != b"\x89PNG\r\n\x1a\n":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Arquivo não é um PNG válido.",
        )
    _STATIC_DIR.mkdir(parents=True, exist_ok=True)
    _LOGO_PATH.write_bytes(conteudo)

    cfg = _get_config(db)
    cfg.logo_path = "/static/logo.png"
    db.commit()
    db.refresh(cfg)
    return cfg
