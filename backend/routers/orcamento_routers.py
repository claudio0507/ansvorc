"""Routers de Orçamento e CRM — itens com custo automático, cálculo BDI/Fator K,
desconto rateado, versionamento e snapshot imutável.

Conforme docs/02 (schema), docs/04 (motor) e regras de integridade.
"""

from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.bd_models import BdBDI, BdEstrutura
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
    ItemFaturavel,
    aplicar_mod_fat,
    aplicar_reidi,
    calcular_bdi_completo,
    calcular_bdi_sombra,
    calcular_fator_k,
    margem_liquida_real,
)

router = APIRouter()

FATURAVEIS = {"servicos", "produtos"}
NAO_FATURAVEIS = {"operacional", "excepcionais"}


def _q4(v: Decimal) -> Decimal:
    return v.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def _get_or_404(db: Session, model, pk: int):
    obj = db.get(model, pk)
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Não encontrado"
        )
    return obj


def _guard_rascunho(orc: Orcamento) -> None:
    if orc.status != "rascunho":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Orçamento com status '{orc.status}' não pode ser editado. "
            "Apenas orçamentos em 'rascunho' permitem alterações.",
        )


_TRANSICOES_STATUS: dict[str, frozenset[str]] = {
    "rascunho": frozenset({"enviado"}),
    "enviado": frozenset({"aprovado", "rejeitado"}),
    "aprovado": frozenset(),
    "rejeitado": frozenset({"rascunho"}),
}


def _guard_transicao_status(atual: str, novo: str) -> None:
    permitidos = _TRANSICOES_STATUS.get(atual, frozenset())
    if novo not in permitidos:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Transição de status inválida: '{atual}' → '{novo}'. "
            f"Permitido a partir de '{atual}': {sorted(permitidos) or 'nenhum'}.",
        )


def _impostos_base(db: Session, mod_fat: str, uf: str) -> dict:
    """Monta impostos base de um item a partir de bd_BDI (modalidade, uf).

    Retorna pis, cofins, issqn, icms (discretos) + adm e cf. Fallback em constantes
    de ADM/CF quando não há registro cadastrado (alíquotas fiscais = 0 sem registro).
    """
    row = (
        db.query(BdBDI)
        .filter(BdBDI.modalidade == mod_fat, BdBDI.uf == uf, BdBDI.ativo.is_(True))
        .first()
    )
    if row:
        return {
            "adm": Decimal(row.despesas_adm),
            "cf": Decimal(row.custo_financeiro),
            "pis": Decimal(row.pis),
            "cofins": Decimal(row.cofins),
            "issqn": Decimal(row.issqn),
            "icms": Decimal(row.icms),
        }
    return {
        "adm": ADM_PADRAO,
        "cf": CF_PADRAO,
        "pis": Decimal("0"),
        "cofins": Decimal("0"),
        "issqn": Decimal("0"),
        "icms": Decimal("0"),
    }


# ── Clientes ──────────────────────────────────────────────────────────────────


@router.get("/clientes", response_model=list[ClienteRead], tags=["clientes"])
def listar_clientes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return db.query(Cliente).offset(skip).limit(limit).all()


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
def listar_orcamentos(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    busca: str | None = None,
    status_filtro: str | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
):
    q = db.query(Orcamento)
    if status_filtro:
        q = q.filter(Orcamento.status == status_filtro)
    if busca:
        like = f"%{busca}%"
        q = q.filter((Orcamento.numero.ilike(like)) | (Orcamento.obra.ilike(like)))
    return q.offset(skip).limit(limit).all()


@router.post(
    "/orcamentos",
    response_model=OrcamentoRead,
    status_code=status.HTTP_201_CREATED,
    tags=["orcamentos"],
)
def criar_orcamento(body: OrcamentoCreate, db: Session = Depends(get_db)):
    _get_or_404(db, Cliente, body.cliente_id)
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
    dados = body.model_dump(exclude_none=True)

    if "status" in dados:
        novo = dados.pop("status")
        _guard_transicao_status(obj.status, novo)
        obj.status = novo
        if novo == "aprovado":
            obj.aprovado_em = datetime.now(timezone.utc)

    if dados:
        _guard_rascunho(obj)
        for k, v in dados.items():
            setattr(obj, k, v)

    db.commit()
    db.refresh(obj)
    return obj


