"""Models de Orçamento e CRM (BLOCO 3) — conforme docs/02-schema-banco-dados.md.

Regras: snapshot imutável pós-aprovado; versionamento via orcamento_origem_id;
desconto sobre o total rateado nas linhas; produtos orçáveis sem serviço.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    DECIMAL,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base

if TYPE_CHECKING:
    from backend.models.extra_models import OrcamentoSegmento


class Cliente(Base):
    """3.1 clientes — contratantes de obras viárias."""

    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    tipo: Mapped[str | None] = mapped_column(String(20), nullable=True)
    cnpj_cpf: Mapped[str | None] = mapped_column(String(20), nullable=True)
    contato_nome: Mapped[str | None] = mapped_column(String(100), nullable=True)
    contato_email: Mapped[str | None] = mapped_column(String(150), nullable=True)
    contato_telefone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    orcamentos: Mapped[list["Orcamento"]] = relationship(
        "Orcamento", back_populates="cliente_obj"
    )


class Orcamento(Base):
    """3.2 orcamentos — cabeçalho da proposta comercial."""

    __tablename__ = "orcamentos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    numero: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    cliente_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("clientes.id"), nullable=False
    )
    obra: Mapped[str | None] = mapped_column(String(300), nullable=True)
    uf_execucao: Mapped[str] = mapped_column(String(2), nullable=False)
    beneficio_reidi: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    desconto_percentual: Mapped[Decimal] = mapped_column(
        DECIMAL(5, 2), nullable=False, default=Decimal("0")
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="rascunho")
    # rascunho | enviado | aprovado | reprovado | perdida | fechado
    versao: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    orcamento_origem_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("orcamentos.id"), nullable=True
    )
    created_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("usuarios.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    aprovado_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # BLOCO 1.4 — observações internas (obrigatórias ao aprovar; não vão p/ proposta)
    observacoes_internas: Mapped[str | None] = mapped_column(Text, nullable=True)
    # BLOCO 2.4 — orçamentista responsável
    orcamentista_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("usuarios_orcamentistas.id"), nullable=True
    )
    # BLOCO 2.1/2.3 — textos parametrizáveis da proposta
    validade_proposta: Mapped[str | None] = mapped_column(String(50), nullable=True)
    data_limite: Mapped[date | None] = mapped_column(Date, nullable=True)
    prazo_entrega: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tipo_frete: Mapped[str | None] = mapped_column(String(30), nullable=True)
    condicoes_pagamento: Mapped[str | None] = mapped_column(Text, nullable=True)
    texto_livre_proposta: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Totais de leitura rápida (preenchidos pelo /calcular)
    total_custo_direto: Mapped[Decimal] = mapped_column(
        DECIMAL(14, 4), nullable=False, default=Decimal("0")
    )
    total_proposta: Mapped[Decimal] = mapped_column(
        DECIMAL(14, 4), nullable=False, default=Decimal("0")
    )
    margem_liquida_real: Mapped[Decimal] = mapped_column(
        DECIMAL(8, 6), nullable=False, default=Decimal("0")
    )

    cliente_obj: Mapped["Cliente"] = relationship(
        "Cliente", back_populates="orcamentos"
    )
    itens: Mapped[list["OrcamentoItem"]] = relationship(
        "OrcamentoItem", back_populates="orcamento", cascade="all, delete-orphan"
    )
    segmentos: Mapped[list["OrcamentoSegmento"]] = relationship(
        "OrcamentoSegmento",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class OrcamentoItem(Base):
    """3.3 orcamento_itens — linha de proposta (snapshot fiscal ao calcular).

    Restrições:
      - bloco in ('servicos','produtos','operacional','excepcionais')
      - no máximo um de ficha_servico_id / ficha_produto_id
    """

    __tablename__ = "orcamento_itens"
    __table_args__ = (
        CheckConstraint(
            "bloco IN ('servicos', 'produtos', 'operacional', 'excepcionais')",
            name="chk_orcitem_bloco",
        ),
        CheckConstraint(
            "(CASE WHEN ficha_servico_id IS NOT NULL THEN 1 ELSE 0 END + "
            " CASE WHEN ficha_produto_id IS NOT NULL THEN 1 ELSE 0 END) <= 1",
            name="chk_orcitem_ficha_exclusiva",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    orcamento_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orcamentos.id", ondelete="CASCADE"), nullable=False
    )
    bloco: Mapped[str] = mapped_column(String(30), nullable=False)
    ficha_servico_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("fichas_servico.id"), nullable=True
    )
    ficha_produto_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("fichas_produto.id"), nullable=True
    )
    # BLOCO 1.5 — produto do orçamento referencia o cadastro `produtos` (não a ficha)
    produto_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("produtos.id"), nullable=True
    )
    tipo_origem: Mapped[str] = mapped_column(String(20), nullable=False)
    # servico | produto | operacional | manual
    descricao: Mapped[str] = mapped_column(String(300), nullable=False)
    # BLOCO 2.3 — descrição alternativa exibida ao cliente na proposta
    descricao_cliente: Mapped[str | None] = mapped_column(String(300), nullable=True)
    unidade: Mapped[str] = mapped_column(String(10), nullable=False)
    quantidade: Mapped[Decimal] = mapped_column(DECIMAL(12, 4), nullable=False)
    mod_fat: Mapped[str] = mapped_column(String(20), nullable=False)
    # BDI-MO | BDI-MAT+MO | BDI+ICMS | FAT DIR SIMP | - (não faturável)
    margem_lucro: Mapped[Decimal] = mapped_column(
        DECIMAL(5, 2), nullable=False, default=Decimal("0")
    )  # percentual (10 = 10%)
    custo_direto_unitario: Mapped[Decimal] = mapped_column(
        DECIMAL(12, 4), nullable=False, default=Decimal("0")
    )
    bdi_aplicado: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 6), nullable=False, default=Decimal("0")
    )
    preco_venda_unitario: Mapped[Decimal] = mapped_column(
        DECIMAL(12, 4), nullable=False, default=Decimal("0")
    )
    # BLOCO 1.1 — preço unitário APÓS o rateio do desconto
    preco_venda_unitario_final: Mapped[Decimal] = mapped_column(
        DECIMAL(12, 4), nullable=False, default=Decimal("0")
    )
    preco_venda_total: Mapped[Decimal] = mapped_column(
        DECIMAL(14, 4), nullable=False, default=Decimal("0")
    )
    lucro_absoluto: Mapped[Decimal] = mapped_column(
        DECIMAL(12, 4), nullable=False, default=Decimal("0")
    )
    peso_rateio: Mapped[Decimal] = mapped_column(
        DECIMAL(8, 6), nullable=False, default=Decimal("0")
    )
    desconto_rateado: Mapped[Decimal] = mapped_column(
        DECIMAL(12, 4), nullable=False, default=Decimal("0")
    )
    flag_aprovacao: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    orcamento: Mapped["Orcamento"] = relationship("Orcamento", back_populates="itens")
