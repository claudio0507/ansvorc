from decimal import Decimal

from pydantic import BaseModel, ConfigDict, model_validator


# ── Fichas de Equipe ─────────────────────────────────────────────────────────

class FichaEquipeItemCreate(BaseModel):
    tipo_recurso: str  # RH | EPI | FERRAMENTAL
    rh_id: int | None = None
    epi_id: int | None = None
    ferramental_id: int | None = None
    quantidade: Decimal
    observacao: str | None = None

    @model_validator(mode="after")
    def valida_recurso_exclusivo(self) -> "FichaEquipeItemCreate":
        filled = sum([
            self.rh_id is not None,
            self.epi_id is not None,
            self.ferramental_id is not None,
        ])
        if filled != 1:
            raise ValueError("Exatamente um de rh_id, epi_id ou ferramental_id deve ser informado")
        mapa = {"RH": self.rh_id, "EPI": self.epi_id, "FERRAMENTAL": self.ferramental_id}
        esperado = mapa.get(self.tipo_recurso)
        if esperado is None:
            raise ValueError(f"tipo_recurso '{self.tipo_recurso}' não corresponde ao FK preenchido")
        return self


class FichaEquipeItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ficha_equipe_id: int
    tipo_recurso: str
    rh_id: int | None
    epi_id: int | None
    ferramental_id: int | None
    quantidade: Decimal
    custo_unitario_gravado: Decimal
    observacao: str | None


class FichaEquipeCreate(BaseModel):
    codigo: str
    nome: str
    descricao: str | None = None
    producao_diaria: Decimal = Decimal("1.00")
    unidade_producao: str = "dia"


class FichaEquipeUpdate(BaseModel):
    nome: str | None = None
    descricao: str | None = None
    producao_diaria: Decimal | None = None
    unidade_producao: str | None = None
    ativo: bool | None = None


class FichaEquipeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    codigo: str
    nome: str
    descricao: str | None
    producao_diaria: Decimal
    unidade_producao: str
    possui_itens: bool
    ativo: bool
    itens: list[FichaEquipeItemRead] = []


# ── Fichas de Produto ─────────────────────────────────────────────────────────

class FichaProdutoItemCreate(BaseModel):
    material_id: int | None = None
    componente_filho_id: int | None = None
    quantidade: Decimal
    observacao: str | None = None

    @model_validator(mode="after")
    def valida_bom_exclusividade(self) -> "FichaProdutoItemCreate":
        filled = sum([
            self.material_id is not None,
            self.componente_filho_id is not None,
        ])
        if filled != 1:
            raise ValueError(
                "Exatamente um de material_id ou componente_filho_id deve ser informado — nunca ambos, nunca nenhum"
            )
        return self


class FichaProdutoItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ficha_produto_id: int
    material_id: int | None
    componente_filho_id: int | None
    quantidade: Decimal
    custo_unitario_gravado: Decimal
    observacao: str | None


class FichaProdutoCreate(BaseModel):
    codigo: str
    nome: str
    descricao: str | None = None
    unidade_medida: str = "un"


class FichaProdutoUpdate(BaseModel):
    nome: str | None = None
    descricao: str | None = None
    unidade_medida: str | None = None
    ativo: bool | None = None


class FichaProdutoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    codigo: str
    nome: str
    descricao: str | None
    unidade_medida: str
    possui_itens: bool
    ativo: bool
    itens: list[FichaProdutoItemRead] = []


# ── Fichas de Serviço ─────────────────────────────────────────────────────────

class FichaServicoRecursoCreate(BaseModel):
    ficha_equipe_id: int | None = None
    frota_id: int | None = None
    ferramental_id: int | None = None
    ficha_produto_id: int | None = None
    quantidade: Decimal
    observacao: str | None = None

    @model_validator(mode="after")
    def valida_recurso_exclusivo(self) -> "FichaServicoRecursoCreate":
        filled = sum([
            self.ficha_equipe_id is not None,
            self.frota_id is not None,
            self.ferramental_id is not None,
            self.ficha_produto_id is not None,
        ])
        if filled != 1:
            raise ValueError(
                "Exatamente um de ficha_equipe_id, frota_id, ferramental_id ou ficha_produto_id deve ser informado"
            )
        return self


class FichaServicoRecursoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ficha_servico_id: int
    ficha_equipe_id: int | None
    frota_id: int | None
    ferramental_id: int | None
    ficha_produto_id: int | None
    quantidade: Decimal
    custo_unitario_gravado: Decimal
    observacao: str | None


class FichaServicoCreate(BaseModel):
    codigo: str
    nome: str
    descricao: str | None = None
    tipo_servico: str
    unidade_medida: str
    producao_diaria: Decimal = Decimal("1.00")


class FichaServicoUpdate(BaseModel):
    nome: str | None = None
    descricao: str | None = None
    tipo_servico: str | None = None
    unidade_medida: str | None = None
    producao_diaria: Decimal | None = None
    ativo: bool | None = None


class FichaServicoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    codigo: str
    nome: str
    descricao: str | None
    tipo_servico: str
    unidade_medida: str
    producao_diaria: Decimal
    possui_recursos: bool
    ativo: bool
    recursos: list[FichaServicoRecursoRead] = []
