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
from backend.models.extra_models import HistoricoDesconto, OrcamentoSegmento
from backend.models.ficha_models import FichaProduto, FichaServico
from backend.models.orcamento_models import Cliente, Orcamento, OrcamentoItem
from backend.models.param_models import ParametroSeguimento
from backend.schemas.orcamento_schemas import (
    ClienteCreate,
    ClienteRead,
    ClienteUpdate,
    ItemCalculadoRead,
    OrcamentoCreate,
    OrcamentoItemCreate,
    OrcamentoItemDescricaoPatch,
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


_EDITAVEIS = frozenset({"rascunho", "reprovado"})


def _guard_rascunho(orc: Orcamento) -> None:
    """Itens só editam em status editável (rascunho/reprovado). Demais congelam."""
    if orc.status not in _EDITAVEIS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Orçamento com status '{orc.status}' está congelado e não "
            "permite alterações de itens.",
        )


def _aplicar_segmentos(db: Session, orc: Orcamento, segmentos: list[str]) -> None:
    """Substitui em bloco os segmentos do orçamento. Valida contra ParametroSeguimento."""
    if len(segmentos) != len(set(segmentos)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Lista de segmentos contém duplicatas.",
        )
    validos = {
        s.nome
        for s in db.query(ParametroSeguimento)
        .filter(ParametroSeguimento.ativo.is_(True))
        .all()
    }
    for seg in segmentos:
        if seg not in validos:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Segmento inválido: '{seg}'. Cadastre em Parâmetros.",
            )
    orc.segmentos.clear()  # delete-orphan remove os antigos
    db.flush()
    for seg in segmentos:
        orc.segmentos.append(OrcamentoSegmento(seguimento=seg))


def _gravar_historico_desconto(db: Session, orc: Orcamento) -> None:
    """BLOCO 1.3 — grava o desconto concedido nesta versão ao aprovar."""
    itens = db.query(OrcamentoItem).filter(OrcamentoItem.orcamento_id == orc.id).all()
    subtotal_fat = sum(
        (Decimal(i.preco_venda_total) for i in itens if i.bloco in FATURAVEIS),
        Decimal("0"),
    )
    desc_frac = Decimal(orc.desconto_percentual or 0) / Decimal("100")
    db.add(
        HistoricoDesconto(
            orcamento_id=orc.id,
            versao=orc.versao,
            desconto_percentual=orc.desconto_percentual,
            subtotal_faturavel=_q4(subtotal_fat),
            desconto_total=_q4(subtotal_fat * desc_frac),
        )
    )


