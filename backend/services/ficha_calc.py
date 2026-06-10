"""ficha_calc.py — Cálculo de custos das fichas técnicas (docs/03).

Lookups nos bancos de dados + fórmulas em cascata:
  equipe_item: custo_mo=bd_RH.custo_diario; custo_epi=bd_EPI.custo_diario;
               refeicao/hospedagem=bd_DESPESAS[seguimento];
               custo_dia_linha=(custo_mo+custo_epi+refeicao+hospedagem)×quantidade
  equipe.custo_dia_total = Σ custo_dia_linha
  produto_item.custo_total_linha = quantidade × custo_unitario
  produto.custo_total = Σ custo_total_linha (BOM recursivo)
  servico.custo_unitario = (equipe.custo_dia_total + frota.custo_diario +
                            ferramental.custo_diario) / produtividade_dia + produto.custo_total
"""

from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy.orm import Session

from backend.models.bd_models import (
    BdDespesas,
    BdEPI,
    BdFerramental,
    BdFrotas,
    BdMateriais,
    BdRH,
)
from backend.models.ficha_models import (
    FichaEquipe,
    FichaProduto,
    FichaServico,
)


def _q4(v: Decimal) -> Decimal:
    return v.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def _despesas_seguimento(db: Session, seguimento: str) -> tuple[Decimal, Decimal]:
    """Retorna (refeicao, hospedagem) do bd_DESPESAS para o seguimento (0 se ausente)."""
    desp = (
        db.query(BdDespesas)
        .filter(BdDespesas.seguimento == seguimento, BdDespesas.ativo.is_(True))
        .first()
    )
    if not desp:
        return Decimal("0"), Decimal("0")
    return Decimal(desp.refeicao), Decimal(desp.hospedagem)


# ── Equipe ───────────────────────────────────────────────────────────────────


def calcular_item_equipe(
    db: Session, seguimento: str, rh_id: int, epi_id: int | None, quantidade: int
) -> dict:
    """Resolve lookups e calcula os custos de uma linha da ficha de equipe."""
    rh = db.get(BdRH, rh_id)
    if not rh:
        raise ValueError(f"bd_RH id={rh_id} não encontrado")
    custo_mo = Decimal(rh.custo_diario)

    custo_epi = Decimal("0")
    if epi_id is not None:
        epi = db.get(BdEPI, epi_id)
        if not epi:
            raise ValueError(f"bd_EPI id={epi_id} não encontrado")
        custo_epi = Decimal(epi.custo_diario)

    refeicao, hospedagem = _despesas_seguimento(db, seguimento)
    qtd = Decimal(quantidade)
    custo_dia_linha = _q4((custo_mo + custo_epi + refeicao + hospedagem) * qtd)

    return {
        "custo_mo": _q4(custo_mo),
        "custo_epi": _q4(custo_epi),
        "refeicao": _q4(refeicao),
        "hospedagem": _q4(hospedagem),
        "custo_dia_linha": custo_dia_linha,
    }


def recalcular_equipe(db: Session, ficha: FichaEquipe) -> Decimal:
    """Recalcula custo_dia_total da equipe a partir dos seus itens. Não commita."""
    total = sum((Decimal(i.custo_dia_linha) for i in ficha.itens), Decimal("0"))
    ficha.custo_dia_total = _q4(total)
    return ficha.custo_dia_total


# ── Produto (BOM) ────────────────────────────────────────────────────────────


def custo_unitario_componente(
    db: Session, material_id: int | None, componente_filho_id: int | None
) -> tuple[Decimal, str]:
    """Custo unitário + unidade de um componente (material bruto ou sub-produto)."""
    if material_id is not None:
        mat = db.get(BdMateriais, material_id)
        if not mat:
            raise ValueError(f"bd_MATERIAIS id={material_id} não encontrado")
        return Decimal(mat.valor_unitario), mat.unidade
    if componente_filho_id is not None:
        prod = db.get(FichaProduto, componente_filho_id)
        if not prod:
            raise ValueError(f"fichas_produto id={componente_filho_id} não encontrado")
        return Decimal(prod.custo_total), prod.unidade
    raise ValueError("material_id ou componente_filho_id obrigatório")


def recalcular_produto(db: Session, ficha: FichaProduto) -> Decimal:
    """Recalcula custo_total do produto a partir das linhas de BOM. Não commita."""
    total = sum((Decimal(i.custo_total_linha) for i in ficha.itens), Decimal("0"))
    ficha.custo_total = _q4(total)
    return ficha.custo_total


def detectar_ciclo_bom(
    db: Session, ficha_produto_id: int, componente_filho_id: int
) -> bool:
    """True se adicionar componente_filho_id a ficha_produto_id criar ciclo na BOM."""
    if componente_filho_id == ficha_produto_id:
        return True
    # DFS descendo pelos filhos do candidato; se alcançar a ficha-pai, há ciclo.
    from backend.models.ficha_models import FichaProdutoItem

    visitados: set[int] = set()
    pilha = [componente_filho_id]
    while pilha:
        atual = pilha.pop()
        if atual == ficha_produto_id:
            return True
        if atual in visitados:
            continue
        visitados.add(atual)
        filhos = (
            db.query(FichaProdutoItem.componente_filho_id)
            .filter(
                FichaProdutoItem.ficha_produto_id == atual,
                FichaProdutoItem.componente_filho_id.isnot(None),
            )
            .all()
        )
        pilha.extend(f[0] for f in filhos if f[0] is not None)
    return False


# ── Serviço ──────────────────────────────────────────────────────────────────


def calcular_custo_servico(
    db: Session,
    produtividade_dia: Decimal,
    ficha_equipe_id: int,
    frota_id: int,
    ferramental_id: int,
    ficha_produto_id: int | None,
) -> Decimal:
    """custo_unitario = (equipe+frota+ferr)/produtividade + produto.custo_total."""
    equipe = db.get(FichaEquipe, ficha_equipe_id)
    if not equipe:
        raise ValueError(f"fichas_equipe id={ficha_equipe_id} não encontrado")
    frota = db.get(BdFrotas, frota_id)
    if not frota:
        raise ValueError(f"bd_FROTAS id={frota_id} não encontrado")
    ferr = db.get(BdFerramental, ferramental_id)
    if not ferr:
        raise ValueError(f"bd_FERRAMENTAL id={ferramental_id} não encontrado")

    soma_dia = (
        Decimal(equipe.custo_dia_total)
        + Decimal(frota.custo_diario)
        + Decimal(ferr.custo_diario)
    )
    prod = Decimal(produtividade_dia)
    if prod <= 0:
        raise ValueError("produtividade_dia deve ser > 0")

    custo = soma_dia / prod
    if ficha_produto_id is not None:
        produto = db.get(FichaProduto, ficha_produto_id)
        if not produto:
            raise ValueError(f"fichas_produto id={ficha_produto_id} não encontrado")
        custo += Decimal(produto.custo_total)

    return _q4(custo)


def recalcular_servico(db: Session, ficha: FichaServico) -> Decimal:
    """Recalcula custo_unitario somando todos os recursos vinculados. Não commita.

    Quando há múltiplas linhas de recurso, soma a contribuição de cada uma.
    """
    total = Decimal("0")
    for r in ficha.recursos:
        total += calcular_custo_servico(
            db,
            Decimal(ficha.produtividade_dia),
            r.ficha_equipe_id,
            r.frota_id,
            r.ferramental_id,
            r.ficha_produto_id,
        )
    ficha.custo_unitario = _q4(total)
    return ficha.custo_unitario
