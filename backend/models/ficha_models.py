"""Models das Fichas Técnicas (BLOCO 2) — conforme docs/02 + docs/03.

- Ficha de Equipe: cargos (bd_RH) + EPI + refeição/hospedagem por seguimento.
- Ficha de Produto: BOM recursivo (material OU sub-produto).
- Ficha de Serviço: equipe + frota + ferramental (+ produto opc) numa MESMA linha.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DECIMAL,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base

# ── Ficha de Equipe ──────────────────────────────────────────────────────────


class FichaEquipe(Base):
    """2.1 fichas_equipe — cabeçalho de equipe operacional por seguimento."""

    __tablename__ = "fichas_equipe"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    seguimento: Mapped[str] = mapped_column(String(50), nullable=False)
    # EPS, HORIZONTAL, VERTICAL, APOIO
    custo_dia_total: Mapped[Decimal] = mapped_column(
        DECIMAL(12, 4), nullable=False, default=Decimal("0")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    itens: Mapped[list["FichaEquipeItem"]] = relationship(
        "FichaEquipeItem", back_populates="ficha", cascade="all, delete-orphan"
    )


class FichaEquipeItem(Base):
    """2.2 fichas_equipe_itens — cargo + EPI + refeição/hospedagem por linha.

    custo_dia_linha = (custo_mo + custo_epi + refeicao + hospedagem) × quantidade
    """

    __tablename__ = "fichas_equipe_itens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ficha_equipe_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("fichas_equipe.id", ondelete="CASCADE"), nullable=False
    )
    rh_id: Mapped[int] = mapped_column(Integer, ForeignKey("bd_RH.id"), nullable=False)
    quantidade: Mapped[int] = mapped_column(Integer, nullable=False)
    custo_mo: Mapped[Decimal] = mapped_column(DECIMAL(10, 4), nullable=False)
    epi_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("bd_EPI.id"), nullable=True
    )
    custo_epi: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 4), nullable=False, default=Decimal("0")
    )
    refeicao: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 4), nullable=False, default=Decimal("0")
    )
    hospedagem: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 4), nullable=False, default=Decimal("0")
    )
    custo_dia_linha: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 4), nullable=False, default=Decimal("0")
    )

    ficha: Mapped["FichaEquipe"] = relationship("FichaEquipe", back_populates="itens")


# ── Ficha de Produto (BOM recursivo) ─────────────────────────────────────────


class FichaProduto(Base):
    """2.3 fichas_produto — produto orçável (placa, kit, componente)."""

    __tablename__ = "fichas_produto"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    unidade: Mapped[str] = mapped_column(String(10), nullable=False)
    custo_total: Mapped[Decimal] = mapped_column(
        DECIMAL(12, 4), nullable=False, default=Decimal("0")
    )
    possui_ficha: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    itens: Mapped[list["FichaProdutoItem"]] = relationship(
        "FichaProdutoItem",
        foreign_keys="FichaProdutoItem.ficha_produto_id",
        back_populates="ficha",
        cascade="all, delete-orphan",
    )


class FichaProdutoItem(Base):
    """2.4 fichas_produto_itens — material bruto OU sub-produto (BOM)."""

    __tablename__ = "fichas_produto_itens"
    __table_args__ = (
        CheckConstraint(
            "(material_id IS NOT NULL AND componente_filho_id IS NULL) OR "
            "(material_id IS NULL AND componente_filho_id IS NOT NULL)",
            name="chk_bom_exclusividade",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ficha_produto_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("fichas_produto.id", ondelete="CASCADE"), nullable=False
    )
    material_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("bd_MATERIAIS.id"), nullable=True
    )
    componente_filho_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("fichas_produto.id"), nullable=True
    )
    quantidade: Mapped[Decimal] = mapped_column(DECIMAL(12, 6), nullable=False)
    unidade: Mapped[str] = mapped_column(String(10), nullable=False)
    custo_unitario: Mapped[Decimal] = mapped_column(DECIMAL(12, 4), nullable=False)
    custo_total_linha: Mapped[Decimal] = mapped_column(DECIMAL(12, 4), nullable=False)

    ficha: Mapped["FichaProduto"] = relationship(
        "FichaProduto", foreign_keys=[ficha_produto_id], back_populates="itens"
    )
    componente_filho: Mapped["FichaProduto | None"] = relationship(
        "FichaProduto", foreign_keys=[componente_filho_id]
    )


# ── Ficha de Serviço ─────────────────────────────────────────────────────────


class FichaServico(Base):
    """2.5 fichas_servico — serviço executável (vertical, horizontal, EPS)."""

    __tablename__ = "fichas_servico"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    seguimento: Mapped[str] = mapped_column(String(50), nullable=False)
    produtividade_dia: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2), CheckConstraint("produtividade_dia > 0"), nullable=False
    )
    unidade: Mapped[str] = mapped_column(String(10), nullable=False)
    possui_ficha: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    custo_unitario: Mapped[Decimal] = mapped_column(
        DECIMAL(12, 4), nullable=False, default=Decimal("0")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    recursos: Mapped[list["FichaServicoRecurso"]] = relationship(
        "FichaServicoRecurso", back_populates="ficha", cascade="all, delete-orphan"
    )


class FichaServicoRecurso(Base):
    """2.6 fichas_servico_recursos — equipe + frota + ferramental (+ produto opc).

    Uma linha agrega SIMULTANEAMENTE os recursos do serviço. Sem CHECK de
    exclusividade (a versão anterior forçava exatamente um — errado p/ o spec).

    custo_unitario do serviço =
        (equipe.custo_dia_total + frota.custo_diario + ferramental.custo_diario)
        / produtividade_dia + produto.custo_total
    """

    __tablename__ = "fichas_servico_recursos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ficha_servico_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("fichas_servico.id", ondelete="CASCADE"), nullable=False
    )
    ficha_equipe_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("fichas_equipe.id"), nullable=False
    )
    frota_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("bd_FROTAS.id"), nullable=False
    )
    ferramental_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("bd_FERRAMENTAL.id"), nullable=False
    )
    ficha_produto_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("fichas_produto.id"), nullable=True
    )

    ficha: Mapped["FichaServico"] = relationship(
        "FichaServico", back_populates="recursos"
    )
