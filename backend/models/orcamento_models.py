from decimal import Decimal

from sqlalchemy import (
    DECIMAL,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Cliente(Base):
    """Cadastro de clientes (contratantes de obras viárias)."""

    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    razao_social: Mapped[str] = mapped_column(String(200), nullable=False)
    cnpj: Mapped[str | None] = mapped_column(String(18), unique=True, nullable=True)
    contato_nome: Mapped[str | None] = mapped_column(String(150), nullable=True)
    contato_email: Mapped[str | None] = mapped_column(String(150), nullable=True)
    contato_telefone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    uf_sede: Mapped[str | None] = mapped_column(String(2), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    criado_em: Mapped[DateTime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    orcamentos: Mapped[list["Orcamento"]] = relationship(
        "Orcamento", back_populates="cliente_obj"
    )


class Orcamento(Base):
    """Cabeçalho de uma proposta comercial de obra viária."""

    __tablename__ = "orcamentos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    numero_proposta: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    versao: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    cliente_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("clientes.id"), nullable=False
    )
    descricao_obra: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Parâmetros fiscais globais do orçamento
    uf_execucao: Mapped[str] = mapped_column(String(2), nullable=False, default="PR")
    # PR | SP | ... (determina alíquota ISSQN)
    beneficio_reidi: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Status do ciclo de vida
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="rascunho")
    # rascunho | aprovado | rejeitado | enviado

    # Totais calculados (atualizados pelo endpoint /calcular, leitura rápida)
    total_custo_direto: Mapped[Decimal] = mapped_column(
        DECIMAL(14, 4), nullable=False, default=Decimal("0")
    )
    total_proposta: Mapped[Decimal] = mapped_column(
        DECIMAL(14, 4), nullable=False, default=Decimal("0")
    )
    margem_liquida_real: Mapped[Decimal] = mapped_column(
        DECIMAL(8, 6), nullable=False, default=Decimal("0")
    )

    criado_em: Mapped[DateTime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    atualizado_em: Mapped[DateTime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    cliente_obj: Mapped["Cliente"] = relationship("Cliente", back_populates="orcamentos")
    itens: Mapped[list["OrcamentoItem"]] = relationship(
        "OrcamentoItem", back_populates="orcamento", cascade="all, delete-orphan"
    )


class OrcamentoItem(Base):
    """Item de um orçamento — snapshot fiscal do custo no momento do cálculo.

    Restrições:
      - bloco in ('servicos', 'produtos', 'operacional', 'excepcionais')
      - ficha_servico_id XOR ficha_produto_id (nunca ambos simultaneamente)
      - itens de bloco 'operacional'/'excepcionais' NUNCA têm ficha_servico_id
        nem ficha_produto_id (são custos avulsos)
    """

    __tablename__ = "orcamento_itens"
    __table_args__ = (
        CheckConstraint(
            "bloco IN ('servicos', 'produtos', 'operacional', 'excepcionais')",
            name="chk_orcitem_bloco",
        ),
        CheckConstraint(
            # No máximo um dos dois tipos de ficha
            "(CASE WHEN ficha_servico_id IS NOT NULL THEN 1 ELSE 0 END + "
            " CASE WHEN ficha_produto_id IS NOT NULL THEN 1 ELSE 0 END) <= 1",
            name="chk_orcitem_ficha_exclusiva",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    orcamento_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orcamentos.id", ondelete="CASCADE"), nullable=False
    )

    # Bloco de pertencimento no orçamento
    bloco: Mapped[str] = mapped_column(String(20), nullable=False)
    # servicos | produtos | operacional | excepcionais

    # Referência histórica à ficha técnica utilizada (nullable: item manual)
    ficha_servico_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("fichas_servico.id"), nullable=True
    )
    ficha_produto_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("fichas_produto.id"), nullable=True
    )

    # Descrição e unidade (gravados para auditoria — ficha pode mudar depois)
    descricao: Mapped[str] = mapped_column(String(255), nullable=False)
    unidade_medida: Mapped[str] = mapped_column(String(10), nullable=False)
    quantidade: Mapped[Decimal] = mapped_column(DECIMAL(12, 4), nullable=False)

    # Parâmetros de precificação da linha
    mod_fat: Mapped[str] = mapped_column(String(20), nullable=False, default="BDI-MAT+MO")
    # BDI-MO | BDI-MAT+MO | BDI+ICMS | FAT DIR SIMP | - (não faturável)
    margem_percentual: Mapped[Decimal] = mapped_column(
        DECIMAL(6, 4), nullable=False, default=Decimal("0.1000")
    )
    # fração decimal (0.10 = 10%)

    # ── Valores calculados / snapshot ────────────────────────────────────────
    custo_direto_unitario: Mapped[Decimal] = mapped_column(
        DECIMAL(12, 4), nullable=False, default=Decimal("0")
    )
    bdi_taxa: Mapped[Decimal] = mapped_column(
        DECIMAL(8, 6), nullable=False, default=Decimal("0")
    )
    preco_venda_unitario: Mapped[Decimal] = mapped_column(
        DECIMAL(12, 4), nullable=False, default=Decimal("0")
    )
    preco_venda_total: Mapped[Decimal] = mapped_column(
        DECIMAL(14, 4), nullable=False, default=Decimal("0")
    )
    peso_rateio: Mapped[Decimal] = mapped_column(
        DECIMAL(8, 6), nullable=False, default=Decimal("0")
    )
    # participação % no Fator K
    rateio_absorvido: Mapped[Decimal] = mapped_column(
        DECIMAL(12, 4), nullable=False, default=Decimal("0")
    )
    preco_final_unitario: Mapped[Decimal] = mapped_column(
        DECIMAL(12, 4), nullable=False, default=Decimal("0")
    )
    lucro_absoluto: Mapped[Decimal] = mapped_column(
        DECIMAL(12, 4), nullable=False, default=Decimal("0")
    )

    # Flag: item adicionado manualmente (fora do catálogo de fichas)
    item_excepcional: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    demanda_aprovacao: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    orcamento: Mapped["Orcamento"] = relationship("Orcamento", back_populates="itens")
