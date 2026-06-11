"""Models de Produtos, Componentes e vínculo com fichas técnicas (BLOCO 4).

componentes / produtos: itens cadastráveis com dados industriais + flag de ficha técnica.
item_fichas: tabela associativa (produto OU componente) ↔ (ficha serviço/produto/equipe).
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
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class _ItemIndustrialMixin:
    """Campos comuns a componentes e produtos."""

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    caracteristicas: Mapped[str | None] = mapped_column(Text, nullable=True)
    dimensoes: Mapped[str | None] = mapped_column(String(100), nullable=True)
    volume_m3: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 4), nullable=True)
    peso_kg: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 4), nullable=True)
    deposito_produtivo: Mapped[str | None] = mapped_column(String(100), nullable=True)
    setor: Mapped[str | None] = mapped_column(String(100), nullable=True)
    industrializado_terceiros: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    unidade_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("unidades_medida.id"), nullable=True
    )
    possui_ficha_tecnica: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class Componente(Base, _ItemIndustrialMixin):
    __tablename__ = "componentes"


class Produto(Base, _ItemIndustrialMixin):
    __tablename__ = "produtos"


class ItemFicha(Base):
    """Vínculo item (produto/componente) ↔ ficha técnica."""

    __tablename__ = "item_fichas"
    __table_args__ = (
        CheckConstraint(
            "(CASE WHEN componente_id IS NOT NULL THEN 1 ELSE 0 END + "
            " CASE WHEN produto_id IS NOT NULL THEN 1 ELSE 0 END) >= 1",
            name="chk_itemficha_tem_item",
        ),
        CheckConstraint(
            "(CASE WHEN ficha_servico_id IS NOT NULL THEN 1 ELSE 0 END + "
            " CASE WHEN ficha_produto_id IS NOT NULL THEN 1 ELSE 0 END + "
            " CASE WHEN ficha_equipe_id IS NOT NULL THEN 1 ELSE 0 END) >= 1",
            name="chk_itemficha_tem_ficha",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    componente_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("componentes.id", ondelete="CASCADE"), nullable=True
    )
    produto_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("produtos.id", ondelete="CASCADE"), nullable=True
    )
    ficha_servico_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("fichas_servico.id"), nullable=True
    )
    ficha_produto_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("fichas_produto.id"), nullable=True
    )
    ficha_equipe_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("fichas_equipe.id"), nullable=True
    )
