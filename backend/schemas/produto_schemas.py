"""Schemas de Produtos, Componentes e item_fichas (BLOCO 4)."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from backend.schemas.validators import normalizar_texto


class ItemIndustrialBase(BaseModel):
    nome: str
    descricao: str | None = None
    caracteristicas: str | None = None
    dimensoes: str | None = None
    volume_m3: Decimal | None = None
    peso_kg: Decimal | None = None
    deposito_produtivo: str | None = None
    setor: str | None = None
    industrializado_terceiros: bool = False
    unidade_id: int | None = None
    possui_ficha_tecnica: bool = False
    ativo: bool = True

    _norm_nome = field_validator("nome")(normalizar_texto)


class ItemIndustrialCreate(ItemIndustrialBase):
    # codigo é gerado no backend; opcional no payload
    codigo: str | None = None


class ItemIndustrialUpdate(BaseModel):
    nome: str | None = None
    descricao: str | None = None
    caracteristicas: str | None = None
    dimensoes: str | None = None
    volume_m3: Decimal | None = None
    peso_kg: Decimal | None = None
    deposito_produtivo: str | None = None
    setor: str | None = None
    industrializado_terceiros: bool | None = None
    unidade_id: int | None = None
    possui_ficha_tecnica: bool | None = None
    ativo: bool | None = None

    _norm_nome = field_validator("nome")(normalizar_texto)


class ItemIndustrialRead(ItemIndustrialBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    codigo: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ── item_fichas ──────────────────────────────────────────────────────────────


class ItemFichaCreate(BaseModel):
    componente_id: int | None = None
    produto_id: int | None = None
    ficha_servico_id: int | None = None
    ficha_produto_id: int | None = None
    ficha_equipe_id: int | None = None

    @model_validator(mode="after")
    def valida(self) -> "ItemFichaCreate":
        if self.componente_id is None and self.produto_id is None:
            raise ValueError("Informe componente_id ou produto_id")
        if (
            self.ficha_servico_id is None
            and self.ficha_produto_id is None
            and self.ficha_equipe_id is None
        ):
            raise ValueError("Informe ao menos uma ficha")
        return self


class ItemFichaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    componente_id: int | None
    produto_id: int | None
    ficha_servico_id: int | None
    ficha_produto_id: int | None
    ficha_equipe_id: int | None
