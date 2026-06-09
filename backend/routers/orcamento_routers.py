from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.bd_models import BdBDI
from backend.models.ficha_models import FichaProduto, FichaServico
from backend.models.orcamento_models import Cliente, Orcamento, OrcamentoItem
from backend.schemas.orcamento_schemas import (
    ClienteCreate,
    ClienteRead,
    ClienteUpdate,
    ItemCalculadoRead,
    OrcamentoCreate,
    OrcamentoItemCreate,
    OrcamentoItemRead,
    OrcamentoItemUpdate,
    OrcamentoRead,
    OrcamentoUpdate,
    ResultadoCalculoRead,
)
from backend.services.motor_bdi import (
    ADM_PADRAO,
    CF_PADRAO,
    COFINS_PADRAO,
    ICMS_PADRAO,
    ISSQN_PR,
    ISSQN_SP,
    PIS_COFINS_REGIME_CUMULATIVO,
    PIS_COFINS_REGIME_NORMAL,
    PIS_PADRAO,
    aplicar_mod_fat,
    aplicar_reidi,
    calcular_bdi_completo,
    calcular_bdi_sombra,
    calcular_fator_k,
    margem_liquida_real,
)

router = APIRouter()

# ── helpers ───────────────────────────────────────────────────────────────────


def _get_or_404(db: Session, model, id: int):
    obj = db.get(model, id)
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Não encontrado"
        )
    return obj


def _guard_rascunho(orc: Orcamento) -> None:
    """Levanta 403 se o orçamento não estiver em status rascunho."""
    if orc.status != "rascunho":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Orçamento com status '{orc.status}' não pode ser editado. "
            "Apenas orçamentos em 'rascunho' permitem alterações.",
        )


def _bdi_params_do_bd(db: Session, mod_fat: str) -> BdBDI | None:
    """Busca os parâmetros de BDI cadastrados para a modalidade, se existir."""
    return (
        db.query(BdBDI).filter(BdBDI.modalidade == mod_fat, BdBDI.ativo == True).first()
    )


def _impostos_base(db: Session, mod_fat: str, uf: str) -> dict:
    """
    Monta o dicionário de impostos base para um item, consultando bd_BDI.
    Usa constantes de referência como fallback se nenhum registro estiver cadastrado.
    """
    bdi_row = _bdi_params_do_bd(db, mod_fat)

    if bdi_row:
        adm = bdi_row.adm_percentual
        cf = bdi_row.custo_financeiro_percentual
        issqn = (
            bdi_row.issqn_pr_percentual if uf == "PR" else bdi_row.issqn_sp_percentual
        )
        # Para BDI+ICMS usa pis_cofins_percentual do registro; fallback ao regime cumulativo
        pis_cofins = bdi_row.pis_cofins_percentual
        icms = bdi_row.icms_percentual
    else:
        # Fallback: constantes padrão
        adm = ADM_PADRAO
        cf = CF_PADRAO
        issqn = ISSQN_PR if uf == "PR" else ISSQN_SP
        pis_cofins = (
            PIS_COFINS_REGIME_CUMULATIVO
            if mod_fat in ("BDI+ICMS", "FAT DIR SIMP")
            else PIS_COFINS_REGIME_NORMAL
        )
        icms = ICMS_PADRAO if mod_fat == "BDI+ICMS" else Decimal("0")

    return {
        "adm": adm,
        "cf": cf,
        "pis": pis_cofins,  # pis+cofins acumulado no campo "pis"
        "cofins": Decimal("0"),
        "issqn": issqn,
        "icms": icms,
    }


# ── Clientes ──────────────────────────────────────────────────────────────────


@router.get("/clientes", response_model=list[ClienteRead], tags=["clientes"])
def listar_clientes(db: Session = Depends(get_db)):
    return db.query(Cliente).all()


