"""Schemas das tabelas de parametrização (unidades, seguimentos, tipos estrutura)."""

from pydantic import BaseModel, ConfigDict, field_validator

from backend.schemas.validators import normalizar_seguimento, normalizar_texto


# ── Unidades de medida ───────────────────────────────────────────────────────
class UnidadeMedidaBase(BaseModel):
    sigla: str
    nome: str
    ativo: bool = True

    _norm_nome = field_validator("nome")(normalizar_texto)


class UnidadeMedidaCreate(UnidadeMedidaBase):
    pass


class UnidadeMedidaUpdate(BaseModel):
    sigla: str | None = None
    nome: str | None = None
    ativo: bool | None = None


class UnidadeMedidaRead(UnidadeMedidaBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ── Seguimentos (nome em MAIÚSCULAS: EPS, HORIZONTAL…) ───────────────────────
class SeguimentoCreate(BaseModel):
    nome: str
    ativo: bool = True

    _norm_nome = field_validator("nome")(normalizar_seguimento)


class TipoEstruturaCreate(BaseModel):
    nome: str
    ativo: bool = True

    _norm_nome = field_validator("nome")(normalizar_texto)


class ParametroUpdate(BaseModel):
    nome: str | None = None
    ativo: bool | None = None


class ParametroRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome: str
    ativo: bool
