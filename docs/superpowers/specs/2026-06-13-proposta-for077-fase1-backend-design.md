# Proposta FOR-077 — Fase 1: Backend gaps

**Data:** 2026-06-13
**Branch alvo:** feat/melhorias-v2
**Contexto:** O `PROMPT_PROPOSTA.md` (FOR-077) pede editor de proposta + 19 seções; o backend já tem os 13 campos em `Orcamento` e 13 em `ConfigSistema` + schemas sincronizados. Decomposto em 3 fases: **F1 (backend, esta) → F2 (editor) → F3 (documento + PDF)**. F1 é a base de F2/F3.

## Objetivo

Fechar os gaps de backend do FOR-077: PATCH de descrição de item, PUT /config completo (17 campos) + seed FOR-077, e um endpoint que monta a proposta com fallback ConfigSistema resolvido.

## Decisões travadas (brainstorm)

- PATCH de descrição grava **`descricao_cliente`** (visão cliente), não `descricao` (composição) — coerente com sub-projeto D.
- PUT /config usa **`model_dump(exclude_unset=True)`** — grava o que veio (inclui null para limpar), corrige o bug "não dá pra limpar campo".
- Fallback exposto via **endpoint dedicado `GET /orcamentos/{id}/proposta`** — lógica num lugar só, consumida por F2 e F3.
- Sem Alembic/migrations (projeto usa `Base.metadata.create_all()` + seed).
- Motor BDI intocado.

## Seção 1.1 — PATCH descrição de item

Schema dedicado em `backend/schemas/orcamento_schemas.py`:
```python
class OrcamentoItemDescricaoPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    descricao: str
```
`extra="forbid"` → qualquer campo além de `descricao` resulta em 422 (Pydantic v2 rejeita).

Endpoint em `backend/routers/orcamento_routers.py`:
```python
@router.patch("/orcamentos/{id}/itens/{item_id}", response_model=OrcamentoItemRead, tags=["orcamentos"])
def patch_descricao_item(id: int, item_id: int, payload: OrcamentoItemDescricaoPatch, db: Session = Depends(get_db)):
    orc = _get_or_404(db, Orcamento, id)
    _guard_rascunho(orc)  # 403 se não rascunho/reprovado
    item = db.get(OrcamentoItem, item_id)
    if not item or item.orcamento_id != id:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    item.descricao_cliente = payload.descricao
    db.commit()
    db.refresh(item)
    return item
```
Nota: grava `descricao_cliente`. O prompt diz "descricao" mas a regra do projeto preserva a composição; a planilha/proposta exibe `descricao_cliente || descricao`.

## Seção 1.2 — PUT /config completo (exclude_unset)

Reescrever `atualizar_config` em `backend/routers/extra_routers.py`:
```python
@router.put("/config", response_model=ConfigSistemaRead, tags=["config"])
def atualizar_config(payload: ConfigSistemaUpdate, db: Session = Depends(get_db)):
    cfg = _get_config(db)
    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(cfg, campo, valor)
    db.commit()
    db.refresh(cfg)
    return cfg
```
Cobre os 17 campos (12 dados + 5 diretor) já presentes em `ConfigSistemaUpdate`. `exclude_unset` permite limpar (enviar null) e não toca campos omitidos.

## Seção 1.3 — Seed FOR-077

Em `backend/seeds.py`, na criação/atualização do `ConfigSistema` (seed_extra ou equivalente), popular os defaults FOR-077:
```python
cnpj="20.945.724/0001-15",
banco="Bradesco", agencia="0110", conta_corrente="0287852-6",
diretor_cpf="277.540.838-92",
contato_comercial_nome="Milaini Carvalho Miranda",
contato_comercial_funcao="Comercial",
contato_comercial_fone="(18) 99683-6472",
contato_comercial_email="comercial@altanoroeste.com.br",
garantia_retencao_padrao_pct=Decimal("5"),
garantia_devolucao_padrao_dias=60,
clausula_tributaria_padrao="<texto IBS/CBS do prompt>",
reajustamento_padrao="<texto IPCA/IGPM do prompt>",
declaracoes_padrao="<12 bullets legais do prompt, \\n separados>",
```
(Textos completos em PROMPT_PROPOSTA.md linhas 105-109.) `seeds_prod.py` idem se aplicável.

## Seção 1.4 — Fallback + endpoint GET /orcamentos/{id}/proposta

