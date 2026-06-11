"""Schemas: orçamentistas, config do sistema (nome empresa / logo)."""

from pydantic import BaseModel, ConfigDict, field_validator

from backend.schemas.validators import normalizar_texto


class OrcamentistaBase(BaseModel):
    nome_completo: str
    funcao: str | None = None
    email: str | None = None
    telefone: str | None = None
    ativo: bool = True

    _norm_nome = field_validator("nome_completo")(normalizar_texto)


class OrcamentistaCreate(OrcamentistaBase):
    pass


class OrcamentistaUpdate(BaseModel):
    nome_completo: str | None = None
    funcao: str | None = None
    email: str | None = None
    telefone: str | None = None
    ativo: bool | None = None

    _norm_nome = field_validator("nome_completo")(normalizar_texto)


class OrcamentistaRead(OrcamentistaBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class ConfigSistemaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome_empresa: str
    logo_path: str | None


class ConfigSistemaUpdate(BaseModel):
    nome_empresa: str | None = None
