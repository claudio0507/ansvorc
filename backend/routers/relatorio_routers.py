"""
Router de relatórios e dashboard.

Endpoints:
  GET /orcamentos/{id}/export/pdf   — exporta proposta em PDF
  GET /orcamentos/{id}/versoes      — lista versões de uma proposta
  GET /dashboard                    — métricas agregadas do mês/geral
"""

from __future__ import annotations

import datetime
import re
from datetime import date, timedelta
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

    safe_num = re.sub(r"[^\w\-.]", "_", str(orc.numero or ""))
    filename = f"proposta_{safe_num}.pdf"
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
            "numero": orc.numero,
            "versao": orc.versao,
            "status": orc.status,
            "total_proposta": orc.total_proposta,
            "created_at": orc.created_at,
        }
    ]


# ── Dashboard ──────────────────────────────────────────────────────────────────


def _soma_proposta_status(db, status_val, desde=None):
    q = db.query(func.sum(Orcamento.total_proposta)).filter(
        Orcamento.status == status_val
    )
    if desde is not None:
        q = q.filter(Orcamento.created_at >= desde)
    return Decimal(str(q.scalar() or 0))


def _soma_margem_rs(db, desde=None):
    q = db.query(
        func.sum(Orcamento.total_proposta - Orcamento.total_custo_direto)
    ).filter(Orcamento.status == "fechado")
    if desde is not None:
        q = q.filter(Orcamento.created_at >= desde)
    return Decimal(str(q.scalar() or 0))


def _media_margem_pct(db, desde=None):
    q = db.query(func.avg(Orcamento.margem_liquida_real)).filter(
        Orcamento.status == "fechado"
    )
    if desde is not None:
        q = q.filter(Orcamento.created_at >= desde)
    r = q.scalar()
    return (
        Decimal(str(r)).quantize(Decimal("0.000001"))
        if r is not None
        else Decimal("0")
    )


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)) -> dict:
    """
    Métricas agregadas para o painel principal (redefinidas por STATUS).

    Retorna:
      - total_orcado_mes/acumulado: Σ total_proposta dos orçamentos 'enviado'
      - margem_rs_mes/acumulado: Σ (total_proposta − total_custo_direto) dos 'fechado'
      - margem_pct_mes/acumulado: média de margem_liquida_real dos 'fechado'
      - margem_media/margem_acumulada: aliases de margem_pct (compat.)
      - por_status: contagem por status
      - total_orcamentos: total geral de orçamentos
      - orcamentos_recentes: últimos 5 orçamentos
    (mês = created_at >= 1º dia do mês atual)
    """
    hoje = datetime.date.today()
    primeiro_dia_mes = datetime.datetime(hoje.year, hoje.month, 1)

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
        "reprovado": 0,
        "perdida": 0,
        "fechado": 0,
    }
    for s, cnt in status_counts:
        if s in por_status:
            por_status[s] = cnt
        else:
            por_status[s] = cnt  # status não previsto ainda aparece

    # Total geral
    total_orcamentos: int = db.query(func.count(Orcamento.id)).scalar() or 0

    # Últimos 5 orçamentos
    recentes = db.query(Orcamento).order_by(Orcamento.created_at.desc()).limit(5).all()
    orcamentos_recentes = [
        {
            "id": o.id,
            "numero": o.numero,
            "status": o.status,
            "total_proposta": o.total_proposta,
            "created_at": o.created_at,
        }
        for o in recentes
    ]

    return {
        "total_orcado_mes": _soma_proposta_status(db, "enviado", primeiro_dia_mes),
        "total_orcado_acumulado": _soma_proposta_status(db, "enviado"),
        "margem_rs_mes": _soma_margem_rs(db, primeiro_dia_mes),
        "margem_rs_acumulado": _soma_margem_rs(db),
        "margem_pct_mes": _media_margem_pct(db, primeiro_dia_mes),
        "margem_pct_acumulado": _media_margem_pct(db),
        "margem_media": _media_margem_pct(db, primeiro_dia_mes),
        "margem_acumulada": _media_margem_pct(db),
        "por_status": por_status,
        "total_orcamentos": total_orcamentos,
        "orcamentos_recentes": orcamentos_recentes,
    }


# ── Notificações / Prazos ──────────────────────────────────────────────────────


@router.get("/notificacoes")
def listar_notificacoes(db: Session = Depends(get_db)) -> dict:
    """Prazos de envio iminentes (rascunho/reprovado, até amanhã)."""
    hoje = date.today()
    amanha = hoje + timedelta(days=1)
    orcs = (
        db.query(Orcamento)
        .filter(Orcamento.status.in_(["rascunho", "reprovado"]))
        .filter(Orcamento.data_limite.isnot(None))
        .filter(Orcamento.data_limite <= amanha)
        .order_by(Orcamento.data_limite)
        .all()
    )

    def _urg(d):
        return "atrasado" if d < hoje else "hoje" if d == hoje else "amanha"

    itens = [
        {
            "id": o.id,
            "numero": o.numero,
            "obra": o.obra,
            "data_limite": o.data_limite,
            "urgencia": _urg(o.data_limite),
        }
        for o in orcs
    ]
    return {"total": len(itens), "notificacoes": itens}


@router.get("/prazos")
def listar_prazos(mes: str | None = None, db: Session = Depends(get_db)) -> list[dict]:
    """Orçamentos rascunho/reprovado com data_limite no mês (para o calendário)."""
    hoje = date.today()
    if mes:
        ano, m = int(mes[:4]), int(mes[5:7])
    else:
        ano, m = hoje.year, hoje.month
    inicio = date(ano, m, 1)
    fim = date(ano + (m == 12), (m % 12) + 1, 1)
    orcs = (
        db.query(Orcamento)
        .filter(Orcamento.status.in_(["rascunho", "reprovado"]))
        .filter(Orcamento.data_limite.isnot(None))
        .filter(Orcamento.data_limite >= inicio, Orcamento.data_limite < fim)
        .order_by(Orcamento.data_limite)
        .all()
    )

    def _urg(d):
        if d < hoje:
            return "atrasado"
        if d == hoje:
            return "hoje"
        if d == hoje + timedelta(days=1):
            return "amanha"
        return "futuro"

    return [
        {
            "id": o.id,
            "numero": o.numero,
            "obra": o.obra,
            "data_limite": o.data_limite,
            "urgencia": _urg(o.data_limite),
        }
        for o in orcs
    ]
