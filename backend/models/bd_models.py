"""Models dos Bancos de Dados (BLOCO 1) — conforme docs/02-schema-banco-dados.md.

Campos, tipos e nomes seguem EXATAMENTE a especificação. Valores monetários são
sempre DECIMAL (nunca float).
"""

from decimal import Decimal

from sqlalchemy import DECIMAL, Boolean, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class BdBDI(Base):
    """1.1 bd_BDI — Parâmetros tributários por modalidade × UF."""

    __tablename__ = "bd_BDI"
    __table_args__ = (
        UniqueConstraint("modalidade", "uf", name="uq_bdi_modalidade_uf"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    modalidade: Mapped[str] = mapped_column(String(20), nullable=False)
    # BDI-MAT+MO, BDI-MO, BDI+ICMS, FAT DIR SIMP
    uf: Mapped[str] = mapped_column(String(2), nullable=False)  # PR, SP, etc.
    icms: Mapped[Decimal] = mapped_column(
        DECIMAL(5, 4), nullable=False, default=Decimal("0")
    )
    cofins: Mapped[Decimal] = mapped_column(
        DECIMAL(5, 4), nullable=False, default=Decimal("0")
    )
    pis: Mapped[Decimal] = mapped_column(
        DECIMAL(5, 4), nullable=False, default=Decimal("0")
    )
    issqn: Mapped[Decimal] = mapped_column(
        DECIMAL(5, 4), nullable=False, default=Decimal("0")
    )
    custo_financeiro: Mapped[Decimal] = mapped_column(
        DECIMAL(5, 4), nullable=False, default=Decimal("0.0150")
    )
    irpj: Mapped[Decimal] = mapped_column(
        DECIMAL(5, 4), nullable=False, default=Decimal("0")
    )
    csll: Mapped[Decimal] = mapped_column(
        DECIMAL(5, 4), nullable=False, default=Decimal("0")
    )
    despesas_adm: Mapped[Decimal] = mapped_column(
        DECIMAL(5, 4), nullable=False, default=Decimal("0.1300")
    )
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class BdRH(Base):
    """1.2 bd_RH — Cargos e custo diário de mão de obra."""

    __tablename__ = "bd_RH"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cargo: Mapped[str] = mapped_column(String(100), nullable=False)
    custo_diario: Mapped[Decimal] = mapped_column(DECIMAL(10, 4), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class BdEPI(Base):
    """1.3 bd_EPI — Equipamentos de Proteção Individual (custo diário)."""

    __tablename__ = "bd_EPI"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item: Mapped[str] = mapped_column(String(100), nullable=False)
    custo_diario: Mapped[Decimal] = mapped_column(DECIMAL(10, 4), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class BdFerramental(Base):
    """1.4 bd_FERRAMENTAL — Ferramentas por seguimento."""

    __tablename__ = "bd_FERRAMENTAL"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    seguimento: Mapped[str] = mapped_column(String(50), nullable=False)
    # EPS, HORIZONTAL, OBRA CIVIL, VERTICAL
    custo_diario: Mapped[Decimal] = mapped_column(DECIMAL(10, 4), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class BdFrotas(Base):
    """1.5 bd_FROTAS — Veículos e equipamentos por seguimento."""

    __tablename__ = "bd_FROTAS"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    seguimento: Mapped[str] = mapped_column(String(50), nullable=False)
    # APOIO, EPS, HORIZONTAL, VERTICAL
    custo_diario: Mapped[Decimal] = mapped_column(DECIMAL(10, 4), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class BdMateriais(Base):
    """1.6 bd_MATERIAIS — Materiais e insumos físicos."""

    __tablename__ = "bd_MATERIAIS"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    material: Mapped[str] = mapped_column(String(200), nullable=False)
    unidade: Mapped[str] = mapped_column(
        String(10), nullable=False
    )  # m², m, und, L, kg
    destinacao: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # FABRICA, HORIZONTAL
    valor_unitario: Mapped[Decimal] = mapped_column(DECIMAL(12, 4), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class BdEstrutura(Base):
    """1.7 bd_ESTRUTURA_OPERACIONAL — Custos operacionais (BDI Sombra)."""

    __tablename__ = "bd_ESTRUTURA_OPERACIONAL"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item: Mapped[str] = mapped_column(String(150), nullable=False)
    unidade: Mapped[str] = mapped_column(String(10), nullable=False)
    tipo: Mapped[str] = mapped_column(String(50), nullable=False)
    # Base_de_Apoio, Moradia, Administrativo, Operacional, Logística
    valor_unitario: Mapped[Decimal] = mapped_column(DECIMAL(12, 4), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class BdDespesas(Base):
    """1.8 bd_DESPESAS — EPC, refeição e hospedagem por seguimento."""

    __tablename__ = "bd_DESPESAS"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    seguimento: Mapped[str] = mapped_column(String(50), nullable=False)
    # EPS, HORIZONTAL, VERTICAL, APOIO
    epc: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 4), nullable=False, default=Decimal("0")
    )
    refeicao: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 4), nullable=False, default=Decimal("0")
    )
    hospedagem: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 4), nullable=False, default=Decimal("0")
    )
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
