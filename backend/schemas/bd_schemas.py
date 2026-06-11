"""Schemas Pydantic dos Bancos de Dados — alinhados a docs/02.

Campos monetários sempre Decimal. Texto/código/seguimento normalizados.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator

from backend.schemas.validators import (
    normalizar_seguimento,
    normalizar_texto,
    normalizar_uf,
)

# ── bd_BDI ──────────────────────────────────────────────────────────────────


class BdBDIBase(BaseModel):
    modalidade: str
    uf: str
    icms: Decimal = Decimal("0")
    cofins: Decimal = Decimal("0")
    pis: Decimal = Decimal("0")
    issqn: Decimal = Decimal("0")
    custo_financeiro: Decimal = Decimal("0.0150")
    irpj: Decimal = Decimal("0")
    csll: Decimal = Decimal("0")
    despesas_adm: Decimal = Decimal("0.1300")
    ativo: bool = True

    _norm_uf = field_validator("uf")(normalizar_uf)


class BdBDICreate(BdBDIBase):
    pass


class BdBDIUpdate(BaseModel):
    modalidade: str | None = None
    uf: str | None = None
    icms: Decimal | None = None
    cofins: Decimal | None = None
    pis: Decimal | None = None
    issqn: Decimal | None = None
    custo_financeiro: Decimal | None = None
    irpj: Decimal | None = None
    csll: Decimal | None = None
    despesas_adm: Decimal | None = None
    ativo: bool | None = None

    _norm_uf = field_validator("uf")(normalizar_uf)


class BdBDIRead(BdBDIBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    atualizado_em: datetime | None = None


# ── bd_RH ───────────────────────────────────────────────────────────────────


class BdRHBase(BaseModel):
    cargo: str
    custo_diario: Decimal
    ativo: bool = True

    _norm_cargo = field_validator("cargo")(normalizar_texto)

    @field_validator("custo_diario")
    @classmethod
    def custo_positivo(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("custo_diario não pode ser negativo")
        return v


class BdRHCreate(BdRHBase):
    pass


class BdRHUpdate(BaseModel):
    cargo: str | None = None
    custo_diario: Decimal | None = None
    ativo: bool | None = None

    _norm_cargo = field_validator("cargo")(normalizar_texto)


class BdRHRead(BdRHBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    atualizado_em: datetime | None = None


# ── bd_EPI ──────────────────────────────────────────────────────────────────


class BdEPIBase(BaseModel):
    item: str
    custo_diario: Decimal
    ativo: bool = True

    _norm_item = field_validator("item")(normalizar_texto)


class BdEPICreate(BdEPIBase):
    pass


class BdEPIUpdate(BaseModel):
    item: str | None = None
    custo_diario: Decimal | None = None
    ativo: bool | None = None

    _norm_item = field_validator("item")(normalizar_texto)


class BdEPIRead(BdEPIBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    atualizado_em: datetime | None = None


# ── bd_FERRAMENTAL ──────────────────────────────────────────────────────────


class BdFerramentalBase(BaseModel):
    seguimento: str
    custo_diario: Decimal
    ativo: bool = True

    _norm_seg = field_validator("seguimento")(normalizar_seguimento)


class BdFerramentalCreate(BdFerramentalBase):
    pass


class BdFerramentalUpdate(BaseModel):
    seguimento: str | None = None
    custo_diario: Decimal | None = None
    ativo: bool | None = None

    _norm_seg = field_validator("seguimento")(normalizar_seguimento)


class BdFerramentalRead(BdFerramentalBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    atualizado_em: datetime | None = None


# ── bd_FROTAS ───────────────────────────────────────────────────────────────


class BdFrotasBase(BaseModel):
    seguimento: str
    custo_diario: Decimal
    ativo: bool = True

    _norm_seg = field_validator("seguimento")(normalizar_seguimento)


class BdFrotasCreate(BdFrotasBase):
    pass


class BdFrotasUpdate(BaseModel):
    seguimento: str | None = None
    custo_diario: Decimal | None = None
    ativo: bool | None = None

    _norm_seg = field_validator("seguimento")(normalizar_seguimento)


class BdFrotasRead(BdFrotasBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    atualizado_em: datetime | None = None


# ── bd_MATERIAIS ─────────────────────────────────────────────────────────────


class BdMateriaisBase(BaseModel):
    material: str
    unidade: str
    destinacao: str | None = None
    valor_unitario: Decimal
    ativo: bool = True

    _norm_material = field_validator("material")(normalizar_texto)


class BdMateriaisCreate(BdMateriaisBase):
    pass


class BdMateriaisUpdate(BaseModel):
    material: str | None = None
    unidade: str | None = None
    destinacao: str | None = None
    valor_unitario: Decimal | None = None
    ativo: bool | None = None

    _norm_material = field_validator("material")(normalizar_texto)


class BdMateriaisRead(BdMateriaisBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    atualizado_em: datetime | None = None


# ── bd_ESTRUTURA_OPERACIONAL ─────────────────────────────────────────────────


class BdEstruturaBase(BaseModel):
    item: str
    unidade: str
    tipo: str
    valor_unitario: Decimal
    ativo: bool = True

    _norm_item = field_validator("item")(normalizar_texto)


class BdEstruturaCreate(BdEstruturaBase):
    pass


class BdEstruturaUpdate(BaseModel):
    item: str | None = None
    unidade: str | None = None
    tipo: str | None = None
    valor_unitario: Decimal | None = None
    ativo: bool | None = None

    _norm_item = field_validator("item")(normalizar_texto)


class BdEstruturaRead(BdEstruturaBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    atualizado_em: datetime | None = None


# ── bd_DESPESAS ──────────────────────────────────────────────────────────────


class BdDespesasBase(BaseModel):
    seguimento: str
    epc: Decimal = Decimal("0")
    refeicao: Decimal = Decimal("0")
    hospedagem: Decimal = Decimal("0")
    ativo: bool = True

    _norm_seg = field_validator("seguimento")(normalizar_seguimento)


class BdDespesasCreate(BdDespesasBase):
    pass


class BdDespesasUpdate(BaseModel):
    seguimento: str | None = None
    epc: Decimal | None = None
    refeicao: Decimal | None = None
    hospedagem: Decimal | None = None
    ativo: bool | None = None

    _norm_seg = field_validator("seguimento")(normalizar_seguimento)


class BdDespesasRead(BdDespesasBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    atualizado_em: datetime | None = None
