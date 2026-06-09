from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.bd_models import BdEPI, BdFerramental, BdFrotas, BdMateriais, BdRH
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

router = APIRouter()


def _get_or_404(db: Session, model, id: int):
    obj = db.get(model, id)
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Não encontrado"
        )
    return obj


# ── Lookup helpers ────────────────────────────────────────────────────────────


def _custo_diario_rh(rh: BdRH) -> Decimal:
    """custo_diario = salario_base * (1 + encargos) / (horas_mes / 8)."""
    custo_hora = rh.salario_base * (1 + rh.encargos_percentual) / rh.horas_mes
    return (custo_hora * Decimal("8")).quantize(Decimal("0.0001"))


def _custo_diario_epi(epi: BdEPI) -> Decimal:
    """custo_diario = custo_unitario / vida_util_dias (ou custo_unitario se sem vida útil)."""
    if epi.vida_util_dias:
        return (epi.custo_unitario / Decimal(str(epi.vida_util_dias))).quantize(
            Decimal("0.0001")
        )
    return epi.custo_unitario


def _custo_diario_ferramental(ferr: BdFerramental) -> Decimal:
    if ferr.vida_util_dias:
        return (ferr.custo_unitario / Decimal(str(ferr.vida_util_dias))).quantize(
            Decimal("0.0001")
        )
    return ferr.custo_unitario


def _detecta_ciclo_bom(db: Session, ficha_pai_id: int, candidato_filho_id: int) -> bool:
    """Retorna True se adicionar candidato_filho dentro de ficha_pai criaria ciclo.

    Percorre a árvore de componentes filhos do candidato: se em algum nível
    encontrar ficha_pai_id, há ciclo.
    """
    visitados: set[int] = set()
    fila = [candidato_filho_id]
    while fila:
        atual = fila.pop()
        if atual == ficha_pai_id:
            return True
        if atual in visitados:
            continue
        visitados.add(atual)
        filhos = (
            db.query(FichaProdutoItem.componente_filho_id)
            .filter(
                FichaProdutoItem.ficha_produto_id == atual,
                FichaProdutoItem.componente_filho_id.is_not(None),
            )
            .all()
        )
        fila.extend(f[0] for f in filhos)
    return False


# ── Fichas de Equipe ─────────────────────────────────────────────────────────


@router.get(
    "/fichas-equipe", response_model=list[FichaEquipeRead], tags=["fichas_equipe"]
)
def listar_fichas_equipe(db: Session = Depends(get_db)):
    return db.query(FichaEquipe).all()


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

    # Lookup automático do custo
    if payload.tipo_recurso == "RH":
        rh = _get_or_404(db, BdRH, payload.rh_id)
        custo = _custo_diario_rh(rh)
    elif payload.tipo_recurso == "EPI":
        epi = _get_or_404(db, BdEPI, payload.epi_id)
        custo = _custo_diario_epi(epi)
    elif payload.tipo_recurso == "FERRAMENTAL":
        ferr = _get_or_404(db, BdFerramental, payload.ferramental_id)
        custo = _custo_diario_ferramental(ferr)
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"tipo_recurso inválido: '{payload.tipo_recurso}'. Use RH, EPI ou FERRAMENTAL.",
        )

    item = FichaEquipeItem(
        ficha_equipe_id=id,
        custo_unitario_gravado=custo,
        **payload.model_dump(),
    )
    db.add(item)

    # Seta flag possui_itens
    ficha.possui_itens = True
    db.commit()
    db.refresh(item)
    return item


@router.delete(
    "/fichas-equipe/{ficha_id}/itens/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["fichas_equipe"],
)
def remover_item_equipe(ficha_id: int, item_id: int, db: Session = Depends(get_db)):
    _get_or_404(db, FichaEquipe, ficha_id)
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

    # Atualiza flag após flush (item já removido da sessão)
    restantes = (
        db.query(FichaEquipeItem)
        .filter(FichaEquipeItem.ficha_equipe_id == ficha_id)
        .count()
    )
    ficha = db.get(FichaEquipe, ficha_id)
    ficha.possui_itens = restantes > 0

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

    if payload.material_id is not None:
        mat = _get_or_404(db, BdMateriais, payload.material_id)
        custo = mat.custo_unitario

    else:
        filho_id = payload.componente_filho_id

        # Proteção anti-self-reference
        if filho_id == id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Uma ficha não pode referenciar a si mesma",
            )

        # Proteção anti-ciclo BOM
        if _detecta_ciclo_bom(db, ficha_pai_id=id, candidato_filho_id=filho_id):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Referência circular detectada na BOM — ciclo não permitido",
            )

        _get_or_404(db, FichaProduto, filho_id)
        custo_filho = (
            db.query(FichaProdutoItem)
            .filter(FichaProdutoItem.ficha_produto_id == filho_id)
            .all()
        )
        custo = sum(
            (i.custo_unitario_gravado * i.quantidade for i in custo_filho),
            Decimal("0"),
        )

    item = FichaProdutoItem(
        ficha_produto_id=id,
        custo_unitario_gravado=custo,
        **payload.model_dump(),
    )
    db.add(item)
    ficha.possui_itens = True
    db.commit()
    db.refresh(item)
    return item


@router.delete(
    "/fichas-produto/{ficha_id}/itens/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["fichas_produto"],
)
def remover_item_produto(ficha_id: int, item_id: int, db: Session = Depends(get_db)):
    _get_or_404(db, FichaProduto, ficha_id)
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

    restantes = (
        db.query(FichaProdutoItem)
        .filter(FichaProdutoItem.ficha_produto_id == ficha_id)
        .count()
    )
    ficha = db.get(FichaProduto, ficha_id)
    ficha.possui_itens = restantes > 0
    db.commit()


# ── Fichas de Serviço ─────────────────────────────────────────────────────────


@router.get(
    "/fichas-servico", response_model=list[FichaServicoRead], tags=["fichas_servico"]
)
def listar_fichas_servico(db: Session = Depends(get_db)):
    return db.query(FichaServico).all()


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

    # Lookup automático do custo conforme tipo de recurso
    if payload.ficha_equipe_id is not None:
        equipe = _get_or_404(db, FichaEquipe, payload.ficha_equipe_id)
        # Custo da equipe = soma dos itens gravados
        itens = equipe.itens
        custo = sum(
            (i.custo_unitario_gravado * i.quantidade for i in itens),
            Decimal("0"),
        )

    elif payload.frota_id is not None:
        frota = _get_or_404(db, BdFrotas, payload.frota_id)
        custo = frota.custo_diaria

    elif payload.ferramental_id is not None:
        ferr = _get_or_404(db, BdFerramental, payload.ferramental_id)
        custo = _custo_diario_ferramental(ferr)

    else:  # ficha_produto_id
        produto = _get_or_404(db, FichaProduto, payload.ficha_produto_id)
        itens_prod = produto.itens
        custo = sum(
            (i.custo_unitario_gravado * i.quantidade for i in itens_prod),
            Decimal("0"),
        )

    recurso = FichaServicoRecurso(
        ficha_servico_id=id,
        custo_unitario_gravado=custo,
        **payload.model_dump(),
    )
    db.add(recurso)
    ficha.possui_recursos = True
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
    _get_or_404(db, FichaServico, ficha_id)
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

    restantes = (
        db.query(FichaServicoRecurso)
        .filter(FichaServicoRecurso.ficha_servico_id == ficha_id)
        .count()
    )
    ficha = db.get(FichaServico, ficha_id)
    ficha.possui_recursos = restantes > 0
    db.commit()
