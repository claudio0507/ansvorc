"""Models de parametrização (BLOCO 3.3/3.4 do prompt-melhorias).

- unidades_medida: catálogo de unidades (select em todos os cadastros).
- parametros_seguimentos / parametros_tipos_estrutura: parâmetros editáveis que
  alimentam os selects de seguimento e tipo de estrutura.
"""

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class UnidadeMedida(Base):
    __tablename__ = "unidades_medida"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sigla: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(50), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class ParametroSeguimento(Base):
    __tablename__ = "parametros_seguimentos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class ParametroTipoEstrutura(Base):
    __tablename__ = "parametros_tipos_estrutura"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
