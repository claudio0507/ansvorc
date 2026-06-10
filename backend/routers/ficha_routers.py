"""Routers das Fichas Técnicas — CRUD + itens/recursos com custos calculados.

Custos das fichas são SEMPRE calculados no backend (services/ficha_calc.py) a partir
de lookups nos bancos de dados — nunca enviados pelo cliente.
"""

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.ficha_models import (
    FichaEquipe,
    FichaEquipeItem,
    FichaProduto,
    FichaProdutoItem,
    FichaServico,
    FichaServicoRecurso,
)
from backend.schemas.ficha_schemas import (
    FichaEquipeCreate,
    FichaEquipeItemCreate,
    FichaEquipeItemRead,
    FichaEquipeRead,
    FichaEquipeUpdate,
    FichaProdutoCreate,
    FichaProdutoItemCreate,
    FichaProdutoItemRead,
    FichaProdutoRead,
    FichaProdutoUpdate,
    FichaServicoCreate,
    FichaServicoRead,
    FichaServicoRecursoCreate,
    FichaServicoRecursoRead,
    FichaServicoUpdate,
)
from backend.services import ficha_calc

router = APIRouter()


def _get_or_404(db: Session, model, id: int):
    obj = db.get(model, id)
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Não encontrado"
        )
    return obj


def _422(detail: str):
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


# ── Fichas de Equipe ─────────────────────────────────────────────────────────


@router.get(
    "/fichas-equipe", response_model=list[FichaEquipeRead], tags=["fichas_equipe"]
)
def listar_fichas_equipe(seguimento: str | None = None, db: Session = Depends(get_db)):
    q = db.query(FichaEquipe)
    if seguimento:
        q = q.filter(FichaEquipe.seguimento == seguimento.strip().upper())
    return q.all()


