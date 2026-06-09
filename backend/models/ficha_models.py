from decimal import Decimal

from sqlalchemy import (
    DECIMAL,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base

# ── Fichas de Equipe ─────────────────────────────────────────────────────────


class FichaEquipe(Base):
    """Cabeçalho de uma ficha de equipe operacional."""

    __tablename__ = "fichas_equipe"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    producao_diaria: Mapped[Decimal] = mapped_column(
        DECIMAL(12, 2), nullable=False, default=Decimal("1.00")
    )
    # unidade de produção (m², m, un, dia…)
    unidade_producao: Mapped[str] = mapped_column(
        String(10), nullable=False, default="dia"
    )
    possui_itens: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    itens: Mapped[list["FichaEquipeItem"]] = relationship(
        "FichaEquipeItem", back_populates="ficha", cascade="all, delete-orphan"
    )


class FichaEquipeItem(Base):
    """Item de uma ficha de equipe: cargo RH + EPIs + ferramental."""

    __tablename__ = "fichas_equipe_itens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ficha_equipe_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("fichas_equipe.id", ondelete="CASCADE"), nullable=False
    )
    # Tipo do recurso: RH | EPI | FERRAMENTAL
    tipo_recurso: Mapped[str] = mapped_column(String(20), nullable=False)

    # Exatamente um dos três FKs deve ser preenchido
    rh_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("bd_RH.id"), nullable=True
    )
    epi_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("bd_EPI.id"), nullable=True
    )
    ferramental_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("bd_FERRAMENTAL.id"), nullable=True
    )

    quantidade: Mapped[Decimal] = mapped_column(DECIMAL(12, 4), nullable=False)
    # Custo unitário capturado no momento da adição (snapshot lookup)
    custo_unitario_gravado: Mapped[Decimal] = mapped_column(
        DECIMAL(12, 4), nullable=False
    )
    observacao: Mapped[str | None] = mapped_column(String(255), nullable=True)

    ficha: Mapped["FichaEquipe"] = relationship("FichaEquipe", back_populates="itens")


# ── Fichas de Produto (BOM recursivo) ────────────────────────────────────────


class FichaProduto(Base):
    """Cabeçalho de uma ficha de produto (placa, kit, componente montado)."""

    __tablename__ = "fichas_produto"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    unidade_medida: Mapped[str] = mapped_column(
        String(10), nullable=False, default="un"
    )
    possui_itens: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    itens: Mapped[list["FichaProdutoItem"]] = relationship(
        "FichaProdutoItem",
        foreign_keys="FichaProdutoItem.ficha_produto_id",
        back_populates="ficha",
        cascade="all, delete-orphan",
    )


class FichaProdutoItem(Base):
    """Item de BOM: material bruto OU sub-produto (ficha filho).

    Restrição: exatamente um de material_id ou componente_filho_id deve ser
    preenchido — nunca ambos, nunca nenhum.
    """

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

    # Folha da BOM: material bruto do bd_MATERIAIS
    material_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("bd_MATERIAIS.id"), nullable=True
    )
    # Nó filho: outra ficha de produto (BOM aninhado)
    componente_filho_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("fichas_produto.id"), nullable=True
    )

    quantidade: Mapped[Decimal] = mapped_column(DECIMAL(12, 6), nullable=False)
    # Snapshot do custo no momento da adição
    custo_unitario_gravado: Mapped[Decimal] = mapped_column(
        DECIMAL(12, 4), nullable=False
    )
    observacao: Mapped[str | None] = mapped_column(String(255), nullable=True)

    ficha: Mapped["FichaProduto"] = relationship(
        "FichaProduto",
        foreign_keys=[ficha_produto_id],
        back_populates="itens",
    )
    componente_filho: Mapped["FichaProduto | None"] = relationship(
        "FichaProduto",
        foreign_keys=[componente_filho_id],
    )


# ── Fichas de Serviço ─────────────────────────────────────────────────────────


class FichaServico(Base):
    """Cabeçalho de uma ficha de serviço (SH, vertical, horizontal)."""

    __tablename__ = "fichas_servico"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    tipo_servico: Mapped[str] = mapped_column(String(30), nullable=False)
    # VERTICAL, HORIZONTAL, SH, OUTROS
    unidade_medida: Mapped[str] = mapped_column(String(10), nullable=False)
    producao_diaria: Mapped[Decimal] = mapped_column(
        DECIMAL(12, 2), nullable=False, default=Decimal("1.00")
    )
    possui_recursos: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    recursos: Mapped[list["FichaServicoRecurso"]] = relationship(
        "FichaServicoRecurso", back_populates="ficha", cascade="all, delete-orphan"
    )


class FichaServicoRecurso(Base):
    """Recurso vinculado a uma ficha de serviço.

    Um recurso pode ser: equipe, frota, ferramental avulso ou produto/componente.
    Exatamente um dos FKs de vínculo deve ser preenchido.
    """

    __tablename__ = "fichas_servico_recursos"
    __table_args__ = (
        CheckConstraint(
            # SQLite-compatible: soma de booleanos implícitos via CASE
            """(
                CASE WHEN ficha_equipe_id IS NOT NULL THEN 1 ELSE 0 END +
                CASE WHEN frota_id IS NOT NULL THEN 1 ELSE 0 END +
                CASE WHEN ferramental_id IS NOT NULL THEN 1 ELSE 0 END +
                CASE WHEN ficha_produto_id IS NOT NULL THEN 1 ELSE 0 END
            ) = 1""",
            name="chk_servico_recurso_exclusividade",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ficha_servico_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("fichas_servico.id", ondelete="CASCADE"), nullable=False
    )

    # Exatamente um dos quatro vínculos
    ficha_equipe_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("fichas_equipe.id"), nullable=True
    )
    frota_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("bd_FROTAS.id"), nullable=True
    )
    ferramental_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("bd_FERRAMENTAL.id"), nullable=True
    )
    ficha_produto_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("fichas_produto.id"), nullable=True
    )

    quantidade: Mapped[Decimal] = mapped_column(DECIMAL(12, 4), nullable=False)
    # Snapshot do custo no momento do vínculo
    custo_unitario_gravado: Mapped[Decimal] = mapped_column(
        DECIMAL(12, 4), nullable=False
    )
    observacao: Mapped[str | None] = mapped_column(String(255), nullable=True)

    ficha: Mapped["FichaServico"] = relationship(
        "FichaServico", back_populates="recursos"
    )