Helper `backend/services/proposta_fallback.py`:
```python
def montar_proposta(orc, config) -> dict:
    """Resolve cada campo da proposta com fallback do ConfigSistema + defaults literais."""
    def fb(valor, padrao, literal=""):
        if valor not in (None, ""):
            return valor
        return padrao if padrao not in (None, "") else literal
    return {
        "texto_topo_proposta": fb(orc.texto_topo_proposta, config.declaracoes_padrao),
        "clausula_tributaria": fb(orc.clausula_tributaria, config.clausula_tributaria_padrao),
        "reajustamento": fb(orc.reajustamento, config.reajustamento_padrao),
        "garantia_retencao_pct": orc.garantia_retencao_pct if orc.garantia_retencao_pct is not None else (config.garantia_retencao_padrao_pct or Decimal("5")),
        "garantia_devolucao_dias": orc.garantia_devolucao_dias if orc.garantia_devolucao_dias is not None else (config.garantia_devolucao_padrao_dias or 60),
        "faturamento_direto": fb(orc.faturamento_direto, None, "Não aplicável."),
        "entrega_as_built": fb(orc.entrega_as_built, None, "Não aplicável."),
        "modalidade": fb(orc.modalidade, None, "Preço Unitário"),
        # campos diretos do orc (sem fallback): escopo, medicao_pagamento, prazo_entrega,
        #   validade_proposta, texto_livre_proposta, obra, testemunha_*
        # campos diretos do config: cnpj, banco, agencia, conta_corrente, diretor_*,
        #   contato_comercial_*, nome_empresa, logo_path
    }
```
Endpoint em `orcamento_routers.py`:
```python
@router.get("/orcamentos/{id}/proposta", tags=["orcamentos"])
def obter_proposta(id: int, db: Session = Depends(get_db)) -> dict:
    orc = _get_or_404(db, Orcamento, id)
    from backend.models.extra_models import ConfigSistema
    config = db.query(ConfigSistema).order_by(ConfigSistema.id).first()
    itens = db.query(OrcamentoItem).filter(OrcamentoItem.orcamento_id == id).all()
    cliente = db.get(Cliente, orc.cliente_id)
    resolvidos = montar_proposta(orc, config) if config else {}
    return {
        "orcamento": OrcamentoRead.model_validate(orc).model_dump(mode="json"),
        "config": ConfigSistemaRead.model_validate(config).model_dump(mode="json") if config else None,
        "cliente": ClienteRead.model_validate(cliente).model_dump(mode="json") if cliente else None,
        "itens": [OrcamentoItemRead.model_validate(i).model_dump(mode="json") for i in itens],
        "resolvidos": resolvidos,
        "garantia_texto": f"Retenção de {resolvidos.get('garantia_retencao_pct')}%, com devolução em {resolvidos.get('garantia_devolucao_dias')} dias após o termo de encerramento.",
    }
```
RBAC: `/api/v1/orcamentos` prefixo já cobre (orcamentista/parametrizador/sponsor). O PATCH e o GET caem nesse prefixo — sem entrada nova no middleware.

## Seção 1.5 — Testes (TDD)

`tests/test_proposta_for077.py` (novo):
- PATCH descrição: edita `descricao_cliente` (200); payload com campo extra → 422; orçamento não-rascunho → 403; item de outro orçamento → 404.
- PUT /config: round-trip dos 17 campos; limpar um campo via null (exclude_unset).
- Fallback: orçamento com campos vazios → `resolvidos` traz valores do config; garantia_texto montado; defaults literais ("Não aplicável.", "Preço Unitário") quando config também vazio.

## Arquivos tocados

- `backend/schemas/orcamento_schemas.py` (OrcamentoItemDescricaoPatch)
- `backend/routers/orcamento_routers.py` (PATCH item + GET proposta)
- `backend/routers/extra_routers.py` (PUT /config exclude_unset)
- `backend/services/proposta_fallback.py` (novo)
- `backend/seeds.py` (+ seeds_prod.py se aplicável)
- `tests/test_proposta_for077.py` (novo)

## Fora de escopo (F2/F3)

- Editor `proposta.$id.tsx`, aba Empresa (F2).
- Redesenho do documento `proposta.tsx` + `export_pdf.py` FOR-077 (F3).
- Motor BDI/cálculos; Alembic.
