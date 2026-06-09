"""
Router de relatórios e dashboard.

Endpoints:
  GET /orcamentos/{id}/export/pdf   — exporta proposta em PDF
  GET /orcamentos/{id}/versoes      — lista versões de uma proposta
  GET /dashboard                    — métricas agregadas do mês/geral
"""

from __future__ import annotations

import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.orcamento_models import Cliente, Orcamento, OrcamentoItem
from backend.services.export_pdf import gerar_pdf_proposta

router = APIRouter(tags=["relatorios"])


# ── helpers ────────────────────────────────────────────────────────────────────


def _get_orc_or_404(db: Session, orc_id: int) -> Orcamento:
    orc = db.get(Orcamento, orc_id)
    if not orc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Orçamento não encontrado"
        )
    return orc


# ── Export PDF ─────────────────────────────────────────────────────────────────


@router.get("/orcamentos/{id}/export/pdf")
def exportar_pdf(id: int, db: Session = Depends(get_db)) -> Response:
    """Gera e retorna o PDF da proposta como download."""
    orc = _get_orc_or_404(db, id)

    cliente = db.get(Cliente, orc.cliente_id)
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente vinculado ao orçamento não encontrado",
        )

    itens = db.query(OrcamentoItem).filter(OrcamentoItem.orcamento_id == id).all()

    pdf_bytes = gerar_pdf_proposta(orc, itens, cliente)

    filename = f"proposta_{orc.numero_proposta}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Versões de proposta ────────────────────────────────────────────────────────


@router.get("/orcamentos/{id}/versoes")
def listar_versoes(id: int, db: Session = Depends(get_db)) -> list[dict]:
    """
    Retorna as versões de uma proposta.

    Por ora retorna apenas o orçamento corrente em lista.
    Implementação futura: buscar orçamentos com mesmo número base (sem sufixo -vN).
    """
    orc = _get_orc_or_404(db, id)

    return [
        {
            "id": orc.id,
            "numero_proposta": orc.numero_proposta,
            "versao": orc.versao,
            "status": orc.status,
            "total_proposta": orc.total_proposta,
            "criado_em": orc.criado_em,
        }
    ]


# ── Dashboard ──────────────────────────────────────────────────────────────────


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)) -> dict:
    """
    Métricas agregadas para o painel principal.

    Retorna:
      - total_orcado_mes: soma de total_proposta dos orçamentos criados no mês atual
      - margem_media: média de margem_liquida_real (apenas onde total_proposta > 0)
      - por_status: contagem por status
      - total_orcamentos: total geral de orçamentos
      - orcamentos_recentes: últimos 5 orçamentos
    """
    hoje = datetime.date.today()
    primeiro_dia_mes = datetime.datetime(hoje.year, hoje.month, 1)

    # Total orçado no mês
    resultado_mes = (
        db.query(func.sum(Orcamento.total_proposta))
        .filter(Orcamento.criado_em >= primeiro_dia_mes)
        .scalar()
    )
    total_orcado_mes: Decimal = (
        Decimal(str(resultado_mes)) if resultado_mes is not None else Decimal("0")
    )

    # Margem média (somente orçamentos com total_proposta > 0)
    resultado_margem = (
        db.query(func.avg(Orcamento.margem_liquida_real))
        .filter(Orcamento.total_proposta > Decimal("0"))
        .scalar()
    )
    margem_media: Decimal = (
        Decimal(str(resultado_margem)).quantize(Decimal("0.000001"))
        if resultado_margem is not None
        else Decimal("0")
    )

    # Contagem por status
    status_counts = (
        db.query(Orcamento.status, func.count(Orcamento.id))
        .group_by(Orcamento.status)
        .all()
    )
    por_status: dict[str, int] = {
        "rascunho": 0,
        "enviado": 0,
        "aprovado": 0,
        "rejeitado": 0,
    }
    for s, cnt in status_counts:
        if s in por_status:
            por_status[s] = cnt
        else:
            por_status[s] = cnt  # status não previsto ainda aparece

    # Total geral
    total_orcamentos: int = db.query(func.count(Orcamento.id)).scalar() or 0

    # Últimos 5 orçamentos
    recentes = db.query(Orcamento).order_by(Orcamento.criado_em.desc()).limit(5).all()
    orcamentos_recentes = [
        {
            "id": o.id,
            "numero_proposta": o.numero_proposta,
            "status": o.status,
            "total_proposta": o.total_proposta,
            "criado_em": o.criado_em,
        }
        for o in recentes
    ]

    return {
        "total_orcado_mes": total_orcado_mes,
        "margem_media": margem_media,
        "por_status": por_status,
        "total_orcamentos": total_orcamentos,
        "orcamentos_recentes": orcamentos_recentes,
    }
