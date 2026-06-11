from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.bd_models import (
    BdBDI,
    BdDespesas,
    BdEPI,
    BdEstrutura,
    BdFerramental,
    BdFrotas,
    BdMateriais,
    BdRH,
)
from backend.schemas.bd_schemas import (
    BdBDICreate,
    BdBDIRead,
    BdBDIUpdate,
    BdDespesasCreate,
    BdDespesasRead,
    BdDespesasUpdate,
    BdEPICreate,
    BdEPIRead,
    BdEPIUpdate,
    BdEstruturaCreate,
    BdEstruturaRead,
    BdEstruturaUpdate,
    BdFerramentalCreate,
    BdFerramentalRead,
    BdFerramentalUpdate,
    BdFrotasCreate,
    BdFrotasRead,
    BdFrotasUpdate,
    BdMateriaisCreate,
    BdMateriaisRead,
    BdMateriaisUpdate,
    BdRHCreate,
    BdRHRead,
    BdRHUpdate,
)
from backend.services.soft_delete import (
    DependenciaError,
    soft_delete,
    verificar_bd_epi,
    verificar_bd_estrutura,
    verificar_bd_ferramental,
    verificar_bd_frotas,
    verificar_bd_materiais,
    verificar_bd_rh,
)

router = APIRouter()


# ── Helpers genéricos ────────────────────────────────────────────────────────


def _get_or_404(db: Session, model, id: int):
    obj = db.get(model, id)
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Não encontrado"
        )
    return obj


# ── bd_BDI ──────────────────────────────────────────────────────────────────


@router.get("/bd-bdi", response_model=list[BdBDIRead], tags=["bd_BDI"])
def listar_bdi(uf: str | None = None, db: Session = Depends(get_db)):
    q = db.query(BdBDI)
    if uf:
        q = q.filter(BdBDI.uf == uf.strip().upper())
    return q.all()


@router.post(
    "/bd-bdi",
    response_model=BdBDIRead,
    status_code=status.HTTP_201_CREATED,
    tags=["bd_BDI"],
)
def criar_bdi(payload: BdBDICreate, db: Session = Depends(get_db)):
    obj = BdBDI(**payload.model_dump())
    db.add(obj)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Já existe BDI para modalidade '{payload.modalidade}' e UF "
            f"'{payload.uf}'.",
        )
    db.refresh(obj)
    return obj


@router.get("/bd-bdi/{id}", response_model=BdBDIRead, tags=["bd_BDI"])
def obter_bdi(id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, BdBDI, id)


@router.put("/bd-bdi/{id}", response_model=BdBDIRead, tags=["bd_BDI"])
def atualizar_bdi(id: int, payload: BdBDIUpdate, db: Session = Depends(get_db)):
    obj = _get_or_404(db, BdBDI, id)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/bd-bdi/{id}", status_code=status.HTTP_204_NO_CONTENT, tags=["bd_BDI"])
def deletar_bdi(id: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, BdBDI, id)
    soft_delete(db, obj)
    db.commit()


# ── bd_RH ───────────────────────────────────────────────────────────────────


@router.get("/bd-rh", response_model=list[BdRHRead], tags=["bd_RH"])
def listar_rh(db: Session = Depends(get_db)):
    return db.query(BdRH).all()


