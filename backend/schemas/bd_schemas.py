from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator


# ── bd_BDI ──────────────────────────────────────────────────────────────────

class BdBDIBase(BaseModel):
    modalidade: str
    adm_percentual: Decimal = Decimal("0.1300")
    custo_financeiro_percentual: Decimal = Decimal("0.0150")
    pis_cofins_percentual: Decimal = Decimal("0.0365")
    issqn_pr_percentual: Decimal = Decimal("0.0350")
    issqn_sp_percentual: Decimal = Decimal("0.0500")
    icms_percentual: Decimal = Decimal("0.0000")
    ativo: bool = True
    descricao: str | None = None


class BdBDICreate(BdBDIBase):
    pass


class BdBDIUpdate(BaseModel):
    modalidade: str | None = None
    adm_percentual: Decimal | None = None
    custo_financeiro_percentual: Decimal | None = None
    pis_cofins_percentual: Decimal | None = None
    issqn_pr_percentual: Decimal | None = None
    issqn_sp_percentual: Decimal | None = None
    icms_percentual: Decimal | None = None
    ativo: bool | None = None
    descricao: str | None = None


class BdBDIRead(BdBDIBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ── bd_RH ───────────────────────────────────────────────────────────────────

class BdRHBase(BaseModel):
    codigo: str
    cargo: str
    categoria: str
    salario_base: Decimal
    encargos_percentual: Decimal = Decimal("0.7200")
    horas_mes: Decimal = Decimal("220.00")
    unidade_medida: str = "h"
    ativo: bool = True

    @field_validator("salario_base", "encargos_percentual", "horas_mes")
    @classmethod
    def must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("deve ser positivo")
        return v


class BdRHCreate(BdRHBase):
    pass


class BdRHUpdate(BaseModel):
    cargo: str | None = None
    categoria: str | None = None
    salario_base: Decimal | None = None
    encargos_percentual: Decimal | None = None
    horas_mes: Decimal | None = None
    unidade_medida: str | None = None
    ativo: bool | None = None


class BdRHRead(BdRHBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ── bd_EPI ──────────────────────────────────────────────────────────────────

class BdEPIBase(BaseModel):
    codigo: str
    descricao: str
    unidade_medida: str
    custo_unitario: Decimal
    vida_util_dias: int | None = None
    ativo: bool = True


class BdEPICreate(BdEPIBase):
    pass


class BdEPIUpdate(BaseModel):
    descricao: str | None = None
    unidade_medida: str | None = None
    custo_unitario: Decimal | None = None
    vida_util_dias: int | None = None
    ativo: bool | None = None


class BdEPIRead(BdEPIBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ── bd_FERRAMENTAL ──────────────────────────────────────────────────────────

class BdFerramentalBase(BaseModel):
    codigo: str
    descricao: str
    unidade_medida: str
    custo_unitario: Decimal
    vida_util_dias: int | None = None
    ativo: bool = True


class BdFerramentalCreate(BdFerramentalBase):
    pass


class BdFerramentalUpdate(BaseModel):
    descricao: str | None = None
    unidade_medida: str | None = None
    custo_unitario: Decimal | None = None
    vida_util_dias: int | None = None
    ativo: bool | None = None


class BdFerramentalRead(BdFerramentalBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ── bd_FROTAS ───────────────────────────────────────────────────────────────

class BdFrotasBase(BaseModel):
    codigo: str
    descricao: str
    tipo: str
    custo_diaria: Decimal
    custo_km: Decimal | None = None
    unidade_medida: str = "dia"
    ativo: bool = True


class BdFrotasCreate(BdFrotasBase):
    pass


class BdFrotasUpdate(BaseModel):
    descricao: str | None = None
    tipo: str | None = None
    custo_diaria: Decimal | None = None
    custo_km: Decimal | None = None
    unidade_medida: str | None = None
    ativo: bool | None = None


class BdFrotasRead(BdFrotasBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ── bd_MATERIAIS ─────────────────────────────────────────────────────────────

class BdMateriaisBase(BaseModel):
    codigo: str
    descricao: str
    categoria: str
    unidade_medida: str
    custo_unitario: Decimal
    fornecedor: str | None = None
    icms_incide: bool = True
    ativo: bool = True


class BdMateriaisCreate(BdMateriaisBase):
    pass


class BdMateriaisUpdate(BaseModel):
    descricao: str | None = None
    categoria: str | None = None
    unidade_medida: str | None = None
    custo_unitario: Decimal | None = None
    fornecedor: str | None = None
    icms_incide: bool | None = None
    ativo: bool | None = None


class BdMateriaisRead(BdMateriaisBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ── bd_ESTRUTURA_OPERACIONAL ─────────────────────────────────────────────────

class BdEstruturaBase(BaseModel):
    codigo: str
    descricao: str
    tipo: str
    unidade_medida: str
    custo_unitario: Decimal
    ativo: bool = True


class BdEstruturaCreate(BdEstruturaBase):
    pass


class BdEstruturaUpdate(BaseModel):
    descricao: str | None = None
    tipo: str | None = None
    unidade_medida: str | None = None
    custo_unitario: Decimal | None = None
    ativo: bool | None = None


class BdEstruturaRead(BdEstruturaBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ── bd_DESPESAS ──────────────────────────────────────────────────────────────

class BdDespesasBase(BaseModel):
    codigo: str
    descricao: str
    tipo: str
    percentual: Decimal | None = None
    valor_fixo: Decimal | None = None
    ativo: bool = True


class BdDespesasCreate(BdDespesasBase):
    pass


class BdDespesasUpdate(BaseModel):
    descricao: str | None = None
    tipo: str | None = None
    percentual: Decimal | None = None
    valor_fixo: Decimal | None = None
    ativo: bool | None = None


class BdDespesasRead(BdDespesasBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