_TRANSICOES_STATUS: dict[str, frozenset[str]] = {
    "rascunho": frozenset({"enviado"}),
    "enviado": frozenset({"aprovado", "reprovado", "perdida"}),
    "aprovado": frozenset({"fechado", "perdida"}),
    "reprovado": frozenset({"rascunho"}),
    "perdida": frozenset(),
    "fechado": frozenset(),
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
    dados = body.model_dump()
    segmentos = dados.pop("segmentos", [])
    obj = Orcamento(**dados)
    db.add(obj)
    db.flush()
    _aplicar_segmentos(db, obj, segmentos)
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

    segmentos = dados.pop("segmentos", None)

    if "status" in dados:
        novo = dados.pop("status")
        _guard_transicao_status(obj.status, novo)
        obj.status = novo
        if novo == "aprovado":
            obj.aprovado_em = datetime.now(timezone.utc)
            _gravar_historico_desconto(db, obj)

    if dados:
        _guard_rascunho(obj)
        for k, v in dados.items():
            setattr(obj, k, v)

    if segmentos is not None:
        _guard_rascunho(obj)
        _aplicar_segmentos(db, obj, segmentos)

    db.commit()
    db.refresh(obj)
    return obj


@router.get(
    "/orcamentos/{id}/historico-descontos",
    tags=["orcamentos"],
)
def historico_descontos(id: int, db: Session = Depends(get_db)) -> list[dict]:
    """BLOCO 1.3 — histórico de descontos das versões (próprias e da cadeia de origem)."""
    from backend.models.extra_models import HistoricoDesconto

    orc = _get_or_404(db, Orcamento, id)
    # cadeia: este + ancestrais via orcamento_origem_id
    ids = [orc.id]
    cur = orc
    while cur.orcamento_origem_id:
        cur = db.get(Orcamento, cur.orcamento_origem_id)
        if not cur:
            break
        ids.append(cur.id)
    regs = (
        db.query(HistoricoDesconto)
        .filter(HistoricoDesconto.orcamento_id.in_(ids))
        .order_by(HistoricoDesconto.versao.asc())
        .all()
    )
    return [
        {
            "versao": r.versao,
            "desconto_percentual": r.desconto_percentual,
            "subtotal_faturavel": r.subtotal_faturavel,
            "desconto_total": r.desconto_total,
            "criado_em": r.criado_em,
        }
        for r in regs
    ]


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
        data_limite=origem.data_limite,
    )
    db.add(nova)
    db.flush()

    # Segmentos (classificação) acompanham a nova versão.
    for seg in origem.segmentos:
        nova.segmentos.append(OrcamentoSegmento(seguimento=seg.seguimento))

    for it in origem.itens:
        db.add(
            OrcamentoItem(
                orcamento_id=nova.id,
                bloco=it.bloco,
                ficha_servico_id=it.ficha_servico_id,
                ficha_produto_id=it.ficha_produto_id,
                produto_id=it.produto_id,
                tipo_origem=it.tipo_origem,
                descricao=it.descricao,
                descricao_cliente=it.descricao_cliente,
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
    if getattr(body, "produto_id", None):
        # BLOCO 1.5 — produto do orçamento vem do cadastro `produtos`; o custo vem da
        # ficha técnica vinculada (item_fichas → fichas_produto), se houver.
        from backend.models.param_models import UnidadeMedida
        from backend.models.produto_models import ItemFicha, Produto

        prod = _get_or_404(db, Produto, body.produto_id)
        custo = Decimal("0")
        vinc = (
            db.query(ItemFicha)
            .filter(
                ItemFicha.produto_id == prod.id,
                ItemFicha.ficha_produto_id.isnot(None),
            )
            .first()
        )
        if vinc and vinc.ficha_produto_id:
            fp = db.get(FichaProduto, vinc.ficha_produto_id)
            if fp:
                custo = Decimal(fp.custo_total)
        unidade = body.unidade or "un"
        if prod.unidade_id:
            um = db.get(UnidadeMedida, prod.unidade_id)
            if um:
                unidade = um.sigla
        return custo, unidade, "produto"
    if body.ficha_produto_id:
        from backend.models.param_models import UnidadeMedida
        from backend.models.produto_models import ItemFicha, Produto

        f = _get_or_404(db, FichaProduto, body.ficha_produto_id)
        if not f.possui_ficha:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Produto sem ficha (possui_ficha=False) não pode ser orçado.",
            )
        unidade = f.unidade
        prod_vinc = (
            db.query(Produto)
            .join(ItemFicha, ItemFicha.produto_id == Produto.id)
            .filter(ItemFicha.ficha_produto_id == f.id)
            .first()
        )
        if prod_vinc and prod_vinc.unidade_id:
            um = db.get(UnidadeMedida, prod_vinc.unidade_id)
            if um:
                unidade = um.sigla
        return Decimal(f.custo_total), unidade, "produto"
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
        produto_id=getattr(body, "produto_id", None),
        tipo_origem=tipo_origem,
        descricao=body.descricao,
        descricao_cliente=getattr(body, "descricao_cliente", None),
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


@router.patch(
    "/orcamentos/{id}/itens/{item_id}",
    response_model=OrcamentoItemRead,
    tags=["orcamentos"],
)
def patch_descricao_item(
    id: int,
    item_id: int,
    payload: OrcamentoItemDescricaoPatch,
    db: Session = Depends(get_db),
):
    """FOR-077 — edita a descrição exibida ao cliente (descricao_cliente).

    Preserva `descricao` (composição). Só em status editável (rascunho/reprovado).
    """
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
    item.descricao_cliente = payload.descricao
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

    # Passo 4 — base p/ Margem Líquida Real (calculada após aplicar o desconto)
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

    # Passo 5/6 — Desconto FLAT por linha (BLOCO 2.1 do prompt-melhorias):
    #   desconto_rateado = preco_venda_linha × (desconto% / 100)  [em TODAS as linhas]
    #   preco_venda_final = preco_venda_linha − desconto_rateado
    #   total_proposta = Σ (preco_venda_linha − desconto_rateado)
    desc_frac = Decimal(orc.desconto_percentual) / Decimal("100")
    total_desconto = Decimal("0")
    total_com_desconto = Decimal("0")

    # BLOCO 1.2 — desconto rateado APENAS em servicos+produtos (faturáveis).
    for r in fat:
        item = r["item"]
        fkr = fk_por_id.get(item.id, {})
        preco_linha = _q4(fkr.get("preco_final", r["preco_total_base"]))
        peso = fkr.get("peso_percentual", Decimal("0"))
        desc_linha = _q4(preco_linha * desc_frac)
        qtd = item.quantidade
        item.bdi_aplicado = r["bdi"]
        item.peso_rateio = peso
        item.desconto_rateado = desc_linha
        item.preco_venda_total = preco_linha
        # BLOCO 1.1 — unitário ANTES e DEPOIS do desconto
        item.preco_venda_unitario = _q4(preco_linha / qtd)
        item.preco_venda_unitario_final = _q4((preco_linha - desc_linha) / qtd)
        item.lucro_absoluto = _q4(r["lucro_abs"])
        total_desconto += desc_linha
        total_com_desconto += preco_linha - desc_linha

    # Itens não faturáveis (operacional/excepcionais): SEM desconto (BLOCO 1.2);
    # custo carregado é diluído nos faturáveis via Fator K — não soma de novo ao total.
    for r in nfat:
        item = r["item"]
        preco_linha = _q4(r["carregado"])
        item.bdi_aplicado = Decimal("0")
        item.preco_venda_unitario = Decimal(item.custo_direto_unitario)
        item.preco_venda_unitario_final = Decimal(item.custo_direto_unitario)
        item.preco_venda_total = preco_linha
        item.peso_rateio = Decimal("0")
        item.desconto_rateado = Decimal("0")
        item.lucro_absoluto = Decimal("0")

    total_proposta = _q4(total_com_desconto)
    mlr = margem_liquida_real(itens_mlr, total_proposta)
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
