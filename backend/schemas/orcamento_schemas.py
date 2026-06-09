from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

# ── Clientes ──────────────────────────────────────────────────────────────────


class ClienteCreate(BaseModel):
    razao_social: str
    cnpj: str | None = None
    contato_nome: str | None = None
    contato_email: str | None = None
    contato_telefone: str | None = None
    uf_sede: str | None = None
    ativo: bool = True


class ClienteUpdate(BaseModel):
    razao_social: str | None = None
    cnpj: str | None = None
    contato_nome: str | None = None
    contato_email: str | None = None
    contato_telefone: str | None = None
    uf_sede: str | None = None
    ativo: bool | None = None


class ClienteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    razao_social: str
    cnpj: str | None
    contato_nome: str | None
    contato_email: str | None
    contato_telefone: str | None
    uf_sede: str | None
    ativo: bool


# ── Orçamentos ────────────────────────────────────────────────────────────────

_UF_VALIDAS = {
    "PR",
    "SP",
    "SC",
    "RS",
    "MG",
    "RJ",
    "ES",
    "GO",
    "DF",
    "MT",
    "MS",
    "BA",
    "PE",
    "CE",
    "AM",
    "PA",
    "RO",
    "RR",
    "AP",
    "TO",
    "MA",
    "PI",
    "RN",
    "PB",
    "AL",
    "SE",
    "AC",
}

_STATUS_VALIDOS = {"rascunho", "enviado", "aprovado", "rejeitado"}

_MOD_FAT_VALIDAS = {"BDI-MO", "BDI-MAT+MO", "BDI+ICMS", "FAT DIR SIMP", "-"}

_BLOCOS_VALIDOS = {"servicos", "produtos", "operacional", "excepcionais"}


class OrcamentoCreate(BaseModel):
    numero_proposta: str
    cliente_id: int
    descricao_obra: str | None = None
    uf_execucao: str = "PR"
    beneficio_reidi: bool = False

    @field_validator("uf_execucao")
    @classmethod
    def valida_uf(cls, v: str) -> str:
        v = v.upper()
        if v not in _UF_VALIDAS:
            raise ValueError(f"UF inválida: {v}")
        return v


class OrcamentoUpdate(BaseModel):
    descricao_obra: str | None = None
    uf_execucao: str | None = None
    beneficio_reidi: bool | None = None
    status: str | None = None

    @field_validator("uf_execucao")
    @classmethod
    def valida_uf(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.upper()
        if v not in _UF_VALIDAS:
            raise ValueError(f"UF inválida: {v}")
        return v

    @field_validator("status")
    @classmethod
    def valida_status(cls, v: str | None) -> str | None:
        if v is not None and v not in _STATUS_VALIDOS:
            raise ValueError(f"Status inválido: {v}. Esperado: {_STATUS_VALIDOS}")
        return v


class OrcamentoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    numero_proposta: str
    versao: int
    cliente_id: int
    descricao_obra: str | None
    uf_execucao: str
    beneficio_reidi: bool
    status: str
    total_custo_direto: Decimal
    total_proposta: Decimal
    margem_liquida_real: Decimal


# ── Itens do Orçamento ────────────────────────────────────────────────────────


class OrcamentoItemCreate(BaseModel):
    bloco: str
    ficha_servico_id: int | None = None
    ficha_produto_id: int | None = None
    descricao: str
    unidade_medida: str
    quantidade: Decimal
    mod_fat: str = "BDI-MAT+MO"
    margem_percentual: Decimal = Decimal("0.10")
    custo_direto_unitario: Decimal = Decimal("0")
    item_excepcional: bool = False

    @field_validator("bloco")
    @classmethod
    def valida_bloco(cls, v: str) -> str:
        if v not in _BLOCOS_VALIDOS:
            raise ValueError(f"bloco inválido: {v}. Esperado: {_BLOCOS_VALIDOS}")
        return v

    @field_validator("mod_fat")
    @classmethod
    def valida_mod_fat(cls, v: str) -> str:
        if v not in _MOD_FAT_VALIDAS:
            raise ValueError(f"mod_fat inválido: {v}. Esperado: {_MOD_FAT_VALIDAS}")
        return v

    @field_validator("quantidade")
    @classmethod
    def valida_quantidade(cls, v: Decimal) -> Decimal:
        if v <= Decimal("0"):
            raise ValueError("quantidade deve ser positiva")
        return v

    @field_validator("margem_percentual")
    @classmethod
    def valida_margem(cls, v: Decimal) -> Decimal:
        if v < Decimal("0") or v >= Decimal("1"):
            raise ValueError(
                "margem_percentual deve estar entre 0 e 1 (fração decimal)"
            )
        return v

    @model_validator(mode="after")
    def valida_ficha_exclusiva(self) -> "OrcamentoItemCreate":
        if self.ficha_servico_id is not None and self.ficha_produto_id is not None:
            raise ValueError(
                "ficha_servico_id e ficha_produto_id não podem ser informados simultaneamente"
            )
        # Blocos não faturáveis não devem ter ficha de serviço/produto
        if self.bloco in ("operacional", "excepcionais"):
            if self.ficha_servico_id is not None or self.ficha_produto_id is not None:
                raise ValueError(
                    f"Bloco '{self.bloco}' não pode ter ficha_servico_id nem ficha_produto_id"
                )
        return self


class OrcamentoItemUpdate(BaseModel):
    quantidade: Decimal | None = None
    mod_fat: str | None = None
    margem_percentual: Decimal | None = None
    custo_direto_unitario: Decimal | None = None

    @field_validator("mod_fat")
    @classmethod
    def valida_mod_fat(cls, v: str | None) -> str | None:
        if v is not None and v not in _MOD_FAT_VALIDAS:
            raise ValueError(f"mod_fat inválido: {v}")
        return v

    @field_validator("quantidade")
    @classmethod
    def valida_quantidade(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v <= Decimal("0"):
            raise ValueError("quantidade deve ser positiva")
        return v


class OrcamentoItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    orcamento_id: int
    bloco: str
    ficha_servico_id: int | None
    ficha_produto_id: int | None
    descricao: str
    unidade_medida: str
    quantidade: Decimal
    mod_fat: str
    margem_percentual: Decimal
    custo_direto_unitario: Decimal
    bdi_taxa: Decimal
    preco_venda_unitario: Decimal
    preco_venda_total: Decimal
    peso_rateio: Decimal
    rateio_absorvido: Decimal
    preco_final_unitario: Decimal
    lucro_absoluto: Decimal
    item_excepcional: bool
    demanda_aprovacao: bool


# ── Resultado do cálculo (/calcular) ─────────────────────────────────────────


class ItemCalculadoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    bloco: str
    descricao: str
    quantidade: Decimal
    custo_direto_unitario: Decimal
    bdi_taxa: Decimal
    preco_venda_unitario: Decimal
    preco_venda_total: Decimal
    peso_rateio: Decimal
    rateio_absorvido: Decimal
    preco_final_unitario: Decimal
    lucro_absoluto: Decimal


class ResultadoCalculoRead(BaseModel):
    orcamento_id: int
    uf_execucao: str
    beneficio_reidi: bool
    itens: list[ItemCalculadoRead]
    subtotal_faturavel: Decimal
    total_nao_faturavel: Decimal
    total_proposta: Decimal
    margem_liquida_real: Decimal
    fator_k_percentual: Decimal
