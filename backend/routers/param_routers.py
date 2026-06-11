"""Routers de parametrização — unidades de medida, seguimentos, tipos de estrutura."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.param_models import (
    ParametroSeguimento,
    ParametroTipoEstrutura,
    UnidadeMedida,
)
from backend.schemas.param_schemas import (
    ParametroRead,
    ParametroUpdate,
    SeguimentoCreate,
    TipoEstruturaCreate,
    UnidadeMedidaCreate,
    UnidadeMedidaRead,
    UnidadeMedidaUpdate,
)

router = APIRouter()


def _get_or_404(db: Session, model, pk: int):
    obj = db.get(model, pk)
    if not obj:
        raise HTTPException(status_code=404, detail="Não encontrado")
    return obj


def _commit_unique(db: Session, campo: str):
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Já existe registro com este {campo}.",
        )


# ── Unidades de medida ───────────────────────────────────────────────────────


@router.get(
    "/unidades-medida", response_model=list[UnidadeMedidaRead], tags=["parametros"]
)
def listar_unidades(db: Session = Depends(get_db)):
    return db.query(UnidadeMedida).all()


@router.post(
    "/unidades-medida",
    response_model=UnidadeMedidaRead,
    status_code=status.HTTP_201_CREATED,
    tags=["parametros"],
)
def criar_unidade(payload: UnidadeMedidaCreate, db: Session = Depends(get_db)):
    obj = UnidadeMedida(**payload.model_dump())
    db.add(obj)
    _commit_unique(db, "sigla")
    db.refresh(obj)
    return obj


@router.put(
    "/unidades-medida/{id}", response_model=UnidadeMedidaRead, tags=["parametros"]
)
def atualizar_unidade(
    id: int, payload: UnidadeMedidaUpdate, db: Session = Depends(get_db)
):
    obj = _get_or_404(db, UnidadeMedida, id)
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(obj, k, v)
    _commit_unique(db, "sigla")
    db.refresh(obj)
    return obj


@router.delete(
    "/unidades-medida/{id}", status_code=status.HTTP_204_NO_CONTENT, tags=["parametros"]
)
def deletar_unidade(id: int, db: Session = Depends(get_db)):
    db.delete(_get_or_404(db, UnidadeMedida, id))
    db.commit()


# ── Seguimentos ──────────────────────────────────────────────────────────────


@router.get(
    "/parametros/seguimentos", response_model=list[ParametroRead], tags=["parametros"]
)
def listar_seguimentos(db: Session = Depends(get_db)):
    return db.query(ParametroSeguimento).all()


@router.post(
    "/parametros/seguimentos",
    response_model=ParametroRead,
    status_code=status.HTTP_201_CREATED,
    tags=["parametros"],
)
def criar_seguimento(payload: SeguimentoCreate, db: Session = Depends(get_db)):
    obj = ParametroSeguimento(**payload.model_dump())
    db.add(obj)
    _commit_unique(db, "nome")
    db.refresh(obj)
    return obj


@router.put(
    "/parametros/seguimentos/{id}", response_model=ParametroRead, tags=["parametros"]
)
def atualizar_seguimento(
    id: int, payload: ParametroUpdate, db: Session = Depends(get_db)
):
    obj = _get_or_404(db, ParametroSeguimento, id)
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(obj, k, v)
    _commit_unique(db, "nome")
    db.refresh(obj)
    return obj


@router.delete(
    "/parametros/seguimentos/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["parametros"],
)
def deletar_seguimento(id: int, db: Session = Depends(get_db)):
    db.delete(_get_or_404(db, ParametroSeguimento, id))
    db.commit()


# ── Tipos de estrutura ───────────────────────────────────────────────────────


@router.get(
    "/parametros/tipos-estrutura",
    response_model=list[ParametroRead],
    tags=["parametros"],
)
def listar_tipos(db: Session = Depends(get_db)):
    return db.query(ParametroTipoEstrutura).all()


@router.post(
    "/parametros/tipos-estrutura",
    response_model=ParametroRead,
    status_code=status.HTTP_201_CREATED,
    tags=["parametros"],
)
def criar_tipo(payload: TipoEstruturaCreate, db: Session = Depends(get_db)):
    obj = ParametroTipoEstrutura(**payload.model_dump())
    db.add(obj)
    _commit_unique(db, "nome")
    db.refresh(obj)
    return obj


@router.put(
    "/parametros/tipos-estrutura/{id}",
    response_model=ParametroRead,
    tags=["parametros"],
)
def atualizar_tipo(id: int, payload: ParametroUpdate, db: Session = Depends(get_db)):
    obj = _get_or_404(db, ParametroTipoEstrutura, id)
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(obj, k, v)
    _commit_unique(db, "nome")
    db.refresh(obj)
    return obj


@router.delete(
    "/parametros/tipos-estrutura/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["parametros"],
)
def deletar_tipo(id: int, db: Session = Depends(get_db)):
    db.delete(_get_or_404(db, ParametroTipoEstrutura, id))
    db.commit()
