"""Endpoint de Business Intelligence — Histórico de Preços (BLOCO 4).

GET /api/v1/bi/precos
    Query params:
      - tipo: servico | produto | componente
      - item_id: ID do item (ficha_servico.id, produto.id, componente.id)
      - meses: número de meses para trás (padrão 12)

Retorna:
    - item: nome e tipo do item
    - metricas: preco_medio, preco_max, preco_min, preco_atual, variacao_pct, num_orcamentos
    - serie_temporal: lista de {mes, preco_medio, preco_min, preco_max}
    - precos_por_cliente: lista de {cliente, preco_unitario, media_ponderada}
    - dados_detalhados: lista de {data, cliente, obra, preco_unitario, quantidade, valor_total}
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.ficha_models import FichaServico
from backend.models.orcamento_models import Cliente, Orcamento, OrcamentoItem
from backend.models.produto_models import Componente, Produto

router = APIRouter()


@router.get("/bi/precos", tags=["BI"])
def bi_precos(
    tipo: str = Query(..., description="servico | produto | componente"),
    item_id: int = Query(..., description="ID do item"),
    meses: int = Query(12, ge=1, le=60, description="Meses para análise"),
    db: Session = Depends(get_db),
):
    """Histórico de preços de um item ao longo do tempo."""
    if tipo not in ("servico", "produto", "componente"):
        raise HTTPException(400, "tipo deve ser: servico, produto, componente")

    # ── Resolver item ──
    item_nome = ""
    if tipo == "servico":
        obj = db.get(FichaServico, item_id)
        if not obj:
            raise HTTPException(404, "Serviço não encontrado")
        item_nome = obj.nome or obj.codigo
        coluna_fk = OrcamentoItem.ficha_servico_id
    elif tipo == "produto":
        obj = db.get(Produto, item_id)
        if not obj:
            raise HTTPException(404, "Produto não encontrado")
        item_nome = obj.nome
        coluna_fk = OrcamentoItem.produto_id
    else:
        obj = db.get(Componente, item_id)
        if not obj:
            raise HTTPException(404, "Componente não encontrado")
        item_nome = obj.nome
        coluna_fk = OrcamentoItem.componente_id

    # ── Período ──
    data_limite = datetime.now(timezone.utc) - timedelta(days=meses * 30)

    # ── Query base: apenas orçamentos aprovados ──
    base = (
        db.query(OrcamentoItem)
        .join(Orcamento, OrcamentoItem.orcamento_id == Orcamento.id)
        .filter(
            coluna_fk == item_id,
            Orcamento.status == "aprovado",
            Orcamento.aprovado_em >= data_limite,
        )
    )

    itens = base.all()

    if not itens:
        return {
            "item": {"tipo": tipo, "id": item_id, "nome": item_nome},
            "metricas": None,
            "serie_temporal": [],
            "precos_por_cliente": [],
            "dados_detalhados": [],
            "mensagem": "Nenhum orçamento aprovado encontrado no período.",
        }

    # ── Métricas agregadas ──
    precos = [i.preco_venda_unitario for i in itens]
    preco_medio = sum(precos, Decimal("0")) / len(precos)
    preco_max = max(precos)
    preco_min = min(precos)
    preco_atual = precos[-1]  # último orçamento aprovado

    if len(precos) >= 2 and precos[0] != 0:
        variacao_pct = float((precos[-1] - precos[0]) / precos[0] * 100)
    else:
        variacao_pct = 0.0

    num_orcamentos = len(set(i.orcamento_id for i in itens))

    metricas = {
        "preco_medio": preco_medio,
        "preco_max": preco_max,
        "preco_min": preco_min,
        "preco_atual": preco_atual,
        "variacao_pct": round(variacao_pct, 1),
        "num_orcamentos": num_orcamentos,
        "num_registros": len(itens),
    }

    # ── Série temporal (agrupada por mês) ──
    from collections import defaultdict

    por_mes: dict[str, list[Decimal]] = defaultdict(list)
    for i in itens:
        if i.orcamento.aprovado_em:
            chave = i.orcamento.aprovado_em.strftime("%Y-%m")
            por_mes[chave].append(i.preco_venda_unitario)

    serie_temporal = []
    for mes in sorted(por_mes.keys()):
        vals = por_mes[mes]
        serie_temporal.append({
            "mes": mes,
            "preco_medio": sum(vals, Decimal("0")) / len(vals),
            "preco_min": min(vals),
            "preco_max": max(vals),
            "contagem": len(vals),
        })

    # ── Preços por cliente ──
    por_cliente: dict[str, list[Decimal]] = defaultdict(list)
    for i in itens:
        nome = i.orcamento.cliente_obj.nome if i.orcamento.cliente_obj else "Sem cliente"
        por_cliente[nome].append(i.preco_venda_unitario)

    precos_por_cliente = []
    for cliente_nome, vals in por_cliente.items():
        media = sum(vals, Decimal("0")) / len(vals)
        precos_por_cliente.append({
            "cliente": cliente_nome,
            "preco_medio": media,
            "preco_min": min(vals),
            "preco_max": max(vals),
            "contagem": len(vals),
        })

    # ── Dados detalhados ──
    dados_detalhados = []
    for i in sorted(itens, key=lambda x: x.orcamento.aprovado_em or datetime.min):
        dados_detalhados.append({
            "data": i.orcamento.aprovado_em.isoformat() if i.orcamento.aprovado_em else None,
            "orcamento_numero": i.orcamento.numero,
            "cliente": i.orcamento.cliente_obj.nome if i.orcamento.cliente_obj else "",
            "obra": i.orcamento.obra or "",
            "preco_unitario": i.preco_venda_unitario,
            "quantidade": i.quantidade,
            "valor_total": i.preco_venda_total,
        })

    return {
        "item": {"tipo": tipo, "id": item_id, "nome": item_nome},
        "metricas": metricas,
        "serie_temporal": serie_temporal,
        "precos_por_cliente": precos_por_cliente,
        "dados_detalhados": dados_detalhados,
    }