@router.post(
    "/fichas-equipe",
    response_model=FichaEquipeRead,
    status_code=status.HTTP_201_CREATED,
    tags=["fichas_equipe"],
)
def criar_ficha_equipe(payload: FichaEquipeCreate, db: Session = Depends(get_db)):
    obj = FichaEquipe(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get(
    "/fichas-equipe/{id}", response_model=FichaEquipeRead, tags=["fichas_equipe"]
)
def obter_ficha_equipe(id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, FichaEquipe, id)


@router.put(
    "/fichas-equipe/{id}", response_model=FichaEquipeRead, tags=["fichas_equipe"]
)
def atualizar_ficha_equipe(
    id: int, payload: FichaEquipeUpdate, db: Session = Depends(get_db)
):
    obj = _get_or_404(db, FichaEquipe, id)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(obj, field, value)
    # Seguimento pode mudar refeição/hospedagem — recalcula itens.
    for item in obj.itens:
        custos = ficha_calc.calcular_item_equipe(
            db, obj.seguimento, item.rh_id, item.epi_id, item.quantidade
        )
        for k, v in custos.items():
            setattr(item, k, v)
    ficha_calc.recalcular_equipe(db, obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete(
    "/fichas-equipe/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["fichas_equipe"],
)
def deletar_ficha_equipe(id: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, FichaEquipe, id)
    db.delete(obj)
    db.commit()


@router.post(
    "/fichas-equipe/{id}/itens",
    response_model=FichaEquipeItemRead,
    status_code=status.HTTP_201_CREATED,
    tags=["fichas_equipe"],
)
def adicionar_item_equipe(
    id: int, payload: FichaEquipeItemCreate, db: Session = Depends(get_db)
):
    ficha = _get_or_404(db, FichaEquipe, id)
    try:
        custos = ficha_calc.calcular_item_equipe(
            db, ficha.seguimento, payload.rh_id, payload.epi_id, payload.quantidade
        )
    except ValueError as e:
        _422(str(e))

    item = FichaEquipeItem(
        ficha_equipe_id=id,
        rh_id=payload.rh_id,
        epi_id=payload.epi_id,
        quantidade=payload.quantidade,
        **custos,
    )
    db.add(item)
    db.flush()
    db.refresh(ficha)
    ficha_calc.recalcular_equipe(db, ficha)
    db.commit()
    db.refresh(item)
    return item


@router.delete(
    "/fichas-equipe/{ficha_id}/itens/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["fichas_equipe"],
)
def remover_item_equipe(ficha_id: int, item_id: int, db: Session = Depends(get_db)):
    ficha = _get_or_404(db, FichaEquipe, ficha_id)
    item = (
        db.query(FichaEquipeItem)
        .filter(
            FichaEquipeItem.id == item_id,
            FichaEquipeItem.ficha_equipe_id == ficha_id,
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado nesta ficha")
    db.delete(item)
    db.flush()
    db.refresh(ficha)
    ficha_calc.recalcular_equipe(db, ficha)
    db.commit()


# ── Fichas de Produto ─────────────────────────────────────────────────────────


@router.get(
    "/fichas-produto", response_model=list[FichaProdutoRead], tags=["fichas_produto"]
)
def listar_fichas_produto(db: Session = Depends(get_db)):
    return db.query(FichaProduto).all()


@router.post(
    "/fichas-produto",
    response_model=FichaProdutoRead,
    status_code=status.HTTP_201_CREATED,
    tags=["fichas_produto"],
)
def criar_ficha_produto(payload: FichaProdutoCreate, db: Session = Depends(get_db)):
    obj = FichaProduto(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get(
    "/fichas-produto/{id}", response_model=FichaProdutoRead, tags=["fichas_produto"]
)
def obter_ficha_produto(id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, FichaProduto, id)


@router.put(
    "/fichas-produto/{id}", response_model=FichaProdutoRead, tags=["fichas_produto"]
)
def atualizar_ficha_produto(
    id: int, payload: FichaProdutoUpdate, db: Session = Depends(get_db)
):
    obj = _get_or_404(db, FichaProduto, id)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete(
    "/fichas-produto/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["fichas_produto"],
)
def deletar_ficha_produto(id: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, FichaProduto, id)
    db.delete(obj)
    db.commit()


@router.post(
    "/fichas-produto/{id}/itens",
    response_model=FichaProdutoItemRead,
    status_code=status.HTTP_201_CREATED,
    tags=["fichas_produto"],
)
def adicionar_item_produto(
    id: int, payload: FichaProdutoItemCreate, db: Session = Depends(get_db)
):
    ficha = _get_or_404(db, FichaProduto, id)

    if payload.componente_filho_id is not None:
        filho_id = payload.componente_filho_id
        if filho_id == id:
            _422("Uma ficha não pode referenciar a si mesma")
        if ficha_calc.detectar_ciclo_bom(db, id, filho_id):
            _422("Referência circular detectada na BOM — ciclo não permitido")
        _get_or_404(db, FichaProduto, filho_id)

    try:
        custo_unit, unidade = ficha_calc.custo_unitario_componente(
            db, payload.material_id, payload.componente_filho_id
        )
    except ValueError as e:
        _422(str(e))

    custo_total_linha = (custo_unit * payload.quantidade).quantize(Decimal("0.0001"))
    item = FichaProdutoItem(
        ficha_produto_id=id,
        material_id=payload.material_id,
        componente_filho_id=payload.componente_filho_id,
        quantidade=payload.quantidade,
        unidade=unidade,
        custo_unitario=custo_unit,
        custo_total_linha=custo_total_linha,
    )
    db.add(item)
    db.flush()
    db.refresh(ficha)
    ficha_calc.recalcular_produto(db, ficha)
    db.commit()
    db.refresh(item)
    return item


@router.delete(
    "/fichas-produto/{ficha_id}/itens/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["fichas_produto"],
)
def remover_item_produto(ficha_id: int, item_id: int, db: Session = Depends(get_db)):
    ficha = _get_or_404(db, FichaProduto, ficha_id)
    item = (
        db.query(FichaProdutoItem)
        .filter(
            FichaProdutoItem.id == item_id,
            FichaProdutoItem.ficha_produto_id == ficha_id,
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado nesta ficha")
    db.delete(item)
    db.flush()
    db.refresh(ficha)
    ficha_calc.recalcular_produto(db, ficha)
    db.commit()


# ── Fichas de Serviço ─────────────────────────────────────────────────────────


@router.get(
    "/fichas-servico", response_model=list[FichaServicoRead], tags=["fichas_servico"]
)
def listar_fichas_servico(seguimento: str | None = None, db: Session = Depends(get_db)):
    q = db.query(FichaServico)
    if seguimento:
        q = q.filter(FichaServico.seguimento == seguimento.strip().upper())
    return q.all()


@router.post(
    "/fichas-servico",
    response_model=FichaServicoRead,
    status_code=status.HTTP_201_CREATED,
    tags=["fichas_servico"],
)
def criar_ficha_servico(payload: FichaServicoCreate, db: Session = Depends(get_db)):
    obj = FichaServico(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get(
    "/fichas-servico/{id}", response_model=FichaServicoRead, tags=["fichas_servico"]
)
def obter_ficha_servico(id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, FichaServico, id)


@router.put(
    "/fichas-servico/{id}", response_model=FichaServicoRead, tags=["fichas_servico"]
)
def atualizar_ficha_servico(
    id: int, payload: FichaServicoUpdate, db: Session = Depends(get_db)
):
    obj = _get_or_404(db, FichaServico, id)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(obj, field, value)
    ficha_calc.recalcular_servico(db, obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete(
    "/fichas-servico/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["fichas_servico"],
)
def deletar_ficha_servico(id: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, FichaServico, id)
    db.delete(obj)
    db.commit()


@router.post(
    "/fichas-servico/{id}/recursos",
    response_model=FichaServicoRecursoRead,
    status_code=status.HTTP_201_CREATED,
    tags=["fichas_servico"],
)
def adicionar_recurso_servico(
    id: int, payload: FichaServicoRecursoCreate, db: Session = Depends(get_db)
):
    ficha = _get_or_404(db, FichaServico, id)
    # Valida existência dos vínculos (calcular_custo_servico lança ValueError)
    try:
        ficha_calc.calcular_custo_servico(
            db,
            ficha.produtividade_dia,
            payload.ficha_equipe_id,
            payload.frota_id,
            payload.ferramental_id,
            payload.ficha_produto_id,
        )
    except ValueError as e:
        _422(str(e))

    recurso = FichaServicoRecurso(ficha_servico_id=id, **payload.model_dump())
    db.add(recurso)
    db.flush()
    db.refresh(ficha)
    ficha_calc.recalcular_servico(db, ficha)
    db.commit()
    db.refresh(recurso)
    return recurso


@router.delete(
    "/fichas-servico/{ficha_id}/recursos/{recurso_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["fichas_servico"],
)
def remover_recurso_servico(
    ficha_id: int, recurso_id: int, db: Session = Depends(get_db)
):
    ficha = _get_or_404(db, FichaServico, ficha_id)
    recurso = (
        db.query(FichaServicoRecurso)
        .filter(
            FichaServicoRecurso.id == recurso_id,
            FichaServicoRecurso.ficha_servico_id == ficha_id,
        )
        .first()
    )
    if not recurso:
        raise HTTPException(
            status_code=404, detail="Recurso não encontrado nesta ficha"
        )
    db.delete(recurso)
    db.flush()
    db.refresh(ficha)
    ficha_calc.recalcular_servico(db, ficha)
    db.commit()
