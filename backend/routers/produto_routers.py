"""Routers de Produtos, Componentes e atribuição de fichas técnicas (BLOCO 4)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.produto_models import Componente, ItemFicha, Produto
from backend.schemas.produto_schemas import (
    ItemFichaCreate,
    ItemFichaRead,
    ItemIndustrialCreate,
    ItemIndustrialRead,
    ItemIndustrialUpdate,
)
from backend.services.codigo import gerar_codigo

router = APIRouter()


def _get_or_404(db: Session, model, pk: int):
    obj = db.get(model, pk)
    if not obj:
        raise HTTPException(status_code=404, detail="Não encontrado")
    return obj


def _crud(prefixo: str, modelo, tag: str, rota: str):
    """Registra CRUD para Componente/Produto reaproveitando a mesma lógica."""

    @router.get(f"/{rota}", response_model=list[ItemIndustrialRead], tags=[tag])
    def listar(db: Session = Depends(get_db)):
        return db.query(modelo).all()

    @router.post(
        f"/{rota}",
        response_model=ItemIndustrialRead,
        status_code=status.HTTP_201_CREATED,
        tags=[tag],
    )
    def criar(payload: ItemIndustrialCreate, db: Session = Depends(get_db)):
        dados = payload.model_dump()
        if not dados.get("codigo"):
            dados["codigo"] = gerar_codigo(db, modelo, prefixo)
        obj = modelo(**dados)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @router.get(f"/{rota}/{{id}}", response_model=ItemIndustrialRead, tags=[tag])
    def obter(id: int, db: Session = Depends(get_db)):
        return _get_or_404(db, modelo, id)

    @router.put(f"/{rota}/{{id}}", response_model=ItemIndustrialRead, tags=[tag])
    def atualizar(
        id: int, payload: ItemIndustrialUpdate, db: Session = Depends(get_db)
    ):
        obj = _get_or_404(db, modelo, id)
        for k, v in payload.model_dump(exclude_none=True).items():
            setattr(obj, k, v)
        db.commit()
        db.refresh(obj)
        return obj

    @router.delete(
        f"/{rota}/{{id}}", status_code=status.HTTP_204_NO_CONTENT, tags=[tag]
    )
    def deletar(id: int, db: Session = Depends(get_db)):
        db.delete(_get_or_404(db, modelo, id))
        db.commit()


_crud("CMP", Componente, "componentes", "componentes")
_crud("PRD", Produto, "produtos", "produtos")


# ── Atribuição de fichas técnicas ────────────────────────────────────────────


@router.get("/item-fichas", response_model=list[ItemFichaRead], tags=["item_fichas"])
def listar_item_fichas(
    componente_id: int | None = None,
    produto_id: int | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(ItemFicha)
    if componente_id is not None:
        q = q.filter(ItemFicha.componente_id == componente_id)
    if produto_id is not None:
        q = q.filter(ItemFicha.produto_id == produto_id)
    return q.all()


@router.post(
    "/item-fichas",
    response_model=ItemFichaRead,
    status_code=status.HTTP_201_CREATED,
    tags=["item_fichas"],
)
def atribuir_ficha(payload: ItemFichaCreate, db: Session = Depends(get_db)):
    obj = ItemFicha(**payload.model_dump())
    db.add(obj)
    db.flush()
    # Marca o item como possuindo ficha técnica
    if payload.componente_id:
        comp = db.get(Componente, payload.componente_id)
        if comp:
            comp.possui_ficha_tecnica = True
    if payload.produto_id:
        prod = db.get(Produto, payload.produto_id)
        if prod:
            prod.possui_ficha_tecnica = True
    db.commit()
    db.refresh(obj)
    return obj


@router.delete(
    "/item-fichas/{id}", status_code=status.HTTP_204_NO_CONTENT, tags=["item_fichas"]
)
def remover_atribuicao(id: int, db: Session = Depends(get_db)):
    db.delete(_get_or_404(db, ItemFicha, id))
    db.commit()