@router.post(
    "/clientes",
    response_model=ClienteRead,
    status_code=status.HTTP_201_CREATED,
    tags=["clientes"],
)
def criar_cliente(body: ClienteCreate, db: Session = Depends(get_db)):
    obj = Cliente(**body.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/clientes/{id}", response_model=ClienteRead, tags=["clientes"])
def obter_cliente(id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, Cliente, id)


@router.put("/clientes/{id}", response_model=ClienteRead, tags=["clientes"])
def atualizar_cliente(id: int, body: ClienteUpdate, db: Session = Depends(get_db)):
    obj = _get_or_404(db, Cliente, id)
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete(
    "/clientes/{id}", status_code=status.HTTP_204_NO_CONTENT, tags=["clientes"]
)
def excluir_cliente(id: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, Cliente, id)
    db.delete(obj)
    db.commit()


# ── Orçamentos ────────────────────────────────────────────────────────────────


@router.get("/orcamentos", response_model=list[OrcamentoRead], tags=["orcamentos"])
def listar_orcamentos(db: Session = Depends(get_db)):
    return db.query(Orcamento).all()


@router.post(
    "/orcamentos",
    response_model=OrcamentoRead,
    status_code=status.HTTP_201_CREATED,
    tags=["orcamentos"],
)
def criar_orcamento(body: OrcamentoCreate, db: Session = Depends(get_db)):
    _get_or_404(db, Cliente, body.cliente_id)  # valida existência do cliente
    obj = Orcamento(**body.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/orcamentos/{id}", response_model=OrcamentoRead, tags=["orcamentos"])
def obter_orcamento(id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, Orcamento, id)


@router.put("/orcamentos/{id}", response_model=OrcamentoRead, tags=["orcamentos"])
def atualizar_orcamento(id: int, body: OrcamentoUpdate, db: Session = Depends(get_db)):
    obj = _get_or_404(db, Orcamento, id)
    _guard_rascunho(obj)
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete(
    "/orcamentos/{id}", status_code=status.HTTP_204_NO_CONTENT, tags=["orcamentos"]
)
def excluir_orcamento(id: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, Orcamento, id)
    _guard_rascunho(obj)
    db.delete(obj)
    db.commit()


# ── Itens do Orçamento ────────────────────────────────────────────────────────


@router.get(
    "/orcamentos/{id}/itens",
    response_model=list[OrcamentoItemRead],
    tags=["orcamentos"],
)
def listar_itens(id: int, db: Session = Depends(get_db)):
    _get_or_404(db, Orcamento, id)
    return db.query(OrcamentoItem).filter(OrcamentoItem.orcamento_id == id).all()


@router.post(
    "/orcamentos/{id}/itens",
    response_model=OrcamentoItemRead,
    status_code=status.HTTP_201_CREATED,
    tags=["orcamentos"],
)
def adicionar_item(id: int, body: OrcamentoItemCreate, db: Session = Depends(get_db)):
    orc = _get_or_404(db, Orcamento, id)
    _guard_rascunho(orc)

    # Valida FKs de fichas
    if body.ficha_servico_id:
        _get_or_404(db, FichaServico, body.ficha_servico_id)
    if body.ficha_produto_id:
        _get_or_404(db, FichaProduto, body.ficha_produto_id)

    dados = body.model_dump()
    dados["orcamento_id"] = id
    if body.item_excepcional:
        dados["demanda_aprovacao"] = True

    obj = OrcamentoItem(**dados)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put(
    "/orcamentos/{id}/itens/{item_id}",
    response_model=OrcamentoItemRead,
    tags=["orcamentos"],
)
def atualizar_item(
    id: int, item_id: int, body: OrcamentoItemUpdate, db: Session = Depends(get_db)
):
    orc = _get_or_404(db, Orcamento, id)
    _guard_rascunho(orc)

    item = (
        db.query(OrcamentoItem)
        .filter(OrcamentoItem.id == item_id, OrcamentoItem.orcamento_id == id)
        .first()
    )
    if not item:
        raise HTTPException(
            status_code=404, detail="Item não encontrado neste orçamento"
        )

    for k, v in body.model_dump(exclude_none=True).items():
        setattr(item, k, v)
    db.commit()
    db.refresh(item)
    return item


@router.delete(
    "/orcamentos/{id}/itens/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["orcamentos"],
)
def remover_item(id: int, item_id: int, db: Session = Depends(get_db)):
    orc = _get_or_404(db, Orcamento, id)
    _guard_rascunho(orc)

    item = (
        db.query(OrcamentoItem)
        .filter(OrcamentoItem.id == item_id, OrcamentoItem.orcamento_id == id)
        .first()
    )
    if not item:
        raise HTTPException(
            status_code=404, detail="Item não encontrado neste orçamento"
        )

    db.delete(item)
    db.commit()


# ── Endpoint de Cálculo ───────────────────────────────────────────────────────


@router.post(
    "/orcamentos/{id}/calcular",
    response_model=ResultadoCalculoRead,
    tags=["orcamentos"],
)
def calcular_orcamento(id: int, db: Session = Depends(get_db)):
    """
    Pipeline de cálculo completo:

    1. Carrega orçamento + todos os itens
    2. Para cada item:
       a. Monta impostos base do bd_BDI (ou fallback em constantes)
       b. Aplica REIDI se beneficio_reidi = True
       c. Aplica máscara MOD FAT
       d. Calcula BDI Sombra (bloco operacional/excepcionais)
          ou BDI Completo (bloco servicos/produtos)
       e. Calcula lucro absoluto da linha (apenas faturáveis)
    3. Executa Fator K top-down
    4. Calcula Margem Líquida Real
    5. Persiste os valores calculados em cada OrcamentoItem
    6. Atualiza totais no cabeçalho do Orçamento
    7. Retorna ResultadoCalculoRead
    """
    orc = _get_or_404(db, Orcamento, id)
    itens = db.query(OrcamentoItem).filter(OrcamentoItem.orcamento_id == id).all()

    if not itens:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="O orçamento não possui itens para calcular.",
        )

    uf = orc.uf_execucao
    reidi = orc.beneficio_reidi

    # Separar blocos
    FATURAVEIS = {"servicos", "produtos"}
    NAO_FATURAVEIS = {"operacional", "excepcionais"}

    itens_fat = [i for i in itens if i.bloco in FATURAVEIS]
    itens_nfat = [i for i in itens if i.bloco in NAO_FATURAVEIS]

    # ── Passo 1: Calcular BDI e preços base dos itens faturáveis ──────────────
    fat_intermediarios: list[dict] = []
    total_custo_direto = Decimal("0")

    for item in itens_fat:
        mod_fat = item.mod_fat if item.mod_fat != "-" else "BDI-MAT+MO"
        params = _impostos_base(db, mod_fat, uf)

        imp = {
            "pis": params["pis"],
            "cofins": params["cofins"],
            "issqn": params["issqn"],
            "icms": params["icms"],
        }

        if reidi:
            imp = aplicar_reidi(imp)

        imp = aplicar_mod_fat(mod_fat, imp)

        try:
            bdi_taxa = calcular_bdi_completo(
                despesas_adm=params["adm"],
                custo_financeiro=params["cf"],
                margem=item.margem_percentual,
                pis=imp["pis"],
                cofins=imp["cofins"],
                issqn=imp["issqn"],
                icms=imp["icms"],
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Item {item.id} ({item.descricao}): {exc}",
            )

        cdu = item.custo_direto_unitario
        preco_unit_base = cdu * (Decimal("1") + bdi_taxa)
        preco_total_base = preco_unit_base * item.quantidade

        lucro_abs = (
            cdu
            * item.quantidade
            * (Decimal("1") + params["adm"])
            * (Decimal("1") + params["cf"])
            * item.margem_percentual
        )

        total_custo_direto += cdu * item.quantidade

        fat_intermediarios.append(
            {
                "item": item,
                "bdi_taxa": bdi_taxa,
                "preco_unit_base": preco_unit_base,
                "preco_total_base": preco_total_base,
                "lucro_abs": lucro_abs,
                "adm": params["adm"],
                "cf": params["cf"],
            }
        )

    # ── Passo 2: BDI Sombra dos itens não faturáveis ─────────────────────────
    total_nao_faturavel = Decimal("0")
    nfat_resultados: list[dict] = []

    for item in itens_nfat:
        # Para BDI Sombra usamos ADM + PIS + COFINS + ISSQN do bd_BDI genérico
        # Usa modalidade "BDI-MAT+MO" como referência de alíquotas ADM/CF
        params_sombra = _impostos_base(db, "BDI-MAT+MO", uf)

        pis_s = params_sombra["pis"]
        cof_s = params_sombra["cofins"]
        iss_s = params_sombra["issqn"]

        if reidi:
            pis_s = Decimal("0")
            cof_s = Decimal("0")

        custo_carregado = calcular_bdi_sombra(
            custo_direto=item.custo_direto_unitario * item.quantidade,
            despesas_adm=params_sombra["adm"],
            pis=pis_s,
            cofins=cof_s,
            issqn=iss_s,
        )

        total_custo_direto += item.custo_direto_unitario * item.quantidade
        total_nao_faturavel += custo_carregado
        nfat_resultados.append({"item": item, "custo_carregado": custo_carregado})

    # ── Passo 3: Fator K ──────────────────────────────────────────────────────
    from backend.services.motor_bdi import ItemFaturavel

    itens_fk = [
        ItemFaturavel(
            id=r["item"].id,
            custo_direto=r["item"].custo_direto_unitario * r["item"].quantidade,
            preco_base_total=r["preco_total_base"],
        )
        for r in fat_intermediarios
    ]

    resultados_fk = calcular_fator_k(itens_fk, total_nao_faturavel)
    fk_por_id = {r["id"]: r for r in resultados_fk}

    # ── Passo 4: Margem Líquida Real ──────────────────────────────────────────
    itens_mlr = [
        {
            "custo_direto": r["item"].custo_direto_unitario,
            "quantidade": r["item"].quantidade,
            "margem": r["item"].margem_percentual,
            "despesas_adm": r["adm"],
            "custo_financeiro": r["cf"],
        }
        for r in fat_intermediarios
    ]

    subtotal_faturavel = sum(
        (r["preco_total_base"] for r in fat_intermediarios), Decimal("0")
    )
    total_proposta = subtotal_faturavel + total_nao_faturavel
    mlr = margem_liquida_real(itens_mlr, total_proposta)

    # ── Passo 5: Persistir resultados nos itens ───────────────────────────────
    for r in fat_intermediarios:
        item = r["item"]
        fk = fk_por_id.get(item.id, {})
        item.bdi_taxa = r["bdi_taxa"]
        item.preco_venda_unitario = r["preco_unit_base"].quantize(Decimal("0.0001"))
        item.preco_venda_total = r["preco_total_base"].quantize(Decimal("0.0001"))
        item.peso_rateio = fk.get("peso_percentual", Decimal("0"))
        item.rateio_absorvido = fk.get("rateio", Decimal("0"))
        item.preco_final_unitario = (
            fk.get("preco_final", r["preco_total_base"]) / item.quantidade
        ).quantize(Decimal("0.0001"))
        item.lucro_absoluto = r["lucro_abs"].quantize(Decimal("0.0001"))

    for r in nfat_resultados:
        item = r["item"]
        item.bdi_taxa = Decimal("0")
        item.preco_venda_unitario = item.custo_direto_unitario
        item.preco_venda_total = r["custo_carregado"]
        item.peso_rateio = Decimal("0")
        item.rateio_absorvido = Decimal("0")
        item.preco_final_unitario = Decimal("0")
        item.lucro_absoluto = Decimal("0")

    # ── Passo 6: Atualizar cabeçalho ──────────────────────────────────────────
    orc.total_custo_direto = total_custo_direto.quantize(Decimal("0.0001"))
    orc.total_proposta = total_proposta.quantize(Decimal("0.0001"))
    orc.margem_liquida_real = mlr

    db.commit()

    # ── Passo 7: Montar resposta ──────────────────────────────────────────────
    fk_val = (
        (total_nao_faturavel / subtotal_faturavel * Decimal("100")).quantize(
            Decimal("0.0001")
        )
        if subtotal_faturavel > Decimal("0")
        else Decimal("0")
    )

    db.refresh(orc)
    todos_itens = db.query(OrcamentoItem).filter(OrcamentoItem.orcamento_id == id).all()

    return ResultadoCalculoRead(
        orcamento_id=orc.id,
        uf_execucao=orc.uf_execucao,
        beneficio_reidi=orc.beneficio_reidi,
        itens=[ItemCalculadoRead.model_validate(i) for i in todos_itens],
        subtotal_faturavel=subtotal_faturavel.quantize(Decimal("0.0001")),
        total_nao_faturavel=total_nao_faturavel.quantize(Decimal("0.0001")),
        total_proposta=total_proposta.quantize(Decimal("0.0001")),
        margem_liquida_real=mlr,
        fator_k_percentual=fk_val,
    )
