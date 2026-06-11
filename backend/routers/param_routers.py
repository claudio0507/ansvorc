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
    ParametroCreate,
    ParametroRead,
    ParametroUpdate,
    SeguimentoCreate,
    TipoEstruturaCreate,
    UnidadeMedidaCreate,
    UnidadeMedidaRead,
    UnidadeMedidaUpdate,
)
from backend.services.soft_delete import (
    DependenciaError,
    soft_delete,
    verificar_seguimento,
    verificar_tipo_estrutura,
    verificar_unidade_medida,
)

router = APIRouter()


def _get_or_404(db: Session, model, id: int):
    obj = db.get(model, id)
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Não encontrado"
        )
    return obj


# ── Unidades de Medida ────────────────────────────────────────────────────────


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
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Unidade '{payload.sigla}' já existe.",
        )
    db.refresh(obj)
    return obj


@router.put(
    "/unidades-medida/{id}",
    response_model=UnidadeMedidaRead,
    tags=["parametros"],
)
def atualizar_unidade(
    id: int, payload: UnidadeMedidaUpdate, db: Session = Depends(get_db)
):
    obj = _get_or_404(db, UnidadeMedida, id)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete(
    "/unidades-medida/{id}", status_code=status.HTTP_204_NO_CONTENT, tags=["parametros"]
)
def deletar_unidade(id: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, UnidadeMedida, id)
    try:
        soft_delete(db, obj, verificar_unidade_medida)
        db.commit()
    except DependenciaError as e:
        raise HTTPException(status_code=409, detail=str(e))


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
def criar_seguimento(
    payload: SeguimentoCreate, db: Session = Depends(get_db)
):
    obj = ParametroSeguimento(**payload.model_dump())
    db.add(obj)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Seguimento '{payload.nome}' já existe.",
        )
    db.refresh(obj)
    return obj


@router.put(
    "/parametros/seguimentos/{id}",
    response_model=ParametroRead,
    tags=["parametros"],
)
def atualizar_seguimento(
    id: int, payload: ParametroUpdate, db: Session = Depends(get_db)
):
    obj = _get_or_404(db, ParametroSeguimento, id)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete(
    "/parametros/seguimentos/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["parametros"],
)
def deletar_seguimento(id: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, ParametroSeguimento, id)
    try:
        soft_delete(db, obj, verificar_seguimento)
        db.commit()
    except DependenciaError as e:
        raise HTTPException(status_code=409, detail=str(e))


# ── Tipos de Estrutura Operacional ────────────────────────────────────────────


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
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tipo '{payload.nome}' já existe.",
        )
    db.refresh(obj)
    return obj


@router.put(
    "/parametros/tipos-estrutura/{id}",
    response_model=ParametroRead,
    tags=["parametros"],
)
def atualizar_tipo(
    id: int, payload: ParametroUpdate, db: Session = Depends(get_db)
):
    obj = _get_or_404(db, ParametroTipoEstrutura, id)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete(
    "/parametros/tipos-estrutura/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["parametros"],
)
def deletar_tipo(id: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, ParametroTipoEstrutura, id)
    try:
        soft_delete(db, obj, verificar_tipo_estrutura)
        db.commit()
    except DependenciaError as e:
        raise HTTPException(status_code=409, detail=str(e))