@router.post(
    "/orcamentos/{id}/reabrir",
    response_model=OrcamentoRead,
    status_code=status.HTTP_201_CREATED,
    tags=["orcamentos"],
)
def reabrir_orcamento(id: int, db: Session = Depends(get_db)):
    """Cria uma NOVA versão (rascunho) a partir de um orçamento aprovado.

    O orçamento original permanece imutável (auditoria). Itens são copiados.
    """
    origem = _get_or_404(db, Orcamento, id)
    if origem.status != "aprovado":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Apenas orçamentos aprovados podem ser reabertos em nova versão.",
        )

    nova = Orcamento(
        numero=f"{origem.numero}-v{origem.versao + 1}",
        cliente_id=origem.cliente_id,
        obra=origem.obra,
        uf_execucao=origem.uf_execucao,
        beneficio_reidi=origem.beneficio_reidi,
        desconto_percentual=origem.desconto_percentual,
        status="rascunho",
        versao=origem.versao + 1,
        orcamento_origem_id=origem.id,
        created_by=origem.created_by,
    )
    db.add(nova)
    db.flush()

    for it in origem.itens:
        db.add(
            OrcamentoItem(
                orcamento_id=nova.id,
                bloco=it.bloco,
                ficha_servico_id=it.ficha_servico_id,
                ficha_produto_id=it.ficha_produto_id,
                tipo_origem=it.tipo_origem,
                descricao=it.descricao,
                unidade=it.unidade,
                quantidade=it.quantidade,
                mod_fat=it.mod_fat,
                margem_lucro=it.margem_lucro,
                custo_direto_unitario=it.custo_direto_unitario,
                flag_aprovacao=it.flag_aprovacao,
            )
        )
    db.commit()
    db.refresh(nova)
    return nova


@router.delete(
    "/orcamentos/{id}", status_code=status.HTTP_204_NO_CONTENT, tags=["orcamentos"]
)
def excluir_orcamento(id: int, db: Session = Depends(get_db)):
    obj = _get_or_404(db, Orcamento, id)
    _guard_rascunho(obj)
    db.delete(obj)
    db.commit()


# ── Itens do Orçamento ────────────────────────────────────────────────────────


