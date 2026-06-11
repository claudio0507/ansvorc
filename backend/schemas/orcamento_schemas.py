"""Schemas Pydantic de Orçamento e CRM — alinhados a docs/02 + docs/04.

margem_lucro é PERCENTUAL (10 = 10%, DECIMAL(5,2)). Custos de itens faturáveis vêm
da ficha (não enviados pelo cliente); apenas itens manuais informam custo.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from backend.schemas.validators import normalizar_texto, normalizar_uf

# ── Clientes ──────────────────────────────────────────────────────────────────


class ClienteCreate(BaseModel):
    nome: str
    tipo: str | None = None
    cnpj_cpf: str | None = None
    contato_nome: str | None = None
    contato_email: str | None = None
    contato_telefone: str | None = None
    ativo: bool = True

    _norm_nome = field_validator("nome")(normalizar_texto)


class ClienteUpdate(BaseModel):
    nome: str | None = None
    tipo: str | None = None
    cnpj_cpf: str | None = None
    contato_nome: str | None = None
    contato_email: str | None = None
    contato_telefone: str | None = None
    ativo: bool | None = None

    _norm_nome = field_validator("nome")(normalizar_texto)


class ClienteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    tipo: str | None
    cnpj_cpf: str | None
    contato_nome: str | None
    contato_email: str | None
    contato_telefone: str | None
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
_TIPO_ORIGEM_VALIDOS = {"servico", "produto", "operacional", "manual"}


def _check_uf(v: str | None) -> str | None:
    if v is None:
        return v
    v = normalizar_uf(v)
    if v not in _UF_VALIDAS:
        raise ValueError(f"UF inválida: {v}")
    return v


class OrcamentoCreate(BaseModel):
    numero: str
    cliente_id: int
    obra: str | None = None
    uf_execucao: str = "PR"
    beneficio_reidi: bool = False
    desconto_percentual: Decimal = Decimal("0")
    orcamentista_id: int | None = None  # BLOCO 2.4

    _norm_obra = field_validator("obra")(normalizar_texto)
    _valida_uf = field_validator("uf_execucao")(_check_uf)

    @field_validator("desconto_percentual")
    @classmethod
    def valida_desconto(cls, v: Decimal) -> Decimal:
        if v < Decimal("0") or v > Decimal("100"):
            raise ValueError("desconto_percentual deve estar entre 0 e 100")
        return v


class OrcamentoUpdate(BaseModel):
    obra: str | None = None
    uf_execucao: str | None = None
    beneficio_reidi: bool | None = None
    desconto_percentual: Decimal | None = None
    status: str | None = None
    orcamentista_id: int | None = None
    validade_proposta: str | None = None
    condicoes_pagamento: str | None = None
    texto_livre_proposta: str | None = None

    _norm_obra = field_validator("obra")(normalizar_texto)
    _valida_uf = field_validator("uf_execucao")(_check_uf)

    @field_validator("status")
    @classmethod
    def valida_status(cls, v: str | None) -> str | None:
        if v is not None and v not in _STATUS_VALIDOS:
            raise ValueError(f"Status inválido: {v}. Esperado: {_STATUS_VALIDOS}")
        return v

    @field_validator("desconto_percentual")
    @classmethod
    def valida_desconto(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and (v < Decimal("0") or v > Decimal("100")):
            raise ValueError("desconto_percentual deve estar entre 0 e 100")
        return v


class OrcamentoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    numero: str
    versao: int
    cliente_id: int
    obra: str | None
    uf_execucao: str
    beneficio_reidi: bool
    desconto_percentual: Decimal
    status: str
    orcamento_origem_id: int | None
    created_by: int | None
    created_at: datetime | None = None
    aprovado_em: datetime | None = None
    observacoes_internas: str | None = None
    orcamentista_id: int | None = None
    validade_proposta: str | None = None
    condicoes_pagamento: str | None = None
    texto_livre_proposta: str | None = None
    total_custo_direto: Decimal
    total_proposta: Decimal
    margem_liquida_real: Decimal


# ── Itens do Orçamento ────────────────────────────────────────────────────────


class OrcamentoItemCreate(BaseModel):
    bloco: str
    ficha_servico_id: int | None = None
    ficha_produto_id: int | None = None
    produto_id: int | None = None  # BLOCO 1.5 — produto do cadastro `produtos`
    descricao: str
    descricao_cliente: str | None = None  # BLOCO 2.3
    unidade: str
    quantidade: Decimal
    mod_fat: str = "BDI-MAT+MO"
    margem_lucro: Decimal = Decimal("10")  # percentual
    # custo informado apenas para itens manuais/operacionais (faturáveis vêm da ficha)
    custo_direto_unitario: Decimal = Decimal("0")

    _norm_desc = field_validator("descricao")(normalizar_texto)

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

    @field_validator("margem_lucro")
    @classmethod
    def valida_margem(cls, v: Decimal) -> Decimal:
        if v < Decimal("0") or v >= Decimal("100"):
            raise ValueError("margem_lucro deve estar entre 0 e 100 (percentual)")
        return v

    @model_validator(mode="after")
    def valida_ficha_exclusiva(self) -> "OrcamentoItemCreate":
        if self.ficha_servico_id is not None and self.ficha_produto_id is not None:
            raise ValueError(
                "ficha_servico_id e ficha_produto_id não podem ser informados juntos"
            )
        if self.bloco in ("operacional", "excepcionais") and (
            self.ficha_servico_id is not None or self.ficha_produto_id is not None
        ):
            raise ValueError(
                f"Bloco '{self.bloco}' não pode ter ficha_servico_id nem ficha_produto_id"
            )
        return self


class OrcamentoItemUpdate(BaseModel):
    quantidade: Decimal | None = None
    mod_fat: str | None = None
    margem_lucro: Decimal | None = None
    custo_direto_unitario: Decimal | None = None
    descricao_cliente: str | None = None  # BLOCO 2.3

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

    @field_validator("margem_lucro")
    @classmethod
    def valida_margem(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and (v < Decimal("0") or v >= Decimal("100")):
            raise ValueError("margem_lucro deve estar entre 0 e 100 (percentual)")
        return v


class OrcamentoItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    orcamento_id: int
    bloco: str
    ficha_servico_id: int | None
    ficha_produto_id: int | None
    produto_id: int | None
    tipo_origem: str
    descricao: str
    descricao_cliente: str | None
    unidade: str
    quantidade: Decimal
    mod_fat: str
    margem_lucro: Decimal
    custo_direto_unitario: Decimal
    bdi_aplicado: Decimal
    preco_venda_unitario: Decimal
    preco_venda_unitario_final: Decimal
    preco_venda_total: Decimal
    lucro_absoluto: Decimal
    peso_rateio: Decimal
    desconto_rateado: Decimal
    flag_aprovacao: bool


# ── Resultado do cálculo (/calcular) ─────────────────────────────────────────


class ItemCalculadoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    bloco: str
    descricao: str
    quantidade: Decimal
    custo_direto_unitario: Decimal
    bdi_aplicado: Decimal
    preco_venda_unitario: Decimal
    preco_venda_unitario_final: Decimal
    preco_venda_total: Decimal
    peso_rateio: Decimal
    desconto_rateado: Decimal
    lucro_absoluto: Decimal


class ResultadoCalculoRead(BaseModel):
    orcamento_id: int
    uf_execucao: str
    beneficio_reidi: bool
    desconto_percentual: Decimal
    itens: list[ItemCalculadoRead]
    subtotal_faturavel: Decimal
    total_nao_faturavel: Decimal
    total_proposta: Decimal
    margem_liquida_real: Decimal
    fator_k_percentual: Decimal
