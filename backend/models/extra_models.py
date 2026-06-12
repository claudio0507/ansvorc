"""Models adicionais (v2): histórico de descontos, orçamentistas, config do sistema."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DECIMAL, Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class HistoricoDesconto(Base):
    """BLOCO 1.3 — registro do desconto concedido a cada versão do orçamento."""

    __tablename__ = "historico_descontos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    orcamento_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orcamentos.id", ondelete="CASCADE"), nullable=False
    )
    versao: Mapped[int] = mapped_column(Integer, nullable=False)
    desconto_percentual: Mapped[Decimal] = mapped_column(DECIMAL(5, 2), nullable=False)
    subtotal_faturavel: Mapped[Decimal] = mapped_column(DECIMAL(14, 4), nullable=False)
    desconto_total: Mapped[Decimal] = mapped_column(DECIMAL(14, 4), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )


class UsuarioOrcamentista(Base):
    """BLOCO 2.4 — responsáveis pela elaboração de propostas (exibidos na proposta)."""

    __tablename__ = "usuarios_orcamentistas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome_completo: Mapped[str] = mapped_column(String(200), nullable=False)
    funcao: Mapped[str | None] = mapped_column(String(100), nullable=True)
    email: Mapped[str | None] = mapped_column(String(150), nullable=True)
    telefone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class ConfigSistema(Base):
    """BLOCO 5.4 / 2.2 — configurações globais (nome da empresa, caminho do logo)."""

    __tablename__ = "config_sistema"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome_empresa: Mapped[str] = mapped_column(
        String(200), nullable=False, default="ALTA NOROESTE"
    )
    logo_path: Mapped[str | None] = mapped_column(String(300), nullable=True)
    diretor_nome: Mapped[str | None] = mapped_column(String(200), nullable=True)
    diretor_funcao: Mapped[str | None] = mapped_column(String(100), nullable=True)
    diretor_telefone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    diretor_email: Mapped[str | None] = mapped_column(String(150), nullable=True)


class OrcamentoSegmento(Base):
    """BLOCO A — segmentos (multi) classificando o orçamento. Só etiqueta."""

    __tablename__ = "orcamento_segmentos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    orcamento_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orcamentos.id", ondelete="CASCADE"), nullable=False
    )
    seguimento: Mapped[str] = mapped_column(String(50), nullable=False)

    __table_args__ = (
        UniqueConstraint("orcamento_id", "seguimento", name="uq_orc_segmento"),
    )