def _custo_e_unidade_da_ficha(db: Session, body: OrcamentoItemCreate) -> tuple:
    """Resolve custo_direto_unitario, unidade e tipo_origem a partir da origem.

    Faturáveis puxam custo da ficha (sem digitação). Operacional puxa de
    bd_ESTRUTURA_OPERACIONAL pela descrição. Manual usa o custo informado.
    """
    if body.ficha_servico_id:
        f = _get_or_404(db, FichaServico, body.ficha_servico_id)
        if not f.possui_ficha:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Serviço sem ficha (possui_ficha=False) não pode ser orçado.",
            )
        return Decimal(f.custo_unitario), f.unidade, "servico"
    if body.ficha_produto_id:
        f = _get_or_404(db, FichaProduto, body.ficha_produto_id)
        if not f.possui_ficha:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Produto sem ficha (possui_ficha=False) não pode ser orçado.",
            )
        return Decimal(f.custo_total), f.unidade, "produto"
    if body.bloco == "operacional":
        # Custo do bd_ESTRUTURA_OPERACIONAL pela descrição (item)
        est = (
            db.query(BdEstrutura)
            .filter(BdEstrutura.item == body.descricao, BdEstrutura.ativo.is_(True))
            .first()
        )
        if est:
            return Decimal(est.valor_unitario), est.unidade, "operacional"
        return Decimal(body.custo_direto_unitario), body.unidade, "operacional"
    # excepcional/manual: custo digitado
    return Decimal(body.custo_direto_unitario), body.unidade, "manual"


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

    custo, unidade, tipo_origem = _custo_e_unidade_da_ficha(db, body)

    obj = OrcamentoItem(
        orcamento_id=id,
        bloco=body.bloco,
        ficha_servico_id=body.ficha_servico_id,
        ficha_produto_id=body.ficha_produto_id,
        tipo_origem=tipo_origem,
        descricao=body.descricao,
        unidade=unidade,
        quantidade=body.quantidade,
        mod_fat=body.mod_fat,
        margem_lucro=body.margem_lucro,
        custo_direto_unitario=custo,
        flag_aprovacao=(body.bloco == "excepcionais"),
    )
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

    dados = body.model_dump(exclude_none=True)
    # custo_direto_unitario só é editável em itens manuais/operacionais
    if "custo_direto_unitario" in dados and item.tipo_origem in ("servico", "produto"):
        dados.pop("custo_direto_unitario")
    for k, v in dados.items():
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
    """Pipeline: BDI (sombra/completo) → Fator K → desconto rateado → MLR.

    margem_lucro é percentual (10 = 10%); convertida p/ fração no motor.
    """
    orc = _get_or_404(db, Orcamento, id)
    _guard_rascunho(orc)
    itens = db.query(OrcamentoItem).filter(OrcamentoItem.orcamento_id == id).all()
    if not itens:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="O orçamento não possui itens para calcular.",
        )

    uf = orc.uf_execucao
    reidi = orc.beneficio_reidi
    cache: dict[str, dict] = {}

    def imp_base(mod_fat: str) -> dict:
        if mod_fat not in cache:
            cache[mod_fat] = _impostos_base(db, mod_fat, uf)
        return cache[mod_fat]

    itens_fat = [i for i in itens if i.bloco in FATURAVEIS]
    itens_nfat = [i for i in itens if i.bloco in NAO_FATURAVEIS]

    # Passo 1 — BDI completo dos faturáveis
    fat: list[dict] = []
    total_custo_direto = Decimal("0")
    for item in itens_fat:
        mod_fat = item.mod_fat if item.mod_fat != "-" else "BDI-MAT+MO"
        params = imp_base(mod_fat)
        imp = {
            "pis": params["pis"],
            "cofins": params["cofins"],
            "issqn": params["issqn"],
            "icms": params["icms"],
        }
        if reidi:
            imp = aplicar_reidi(imp)
        imp = aplicar_mod_fat(mod_fat, imp)
        margem_frac = Decimal(item.margem_lucro) / Decimal("100")
        try:
            bdi = calcular_bdi_completo(
                despesas_adm=params["adm"],
                custo_financeiro=params["cf"],
                margem=margem_frac,
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
        cdu = Decimal(item.custo_direto_unitario)
        preco_unit_base = cdu * (Decimal("1") + bdi)
        preco_total_base = preco_unit_base * item.quantidade
        lucro_abs = (
            cdu
            * item.quantidade
            * (Decimal("1") + params["adm"])
            * (Decimal("1") + params["cf"])
            * margem_frac
        )
        total_custo_direto += cdu * item.quantidade
        fat.append(
            {
                "item": item,
                "bdi": bdi,
                "preco_unit_base": preco_unit_base,
                "preco_total_base": preco_total_base,
                "lucro_abs": lucro_abs,
                "adm": params["adm"],
                "cf": params["cf"],
                "margem_frac": margem_frac,
            }
        )

    # Passo 2 — BDI Sombra dos não faturáveis
    total_nao_faturavel = Decimal("0")
    nfat: list[dict] = []
    sombra = _impostos_base(db, "BDI-MAT+MO", uf)
    pis_s, cof_s, iss_s = sombra["pis"], sombra["cofins"], sombra["issqn"]
    if reidi:
        pis_s = cof_s = Decimal("0")
    for item in itens_nfat:
        carregado = calcular_bdi_sombra(
            custo_direto=Decimal(item.custo_direto_unitario) * item.quantidade,
            despesas_adm=sombra["adm"],
            pis=pis_s,
            cofins=cof_s,
            issqn=iss_s,
        )
        total_custo_direto += Decimal(item.custo_direto_unitario) * item.quantidade
        total_nao_faturavel += carregado
        nfat.append({"item": item, "carregado": carregado})

    # Passo 3 — Fator K
    itens_fk = [
        ItemFaturavel(
            id=r["item"].id,
            custo_direto=Decimal(r["item"].custo_direto_unitario)
            * r["item"].quantidade,
            preco_base_total=r["preco_total_base"],
        )
        for r in fat
    ]
    fk_por_id = {r["id"]: r for r in calcular_fator_k(itens_fk, total_nao_faturavel)}

    subtotal_faturavel = sum((r["preco_total_base"] for r in fat), Decimal("0"))
    total_antes_desc = subtotal_faturavel + total_nao_faturavel

    # Passo 4 — Margem Líquida Real (sobre total antes do desconto)
    itens_mlr = [
        {
            "custo_direto": Decimal(r["item"].custo_direto_unitario),
            "quantidade": r["item"].quantidade,
            "margem": r["margem_frac"],
            "despesas_adm": r["adm"],
            "custo_financeiro": r["cf"],
        }
        for r in fat
    ]
    mlr = margem_liquida_real(itens_mlr, total_antes_desc)

    # Passo 5 — Desconto sobre o total, rateado por peso de cada linha
    desc_frac = Decimal(orc.desconto_percentual) / Decimal("100")
    total_desconto = _q4(total_antes_desc * desc_frac)

    # Passo 6 — Persistir nos itens (preço com rateio K embutido no preço final)
    for r in fat:
        item = r["item"]
        fkr = fk_por_id.get(item.id, {})
        preco_final_linha = fkr.get("preco_final", r["preco_total_base"])
        peso = fkr.get("peso_percentual", Decimal("0"))
        item.bdi_aplicado = r["bdi"]
        item.peso_rateio = peso
        # desconto rateado proporcional ao peso da linha no faturável
        item.desconto_rateado = (
            _q4(total_desconto * (peso / Decimal("100"))) if peso else Decimal("0")
        )
        item.preco_venda_total = _q4(preco_final_linha)
        item.preco_venda_unitario = _q4(preco_final_linha / item.quantidade)
        item.lucro_absoluto = _q4(r["lucro_abs"])

    for r in nfat:
        item = r["item"]
        item.bdi_aplicado = Decimal("0")
        item.preco_venda_unitario = Decimal(item.custo_direto_unitario)
        item.preco_venda_total = _q4(r["carregado"])
        item.peso_rateio = Decimal("0")
        item.desconto_rateado = Decimal("0")
        item.lucro_absoluto = Decimal("0")

    total_proposta = _q4(total_antes_desc - total_desconto)
    orc.total_custo_direto = _q4(total_custo_direto)
    orc.total_proposta = total_proposta
    orc.margem_liquida_real = mlr
    db.commit()

    fk_val = (
        _q4(total_nao_faturavel / subtotal_faturavel * Decimal("100"))
        if subtotal_faturavel > 0
        else Decimal("0")
    )
    db.refresh(orc)
    todos = db.query(OrcamentoItem).filter(OrcamentoItem.orcamento_id == id).all()
    return ResultadoCalculoRead(
        orcamento_id=orc.id,
        uf_execucao=orc.uf_execucao,
        beneficio_reidi=orc.beneficio_reidi,
        desconto_percentual=orc.desconto_percentual,
        itens=[ItemCalculadoRead.model_validate(i) for i in todos],
        subtotal_faturavel=_q4(subtotal_faturavel),
        total_nao_faturavel=_q4(total_nao_faturavel),
        total_proposta=total_proposta,
        margem_liquida_real=mlr,
        fator_k_percentual=fk_val,
    )