@router.post(
    "/bd-rh",
    response_model=BdRHRead,
    status_code=status.HTTP_201_CREATED,
    tags=["bd_RH"],
)
def criar_rh(payload: BdRHCreate, db: Session = Depends(get_db)):
    obj = BdRH(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/bd-rh/{id}", response_model=BdRHRead, tags=["bd_RH"])
def obter_rh(id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, BdRH, id)


@router.put("/bd-rh/{id}", response_model=BdRHRead, tags=["bd_RH"])
def atualizar_rh(id: int, payload: BdRHUpdate, db: Session = Depends(get_db)):
    obj = _get_or_404(db, BdRH, id)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/bd-rh/{id}", status_code=status.HTTP_204_NO_CONTENT, tags=["bd_RH"])
def deletar_rh(id: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, BdRH, id)
    try:
        soft_delete(db, obj, verificar_bd_rh)
        db.commit()
    except DependenciaError as e:
        raise HTTPException(status_code=409, detail=str(e))


# ── bd_EPI ──────────────────────────────────────────────────────────────────


@router.get("/bd-epi", response_model=list[BdEPIRead], tags=["bd_EPI"])
def listar_epi(db: Session = Depends(get_db)):
    return db.query(BdEPI).all()


@router.post(
    "/bd-epi",
    response_model=BdEPIRead,
    status_code=status.HTTP_201_CREATED,
    tags=["bd_EPI"],
)
def criar_epi(payload: BdEPICreate, db: Session = Depends(get_db)):
    obj = BdEPI(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/bd-epi/{id}", response_model=BdEPIRead, tags=["bd_EPI"])
def obter_epi(id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, BdEPI, id)


@router.put("/bd-epi/{id}", response_model=BdEPIRead, tags=["bd_EPI"])
def atualizar_epi(id: int, payload: BdEPIUpdate, db: Session = Depends(get_db)):
    obj = _get_or_404(db, BdEPI, id)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/bd-epi/{id}", status_code=status.HTTP_204_NO_CONTENT, tags=["bd_EPI"])
def deletar_epi(id: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, BdEPI, id)
    try:
        soft_delete(db, obj, verificar_bd_epi)
        db.commit()
    except DependenciaError as e:
        raise HTTPException(status_code=409, detail=str(e))


# ── bd_FERRAMENTAL ──────────────────────────────────────────────────────────


@router.get(
    "/bd-ferramental", response_model=list[BdFerramentalRead], tags=["bd_FERRAMENTAL"]
)
def listar_ferramental(seguimento: str | None = None, db: Session = Depends(get_db)):
    q = db.query(BdFerramental)
    if seguimento:
        q = q.filter(BdFerramental.seguimento == seguimento.strip().upper())
    return q.all()


@router.post(
    "/bd-ferramental",
    response_model=BdFerramentalRead,
    status_code=status.HTTP_201_CREATED,
    tags=["bd_FERRAMENTAL"],
)
def criar_ferramental(payload: BdFerramentalCreate, db: Session = Depends(get_db)):
    obj = BdFerramental(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get(
    "/bd-ferramental/{id}", response_model=BdFerramentalRead, tags=["bd_FERRAMENTAL"]
)
def obter_ferramental(id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, BdFerramental, id)


@router.put(
    "/bd-ferramental/{id}", response_model=BdFerramentalRead, tags=["bd_FERRAMENTAL"]
)
def atualizar_ferramental(
    id: int, payload: BdFerramentalUpdate, db: Session = Depends(get_db)
):
    obj = _get_or_404(db, BdFerramental, id)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete(
    "/bd-ferramental/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["bd_FERRAMENTAL"],
)
def deletar_ferramental(id: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, BdFerramental, id)
    try:
        soft_delete(db, obj, verificar_bd_ferramental)
        db.commit()
    except DependenciaError as e:
        raise HTTPException(status_code=409, detail=str(e))


# ── bd_FROTAS ───────────────────────────────────────────────────────────────


@router.get("/bd-frotas", response_model=list[BdFrotasRead], tags=["bd_FROTAS"])
def listar_frotas(seguimento: str | None = None, db: Session = Depends(get_db)):
    q = db.query(BdFrotas)
    if seguimento:
        q = q.filter(BdFrotas.seguimento == seguimento.strip().upper())
    return q.all()


@router.post(
    "/bd-frotas",
    response_model=BdFrotasRead,
    status_code=status.HTTP_201_CREATED,
    tags=["bd_FROTAS"],
)
def criar_frotas(payload: BdFrotasCreate, db: Session = Depends(get_db)):
    obj = BdFrotas(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/bd-frotas/{id}", response_model=BdFrotasRead, tags=["bd_FROTAS"])
def obter_frotas(id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, BdFrotas, id)


@router.put("/bd-frotas/{id}", response_model=BdFrotasRead, tags=["bd_FROTAS"])
def atualizar_frotas(id: int, payload: BdFrotasUpdate, db: Session = Depends(get_db)):
    obj = _get_or_404(db, BdFrotas, id)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete(
    "/bd-frotas/{id}", status_code=status.HTTP_204_NO_CONTENT, tags=["bd_FROTAS"]
)
def deletar_frotas(id: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, BdFrotas, id)
    try:
        soft_delete(db, obj, verificar_bd_frotas)
        db.commit()
    except DependenciaError as e:
        raise HTTPException(status_code=409, detail=str(e))


# ── bd_MATERIAIS ─────────────────────────────────────────────────────────────


@router.get(
    "/bd-materiais", response_model=list[BdMateriaisRead], tags=["bd_MATERIAIS"]
)
def listar_materiais(db: Session = Depends(get_db)):
    return db.query(BdMateriais).all()


@router.post(
    "/bd-materiais",
    response_model=BdMateriaisRead,
    status_code=status.HTTP_201_CREATED,
    tags=["bd_MATERIAIS"],
)
def criar_materiais(payload: BdMateriaisCreate, db: Session = Depends(get_db)):
    obj = BdMateriais(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/bd-materiais/{id}", response_model=BdMateriaisRead, tags=["bd_MATERIAIS"])
def obter_materiais(id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, BdMateriais, id)


@router.put("/bd-materiais/{id}", response_model=BdMateriaisRead, tags=["bd_MATERIAIS"])
def atualizar_materiais(
    id: int, payload: BdMateriaisUpdate, db: Session = Depends(get_db)
):
    obj = _get_or_404(db, BdMateriais, id)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete(
    "/bd-materiais/{id}", status_code=status.HTTP_204_NO_CONTENT, tags=["bd_MATERIAIS"]
)
def deletar_materiais(id: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, BdMateriais, id)
    try:
        soft_delete(db, obj, verificar_bd_materiais)
        db.commit()
    except DependenciaError as e:
        raise HTTPException(status_code=409, detail=str(e))


# ── bd_ESTRUTURA_OPERACIONAL ─────────────────────────────────────────────────


@router.get(
    "/bd-estrutura",
    response_model=list[BdEstruturaRead],
    tags=["bd_ESTRUTURA_OPERACIONAL"],
)
def listar_estrutura(db: Session = Depends(get_db)):
    return db.query(BdEstrutura).all()


@router.post(
    "/bd-estrutura",
    response_model=BdEstruturaRead,
    status_code=status.HTTP_201_CREATED,
    tags=["bd_ESTRUTURA_OPERACIONAL"],
)
def criar_estrutura(payload: BdEstruturaCreate, db: Session = Depends(get_db)):
    obj = BdEstrutura(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get(
    "/bd-estrutura/{id}",
    response_model=BdEstruturaRead,
    tags=["bd_ESTRUTURA_OPERACIONAL"],
)
def obter_estrutura(id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, BdEstrutura, id)


@router.put(
    "/bd-estrutura/{id}",
    response_model=BdEstruturaRead,
    tags=["bd_ESTRUTURA_OPERACIONAL"],
)
def atualizar_estrutura(
    id: int, payload: BdEstruturaUpdate, db: Session = Depends(get_db)
):
    obj = _get_or_404(db, BdEstrutura, id)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete(
    "/bd-estrutura/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["bd_ESTRUTURA_OPERACIONAL"],
)
def deletar_estrutura(id: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, BdEstrutura, id)
    try:
        soft_delete(db, obj, verificar_bd_estrutura)
        db.commit()
    except DependenciaError as e:
        raise HTTPException(status_code=409, detail=str(e))


# ── bd_DESPESAS ──────────────────────────────────────────────────────────────


@router.get("/bd-despesas", response_model=list[BdDespesasRead], tags=["bd_DESPESAS"])
def listar_despesas(seguimento: str | None = None, db: Session = Depends(get_db)):
    q = db.query(BdDespesas)
    if seguimento:
        q = q.filter(BdDespesas.seguimento == seguimento.strip().upper())
    return q.all()


@router.post(
    "/bd-despesas",
    response_model=BdDespesasRead,
    status_code=status.HTTP_201_CREATED,
    tags=["bd_DESPESAS"],
)
def criar_despesas(payload: BdDespesasCreate, db: Session = Depends(get_db)):
    obj = BdDespesas(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/bd-despesas/{id}", response_model=BdDespesasRead, tags=["bd_DESPESAS"])
def obter_despesas(id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, BdDespesas, id)


@router.put("/bd-despesas/{id}", response_model=BdDespesasRead, tags=["bd_DESPESAS"])
def atualizar_despesas(
    id: int, payload: BdDespesasUpdate, db: Session = Depends(get_db)
):
    obj = _get_or_404(db, BdDespesas, id)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete(
    "/bd-despesas/{id}", status_code=status.HTTP_204_NO_CONTENT, tags=["bd_DESPESAS"]
)
def deletar_despesas(id: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, BdDespesas, id)
    soft_delete(db, obj)
    db.commit()
