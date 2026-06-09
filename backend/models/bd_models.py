from decimal import Decimal

from sqlalchemy import DECIMAL, Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class BdBDI(Base):
    """Parâmetros de BDI por modalidade de faturamento."""

    __tablename__ = "bd_BDI"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    modalidade: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    # BDI-MO, BDI-MAT+MO, BDI+ICMS, FAT DIR SIMP
    adm_percentual: Mapped[Decimal] = mapped_column(
        DECIMAL(5, 4), nullable=False, default=Decimal("0.1300")
    )
    custo_financeiro_percentual: Mapped[Decimal] = mapped_column(
        DECIMAL(5, 4), nullable=False, default=Decimal("0.0150")
    )
    pis_cofins_percentual: Mapped[Decimal] = mapped_column(
        DECIMAL(5, 4), nullable=False, default=Decimal("0.0365")
    )
    issqn_pr_percentual: Mapped[Decimal] = mapped_column(
        DECIMAL(5, 4), nullable=False, default=Decimal("0.0350")
    )
    issqn_sp_percentual: Mapped[Decimal] = mapped_column(
        DECIMAL(5, 4), nullable=False, default=Decimal("0.0500")
    )
    icms_percentual: Mapped[Decimal] = mapped_column(
        DECIMAL(5, 4), nullable=False, default=Decimal("0.0000")
    )
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)


class BdRH(Base):
    """Banco de dados de Recursos Humanos — cargos e custos de mão de obra."""

    __tablename__ = "bd_RH"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    cargo: Mapped[str] = mapped_column(String(100), nullable=False)
    categoria: Mapped[str] = mapped_column(String(50), nullable=False)
    # OPERACIONAL, ADMINISTRATIVO, TECNICO
    salario_base: Mapped[Decimal] = mapped_column(DECIMAL(12, 4), nullable=False)
    encargos_percentual: Mapped[Decimal] = mapped_column(
        DECIMAL(5, 4), nullable=False, default=Decimal("0.7200")
    )
    # Custo hora = (salario_base * (1 + encargos)) / horas_mes
    horas_mes: Mapped[Decimal] = mapped_column(
        DECIMAL(6, 2), nullable=False, default=Decimal("220.00")
    )
    unidade_medida: Mapped[str] = mapped_column(String(10), nullable=False, default="h")
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class BdEPI(Base):
    """Equipamentos de Proteção Individual."""

    __tablename__ = "bd_EPI"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    descricao: Mapped[str] = mapped_column(String(255), nullable=False)
    unidade_medida: Mapped[str] = mapped_column(String(10), nullable=False)
    custo_unitario: Mapped[Decimal] = mapped_column(DECIMAL(12, 4), nullable=False)
    vida_util_dias: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # custo_dia = custo_unitario / vida_util_dias quando informado
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class BdFerramental(Base):
    """Ferramentas e pequenos equipamentos."""

    __tablename__ = "bd_FERRAMENTAL"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    descricao: Mapped[str] = mapped_column(String(255), nullable=False)
    unidade_medida: Mapped[str] = mapped_column(String(10), nullable=False)
    custo_unitario: Mapped[Decimal] = mapped_column(DECIMAL(12, 4), nullable=False)
    vida_util_dias: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class BdFrotas(Base):
    """Veículos e equipamentos pesados."""

    __tablename__ = "bd_FROTAS"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    descricao: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo: Mapped[str] = mapped_column(String(50), nullable=False)
    # VEICULO_LEVE, VEICULO_PESADO, EQUIPAMENTO, PRANCHA
    custo_diaria: Mapped[Decimal] = mapped_column(DECIMAL(12, 4), nullable=False)
    custo_km: Mapped[Decimal | None] = mapped_column(DECIMAL(12, 4), nullable=True)
    unidade_medida: Mapped[str] = mapped_column(
        String(10), nullable=False, default="dia"
    )
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class BdMateriais(Base):
    """Materiais e insumos físicos."""

    __tablename__ = "bd_MATERIAIS"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    descricao: Mapped[str] = mapped_column(String(255), nullable=False)
    categoria: Mapped[str] = mapped_column(String(50), nullable=False)
    # PLACA, PELICULA, TINTA, PERFIL, PARAFUSO, OUTROS
    unidade_medida: Mapped[str] = mapped_column(String(10), nullable=False)
    custo_unitario: Mapped[Decimal] = mapped_column(DECIMAL(12, 4), nullable=False)
    fornecedor: Mapped[str | None] = mapped_column(String(150), nullable=True)
    icms_incide: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class BdEstrutura(Base):
    """Custos de estrutura operacional (alojamento, logística, mobilização)."""

    __tablename__ = "bd_ESTRUTURA_OPERACIONAL"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    descricao: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo: Mapped[str] = mapped_column(String(50), nullable=False)
    # ALOJAMENTO, LOGISTICA, MOBILIZACAO, COMUNICACAO, OUTROS
    unidade_medida: Mapped[str] = mapped_column(String(10), nullable=False)
    custo_unitario: Mapped[Decimal] = mapped_column(DECIMAL(12, 4), nullable=False)
    # Itens de estrutura recebem BDI Sombra (não são faturáveis diretamente)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class BdDespesas(Base):
    """Despesas administrativas e financeiras parametrizáveis."""

    __tablename__ = "bd_DESPESAS"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    descricao: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo: Mapped[str] = mapped_column(String(50), nullable=False)
    # ADMINISTRATIVA, FINANCEIRA, SEGURO, OUTROS
    percentual: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 4), nullable=True)
    valor_fixo: Mapped[Decimal | None] = mapped_column(DECIMAL(12, 4), nullable=True)
    # Exatamente um dos dois deve ser preenchido
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
