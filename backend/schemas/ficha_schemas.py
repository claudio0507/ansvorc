"""Schemas Pydantic das Fichas Técnicas — alinhados a docs/02 + docs/03.

Custos (custo_mo, custo_epi, refeicao, hospedagem, custo_dia_linha, custo_total_linha,
custo_dia_total, custo_unitario) são CALCULADOS no backend via lookups — nunca enviados
pelo cliente nos Create.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from backend.schemas.validators import (
    normalizar_codigo,
    normalizar_seguimento,
    normalizar_texto,
)

# ── Ficha de Equipe ──────────────────────────────────────────────────────────


class FichaEquipeItemCreate(BaseModel):
    rh_id: int
    quantidade: int  # pessoas — inteiro
    epi_id: int | None = None

    @field_validator("quantidade")
    @classmethod
    def quantidade_positiva(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("quantidade deve ser inteiro positivo")
        return v


class FichaEquipeItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ficha_equipe_id: int
    rh_id: int
    quantidade: int
    custo_mo: Decimal
    epi_id: int | None
    custo_epi: Decimal
    refeicao: Decimal
    hospedagem: Decimal
    custo_dia_linha: Decimal


class FichaEquipeCreate(BaseModel):
    codigo: str
    seguimento: str

    _norm_codigo = field_validator("codigo")(normalizar_codigo)
    _norm_seg = field_validator("seguimento")(normalizar_seguimento)


class FichaEquipeUpdate(BaseModel):
    seguimento: str | None = None
    ativo: bool | None = None

    _norm_seg = field_validator("seguimento")(normalizar_seguimento)


class FichaEquipeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    codigo: str
    seguimento: str
    custo_dia_total: Decimal
    created_at: datetime | None = None
    ativo: bool
    itens: list[FichaEquipeItemRead] = []


# ── Ficha de Produto (BOM) ───────────────────────────────────────────────────


class FichaProdutoItemCreate(BaseModel):
    material_id: int | None = None
    componente_filho_id: int | None = None
    quantidade: Decimal

    @model_validator(mode="after")
    def valida_bom_exclusividade(self) -> "FichaProdutoItemCreate":
        filled = sum(
            [self.material_id is not None, self.componente_filho_id is not None]
        )
        if filled != 1:
            raise ValueError(
                "Exatamente um de material_id ou componente_filho_id deve ser "
                "informado — nunca ambos, nunca nenhum"
            )
        return self


class FichaProdutoItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ficha_produto_id: int
    material_id: int | None
    componente_filho_id: int | None
    quantidade: Decimal
    unidade: str
    custo_unitario: Decimal
    custo_total_linha: Decimal


class FichaProdutoCreate(BaseModel):
    codigo: str
    nome: str
    unidade: str

    _norm_codigo = field_validator("codigo")(normalizar_codigo)
    _norm_nome = field_validator("nome")(normalizar_texto)


class FichaProdutoUpdate(BaseModel):
    nome: str | None = None
    unidade: str | None = None
    ativo: bool | None = None

    _norm_nome = field_validator("nome")(normalizar_texto)


class FichaProdutoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    codigo: str
    nome: str
    unidade: str
    custo_total: Decimal
    possui_ficha: bool
    created_at: datetime | None = None
    ativo: bool
    itens: list[FichaProdutoItemRead] = []


# ── Ficha de Serviço ─────────────────────────────────────────────────────────


class FichaServicoRecursoCreate(BaseModel):
    """Uma linha vincula equipe + frota + ferramental SIMULTANEAMENTE (+ produto opc)."""

    ficha_equipe_id: int
    frota_id: int
    ferramental_id: int
    ficha_produto_id: int | None = None


class FichaServicoRecursoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ficha_servico_id: int
    ficha_equipe_id: int
    frota_id: int
    ferramental_id: int
    ficha_produto_id: int | None


class FichaServicoCreate(BaseModel):
    codigo: str
    nome: str
    seguimento: str
    produtividade_dia: Decimal
    unidade: str

    _norm_codigo = field_validator("codigo")(normalizar_codigo)
    _norm_nome = field_validator("nome")(normalizar_texto)
    _norm_seg = field_validator("seguimento")(normalizar_seguimento)

    @field_validator("produtividade_dia")
    @classmethod
    def prod_positiva(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("produtividade_dia deve ser maior que zero")
        return v


class FichaServicoUpdate(BaseModel):
    nome: str | None = None
    seguimento: str | None = None
    produtividade_dia: Decimal | None = None
    unidade: str | None = None
    ativo: bool | None = None

    _norm_nome = field_validator("nome")(normalizar_texto)
    _norm_seg = field_validator("seguimento")(normalizar_seguimento)


class FichaServicoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    codigo: str
    nome: str
    seguimento: str
    produtividade_dia: Decimal
    unidade: str
    possui_ficha: bool
    custo_unitario: Decimal
    created_at: datetime | None = None
    ativo: bool
    recursos: list[FichaServicoRecursoRead] = []
