"""Schemas: orçamentistas, config do sistema (nome empresa / logo)."""

from decimal import Decimal

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
    diretor_nome: str | None = None
    diretor_funcao: str | None = None
    diretor_telefone: str | None = None
    diretor_email: str | None = None
    diretor_cpf: str | None = None
    banco: str | None = None
    agencia: str | None = None
    conta_corrente: str | None = None
    cnpj: str | None = None
    contato_comercial_nome: str | None = None
    contato_comercial_funcao: str | None = None
    contato_comercial_fone: str | None = None
    contato_comercial_email: str | None = None
    clausula_tributaria_padrao: str | None = None
    reajustamento_padrao: str | None = None
    garantia_retencao_padrao_pct: Decimal | None = None
    garantia_devolucao_padrao_dias: int | None = None
    declaracoes_padrao: str | None = None


class ConfigSistemaUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nome_empresa: str | None = None
    diretor_nome: str | None = None
    diretor_funcao: str | None = None
    diretor_telefone: str | None = None
    diretor_email: str | None = None
    diretor_cpf: str | None = None
    banco: str | None = None
    agencia: str | None = None
    conta_corrente: str | None = None
    cnpj: str | None = None
    contato_comercial_nome: str | None = None
    contato_comercial_funcao: str | None = None
    contato_comercial_fone: str | None = None
    contato_comercial_email: str | None = None
    clausula_tributaria_padrao: str | None = None
    reajustamento_padrao: str | None = None
    garantia_retencao_padrao_pct: Decimal | None = None
    garantia_devolucao_padrao_dias: int | None = None
    declaracoes_padrao: str | None = None
