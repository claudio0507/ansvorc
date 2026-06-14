# Proposta FOR-077 — Fase 1 (Backend) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fechar os gaps de backend do FOR-077 — PATCH de descrição de item (`descricao_cliente`), PUT /config completo com `exclude_unset`, seed FOR-077, e endpoint `GET /orcamentos/{id}/proposta` com fallback ConfigSistema resolvido.

**Architecture:** FastAPI + SQLAlchemy 2.0 (Mapped). Models e schemas já têm os 13+18 campos FOR-077 (verificado). Esta fase só adiciona: 1 schema, 1 helper de fallback (módulo novo em `backend/services/`), 2 endpoints novos no router de orçamento, reescreve 1 endpoint no router de config, popula o seed. Sem Alembic — o projeto usa `Base.metadata.create_all()` + `seeds.py`.

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy 2.0, Pydantic v2, pytest + `fastapi.testclient.TestClient`, SQLite in-memory nos testes.

---

## Convenções verificadas no codebase (leia antes de começar)

- **Prefixo da API:** todos os endpoints de orçamento/config vivem sob `/api/v1` (ex.: `/api/v1/config`, `/api/v1/orcamentos/{id}`). O `router` nos arquivos NÃO repete o prefixo — ele é aplicado no `main.py`. Ao declarar rota use `/orcamentos/...` e `/config` como já é feito.
- **Helpers existentes em `backend/routers/orcamento_routers.py`:** `_get_or_404(db, model, pk)` (404 "Não encontrado"), `_guard_rascunho(orc)` (403 se status não ∈ {rascunho, reprovado}). Reuse — não recrie.
- **Padrão "item não encontrado":** o router usa `db.query(OrcamentoItem).filter(OrcamentoItem.id == item_id, OrcamentoItem.orcamento_id == id).first()` e levanta `HTTPException(404, "Item não encontrado neste orçamento")`. Siga esse padrão (não o `db.get` do spec).
- **Imports no topo de `orcamento_routers.py`:** `Cliente`, `Orcamento`, `OrcamentoItem` já importados; `ClienteRead`, `OrcamentoRead`, `OrcamentoItemRead` já importados. `ConfigSistema`/`ConfigSistemaRead` NÃO estão importados nesse arquivo — importe-os dentro da função (o arquivo já usa import local, ex.: `historico_descontos`).
- **Schema de config está em `backend/schemas/extra_schemas.py`** (não `orcamento_schemas`). `ConfigSistemaUpdate` já tem os 18 campos. `ConfigSistemaRead` idem.
- **Testes são auto-contidos:** cada arquivo de teste cria seu próprio `engine_test` SQLite in-memory + `client = TestClient(app, headers=...)` + fixture `setup_db` autouse. Copie o cabeçalho de `tests/test_config_diretor.py` / `tests/test_orcamentos.py`. NÃO dependa do `conftest.py` (ele só expõe `sponsor_token`/`sponsor_headers` de escopo session, que estes testes não usam).
- **Rodar testes (Windows PowerShell):** `py -m pytest tests/test_proposta_for077.py -v`

---

## File Structure

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `backend/schemas/orcamento_schemas.py` | Modificar | + `OrcamentoItemDescricaoPatch` (schema do PATCH, `extra="forbid"`) |
| `backend/services/proposta_fallback.py` | Criar | `montar_proposta(orc, config) -> dict` — resolve fallback ConfigSistema + defaults literais. Lógica pura, sem DB. |
| `backend/routers/orcamento_routers.py` | Modificar | + `PATCH /orcamentos/{id}/itens/{item_id}` (grava `descricao_cliente`) e + `GET /orcamentos/{id}/proposta` |
| `backend/routers/extra_routers.py` | Modificar | reescrever `atualizar_config` para `model_dump(exclude_unset=True)` (cobre os 18 campos + permite limpar com null) |
| `backend/seeds.py` | Modificar | `seed_extra` popula o `ConfigSistema` com os defaults FOR-077 |
| `tests/test_proposta_for077.py` | Criar | TDD de tudo acima |

`seeds_prod.py` NÃO tem `ConfigSistema` (verificado — não cria essa linha). Fora de escopo.

---

## Task 1: Schema `OrcamentoItemDescricaoPatch`

**Files:**
- Modify: `backend/schemas/orcamento_schemas.py`
- Test: `tests/test_proposta_for077.py`

- [ ] **Step 1: Criar o arquivo de teste com o cabeçalho auto-contido e o primeiro teste (PATCH feliz)**

Cria `tests/test_proposta_for077.py`:

```python
"""tests/test_proposta_for077.py — FOR-077 Fase 1 (backend gaps).

PATCH descrição de item (descricao_cliente), PUT /config completo,
endpoint GET /orcamentos/{id}/proposta com fallback ConfigSistema.
"""

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.auth import criar_token
from backend.database import Base, get_db
from backend.main import app
from backend.models.orcamento_models import Cliente, Orcamento, OrcamentoItem

engine_test = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


_TOKEN = criar_token(usuario_id=9999, papel="sponsor")
client = TestClient(app, headers={"Authorization": f"Bearer {_TOKEN}"})


@pytest.fixture(autouse=True)
def setup_db():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def db_session():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


def _criar_orcamento_com_item(db, *, status="rascunho"):
    """Cria Cliente + Orcamento + 1 OrcamentoItem. Retorna (orc_id, item_id)."""
    c = Cliente(nome="Motiva Rodovias S.A.", cnpj_cpf="00.000.000/0001-91")
    db.add(c)
    db.flush()
    orc = Orcamento(
        numero="ORC-FOR077-1",
        cliente_id=c.id,
        obra="Recapeamento SP-333",
        uf_execucao="SP",
        status=status,
    )
    db.add(orc)
    db.flush()
    item = OrcamentoItem(
        orcamento_id=orc.id,
        bloco="servicos",
        tipo_origem="manual",
        descricao="Fresagem (descrição interna de composição)",
        unidade="m2",
        quantidade=Decimal("100"),
        mod_fat="BDI-MAT+MO",
    )
    db.add(item)
    db.commit()
    return orc.id, item.id


class TestPatchDescricaoItem:
    def test_patch_grava_descricao_cliente(self, db_session):
        orc_id, item_id = _criar_orcamento_com_item(db_session)
        r = client.patch(
            f"/api/v1/orcamentos/{orc_id}/itens/{item_id}",
            json={"descricao": "Fresagem da pista existente"},
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["descricao_cliente"] == "Fresagem da pista existente"
        # composição preservada
        assert body["descricao"] == "Fresagem (descrição interna de composição)"
```

- [ ] **Step 2: Rodar o teste e confirmar que falha**

Run: `py -m pytest tests/test_proposta_for077.py::TestPatchDescricaoItem::test_patch_grava_descricao_cliente -v`
Expected: FAIL — 404/405 (rota PATCH ainda não existe).

- [ ] **Step 3: Adicionar o schema `OrcamentoItemDescricaoPatch` em `orcamento_schemas.py`**

Verifique no topo do arquivo que `ConfigDict` está importado de `pydantic` (a maioria dos schemas Read já usa `model_config = ConfigDict(...)`). Adicione perto dos outros schemas de item (ex.: após `OrcamentoItemUpdate`):

```python
class OrcamentoItemDescricaoPatch(BaseModel):
    """PATCH da descrição exibida ao cliente. extra='forbid' → 422 em campo estranho."""
    model_config = ConfigDict(extra="forbid")
    descricao: str
```

- [ ] **Step 4: (sem implementação de rota ainda) — confirmar que o schema importa**

Run: `py -c "from backend.schemas.orcamento_schemas import OrcamentoItemDescricaoPatch; print('ok')"`
Expected: `ok`

- [ ] **Step 5: Commit**

```bash
git add backend/schemas/orcamento_schemas.py tests/test_proposta_for077.py
git commit -m "test(proposta): schema OrcamentoItemDescricaoPatch + teste PATCH descrição"
```

---

## Task 2: Endpoint PATCH `/orcamentos/{id}/itens/{item_id}`

**Files:**
- Modify: `backend/routers/orcamento_routers.py`
- Test: `tests/test_proposta_for077.py`

- [ ] **Step 1: Adicionar os testes de erro (422 extra, 403 não-rascunho, 404 item de outro orçamento)**

Acrescente à classe `TestPatchDescricaoItem`:

```python
    def test_patch_campo_extra_retorna_422(self, db_session):
        orc_id, item_id = _criar_orcamento_com_item(db_session)
        r = client.patch(
            f"/api/v1/orcamentos/{orc_id}/itens/{item_id}",
            json={"descricao": "ok", "descricao_cliente": "tentativa direta"},
        )
        assert r.status_code == 422, r.text

    def test_patch_orcamento_congelado_retorna_403(self, db_session):
        orc_id, item_id = _criar_orcamento_com_item(db_session, status="aprovado")
        r = client.patch(
            f"/api/v1/orcamentos/{orc_id}/itens/{item_id}",
            json={"descricao": "nao deveria gravar"},
        )
        assert r.status_code == 403, r.text

    def test_patch_item_de_outro_orcamento_retorna_404(self, db_session):
        orc_id, item_id = _criar_orcamento_com_item(db_session)
        outro_orc_id, _ = _criar_orcamento_com_item(db_session)
        # item_id pertence a orc_id, mas pedimos via outro_orc_id
        r = client.patch(
            f"/api/v1/orcamentos/{outro_orc_id}/itens/{item_id}",
            json={"descricao": "x"},
        )
        assert r.status_code == 404, r.text
```

Nota: `_criar_orcamento_com_item` cria `numero="ORC-FOR077-1"` fixo, mas `numero` é `unique`. Para o teste de 404 que chama a fixture duas vezes, ajuste a fixture para numerar de forma única. **Atualize `_criar_orcamento_com_item`** para receber um sufixo:

```python
def _criar_orcamento_com_item(db, *, status="rascunho", sufixo="1"):
    c = Cliente(nome="Motiva Rodovias S.A.", cnpj_cpf="00.000.000/0001-91")
    db.add(c)
    db.flush()
    orc = Orcamento(
        numero=f"ORC-FOR077-{sufixo}",
        cliente_id=c.id,
        obra="Recapeamento SP-333",
        uf_execucao="SP",
        status=status,
    )
    db.add(orc)
    db.flush()
    item = OrcamentoItem(
        orcamento_id=orc.id,
        bloco="servicos",
        tipo_origem="manual",
        descricao="Fresagem (descrição interna de composição)",
        unidade="m2",
        quantidade=Decimal("100"),
        mod_fat="BDI-MAT+MO",
    )
    db.add(item)
    db.commit()
    return orc.id, item.id
```

E no `test_patch_item_de_outro_orcamento_retorna_404` passe `sufixo="2"` na segunda chamada:

```python
        outro_orc_id, _ = _criar_orcamento_com_item(db_session, sufixo="2")
```

- [ ] **Step 2: Rodar e confirmar que os novos testes falham**

Run: `py -m pytest tests/test_proposta_for077.py::TestPatchDescricaoItem -v`
Expected: o teste feliz e os de erro FALHAM (rota ainda não existe → 404/405 onde se esperava 200/422/403).

- [ ] **Step 3: Adicionar o import do schema e o endpoint PATCH**

Em `backend/routers/orcamento_routers.py`, no bloco de import de `backend.schemas.orcamento_schemas`, acrescente `OrcamentoItemDescricaoPatch` à lista. Depois, adicione o endpoint logo após `atualizar_item` (o PUT de item), seguindo o padrão de busca de item já usado no arquivo:

```python
@router.patch(
    "/orcamentos/{id}/itens/{item_id}",
    response_model=OrcamentoItemRead,
    tags=["orcamentos"],
)
def patch_descricao_item(
    id: int,
    item_id: int,
    payload: OrcamentoItemDescricaoPatch,
    db: Session = Depends(get_db),
):
    """FOR-077 — edita a descrição exibida ao cliente (descricao_cliente).

    Preserva `descricao` (composição). Só em status editável (rascunho/reprovado).
    """
    orc = _get_or_404(db, Orcamento, id)
    _guard_rascunho(orc)
    item = (
        db.query(OrcamentoItem)
        .filter(OrcamentoItem.id == item_id, OrcamentoItem.orcamento_id == id)
        .first()
    )
    if not item:
        raise HTTPException(
            status_code=404, detail="Item não encontrado neste orçamento"
        )
    item.descricao_cliente = payload.descricao
    db.commit()
    db.refresh(item)
    return item
```

- [ ] **Step 4: Rodar a classe inteira e confirmar verde**

Run: `py -m pytest tests/test_proposta_for077.py::TestPatchDescricaoItem -v`
Expected: 4 PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/routers/orcamento_routers.py tests/test_proposta_for077.py
git commit -m "feat(proposta): PATCH descrição de item grava descricao_cliente (FOR-077)"
```

---

## Task 3: PUT `/config` completo com `exclude_unset`

**Files:**
- Modify: `backend/routers/extra_routers.py:99-110`
- Test: `tests/test_proposta_for077.py`

- [ ] **Step 1: Escrever os testes de round-trip e de limpar campo via null**

Adicione ao arquivo de teste:

```python
class TestPutConfigCompleto:
    def test_round_trip_campos_for077(self):
        payload = {
            "nome_empresa": "ALTA NOROESTE",
            "cnpj": "20.945.724/0001-15",
            "banco": "Bradesco",
            "agencia": "0110",
            "conta_corrente": "0287852-6",
            "diretor_cpf": "277.540.838-92",
            "contato_comercial_nome": "Milaini Carvalho Miranda",
            "contato_comercial_funcao": "Comercial",
            "contato_comercial_fone": "(18) 99683-6472",
            "contato_comercial_email": "comercial@altanoroeste.com.br",
            "garantia_retencao_padrao_pct": 5,
            "garantia_devolucao_padrao_dias": 60,
            "clausula_tributaria_padrao": "texto tributário",
            "reajustamento_padrao": "texto reajuste",
            "declaracoes_padrao": "linha1\nlinha2",
        }
        r = client.put("/api/v1/config", json=payload)
        assert r.status_code == 200, r.text
        d = client.get("/api/v1/config").json()
        assert d["cnpj"] == "20.945.724/0001-15"
        assert d["contato_comercial_email"] == "comercial@altanoroeste.com.br"
        assert str(d["garantia_retencao_padrao_pct"]) in ("5", "5.0", "5.00")
        assert d["garantia_devolucao_padrao_dias"] == 60
        assert d["declaracoes_padrao"] == "linha1\nlinha2"

    def test_limpar_campo_via_null(self):
        client.put("/api/v1/config", json={"banco": "Bradesco"})
        assert client.get("/api/v1/config").json()["banco"] == "Bradesco"
        # exclude_unset: enviar null limpa; omitir não toca
        client.put("/api/v1/config", json={"banco": None})
        assert client.get("/api/v1/config").json()["banco"] is None

    def test_omitir_campo_nao_apaga(self):
        client.put("/api/v1/config", json={"banco": "Bradesco", "agencia": "0110"})
        client.put("/api/v1/config", json={"agencia": "0220"})
        d = client.get("/api/v1/config").json()
        assert d["agencia"] == "0220"
        assert d["banco"] == "Bradesco"  # não foi tocado
```

- [ ] **Step 2: Rodar e confirmar falha**

Run: `py -m pytest tests/test_proposta_for077.py::TestPutConfigCompleto -v`
Expected: `test_round_trip_campos_for077` FALHA (impl atual só grava nome+diretor — cnpj/banco/etc vêm null). `test_limpar_campo_via_null` FALHA (impl atual usa `is not None`, ignora null).

- [ ] **Step 3: Reescrever `atualizar_config`**

Em `backend/routers/extra_routers.py`, substitua o corpo de `atualizar_config` (linhas 99-110) por:

```python
@router.put("/config", response_model=ConfigSistemaRead, tags=["config"])
def atualizar_config(payload: ConfigSistemaUpdate, db: Session = Depends(get_db)):
    cfg = _get_config(db)
    # exclude_unset: grava só o que veio no JSON (inclui null para limpar);
    # campos omitidos não são tocados. Corrige o bug "não dá pra limpar campo".
    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(cfg, campo, valor)
    db.commit()
    db.refresh(cfg)
    return cfg
```

- [ ] **Step 4: Rodar e confirmar verde**

Run: `py -m pytest tests/test_proposta_for077.py::TestPutConfigCompleto -v`
Expected: 3 PASS.

Run regressão do config antigo: `py -m pytest tests/test_config_diretor.py -v`
Expected: 2 PASS (o novo loop cobre diretor também).

- [ ] **Step 5: Commit**

```bash
git add backend/routers/extra_routers.py tests/test_proposta_for077.py
git commit -m "feat(config): PUT /config grava 18 campos via exclude_unset (limpa com null)"
```

---

## Task 4: Helper de fallback `montar_proposta`

**Files:**
- Create: `backend/services/proposta_fallback.py`
- Test: `tests/test_proposta_for077.py`

Helper puro (recebe objetos `orc` e `config`, devolve dict — sem DB). Testável isoladamente.

- [ ] **Step 1: Escrever o teste unitário do helper**

Adicione ao arquivo de teste (usa objetos do model direto, sem HTTP):

```python
from types import SimpleNamespace

from backend.services.proposta_fallback import montar_proposta


class TestMontarProposta:
    def _orc_vazio(self):
        # SimpleNamespace simula um Orcamento só com os atributos lidos pelo helper
        return SimpleNamespace(
            texto_topo_proposta=None,
            clausula_tributaria=None,
            reajustamento=None,
            garantia_retencao_pct=None,
            garantia_devolucao_dias=None,
            faturamento_direto=None,
            entrega_as_built=None,
            modalidade=None,
        )

    def _config_cheio(self):
        return SimpleNamespace(
            declaracoes_padrao="declarações default",
            clausula_tributaria_padrao="cláusula default",
            reajustamento_padrao="reajuste default",
            garantia_retencao_padrao_pct=Decimal("5"),
            garantia_devolucao_padrao_dias=60,
        )

    def test_usa_padrao_do_config_quando_orc_vazio(self):
        r = montar_proposta(self._orc_vazio(), self._config_cheio())
        assert r["clausula_tributaria"] == "cláusula default"
        assert r["reajustamento"] == "reajuste default"
        assert r["texto_topo_proposta"] == "declarações default"
        assert r["garantia_retencao_pct"] == Decimal("5")
        assert r["garantia_devolucao_dias"] == 60

    def test_orc_tem_precedencia_sobre_config(self):
        orc = self._orc_vazio()
        orc.clausula_tributaria = "cláusula específica do orçamento"
        orc.garantia_retencao_pct = Decimal("10")
        r = montar_proposta(orc, self._config_cheio())
        assert r["clausula_tributaria"] == "cláusula específica do orçamento"
        assert r["garantia_retencao_pct"] == Decimal("10")

    def test_defaults_literais_quando_config_tambem_vazio(self):
        config = SimpleNamespace(
            declaracoes_padrao=None,
            clausula_tributaria_padrao=None,
            reajustamento_padrao=None,
            garantia_retencao_padrao_pct=None,
            garantia_devolucao_padrao_dias=None,
        )
        r = montar_proposta(self._orc_vazio(), config)
        assert r["faturamento_direto"] == "Não aplicável."
        assert r["entrega_as_built"] == "Não aplicável."
        assert r["modalidade"] == "Preço Unitário"
        # garantia cai nos literais 5 / 60 mesmo sem config
        assert r["garantia_retencao_pct"] == Decimal("5")
        assert r["garantia_devolucao_dias"] == 60
```

- [ ] **Step 2: Rodar e confirmar falha**

Run: `py -m pytest tests/test_proposta_for077.py::TestMontarProposta -v`
Expected: FAIL — `ModuleNotFoundError: backend.services.proposta_fallback`.

- [ ] **Step 3: Criar `backend/services/proposta_fallback.py`**

```python
"""FOR-077 — resolução de fallback dos campos da proposta.

Precedência por campo: valor do Orçamento → padrão do ConfigSistema → literal.
Lógica pura (sem DB) para ser reusada por F2 (editor) e F3 (documento/PDF).
"""

from decimal import Decimal


def montar_proposta(orc, config) -> dict:
    """Resolve cada campo da proposta com fallback do ConfigSistema + defaults literais.

    `orc` e `config` são objetos com os atributos lidos abaixo (models ou stubs).
    """

    def fb(valor, padrao, literal=""):
        if valor not in (None, ""):
            return valor
        if padrao not in (None, ""):
            return padrao
        return literal

    return {
        "texto_topo_proposta": fb(orc.texto_topo_proposta, config.declaracoes_padrao),
        "clausula_tributaria": fb(
            orc.clausula_tributaria, config.clausula_tributaria_padrao
        ),
        "reajustamento": fb(orc.reajustamento, config.reajustamento_padrao),
        "garantia_retencao_pct": (
            orc.garantia_retencao_pct
            if orc.garantia_retencao_pct is not None
            else (config.garantia_retencao_padrao_pct or Decimal("5"))
        ),
        "garantia_devolucao_dias": (
            orc.garantia_devolucao_dias
            if orc.garantia_devolucao_dias is not None
            else (config.garantia_devolucao_padrao_dias or 60)
        ),
        "faturamento_direto": fb(orc.faturamento_direto, None, "Não aplicável."),
        "entrega_as_built": fb(orc.entrega_as_built, None, "Não aplicável."),
        "modalidade": fb(orc.modalidade, None, "Preço Unitário"),
    }
```

Nota: campos diretos sem fallback (escopo, medicao_pagamento, prazo_entrega, validade_proposta, texto_livre_proposta, obra, testemunha_*, cnpj/banco/diretor_*/contato_comercial_*/nome_empresa/logo_path) NÃO entram aqui — o endpoint (Task 5) já devolve `orcamento`/`config`/`cliente` serializados completos.

- [ ] **Step 4: Rodar e confirmar verde**

Run: `py -m pytest tests/test_proposta_for077.py::TestMontarProposta -v`
Expected: 3 PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/services/proposta_fallback.py tests/test_proposta_for077.py
git commit -m "feat(proposta): helper montar_proposta com fallback ConfigSistema (FOR-077)"
```

---

## Task 5: Endpoint GET `/orcamentos/{id}/proposta`

**Files:**
- Modify: `backend/routers/orcamento_routers.py`
- Test: `tests/test_proposta_for077.py`

- [ ] **Step 1: Escrever o teste de integração do endpoint**

Adicione ao arquivo de teste. Cria orçamento com campos vazios + config com padrões → confere que `resolvidos` traz os padrões e `garantia_texto` é montado.

```python
class TestEndpointProposta:
    def test_proposta_resolve_fallback_e_monta_garantia(self, db_session):
        orc_id, _ = _criar_orcamento_com_item(db_session, sufixo="prop1")
        # popula config com padrões FOR-077
        client.put(
            "/api/v1/config",
            json={
                "nome_empresa": "ALTA NOROESTE",
                "cnpj": "20.945.724/0001-15",
                "clausula_tributaria_padrao": "cláusula default",
                "garantia_retencao_padrao_pct": 5,
                "garantia_devolucao_padrao_dias": 60,
            },
        )
        r = client.get(f"/api/v1/orcamentos/{orc_id}/proposta")
        assert r.status_code == 200, r.text
        body = r.json()
        # blocos serializados presentes
        assert body["orcamento"]["id"] == orc_id
        assert body["config"]["cnpj"] == "20.945.724/0001-15"
        assert body["cliente"]["nome"] == "Motiva Rodovias S.A."
        assert len(body["itens"]) == 1
        # fallback resolvido
        assert body["resolvidos"]["clausula_tributaria"] == "cláusula default"
        # garantia_texto montado a partir dos resolvidos
        assert "5" in body["garantia_texto"]
        assert "60 dias" in body["garantia_texto"]

    def test_proposta_404_orcamento_inexistente(self):
        r = client.get("/api/v1/orcamentos/999999/proposta")
        assert r.status_code == 404, r.text

    def test_proposta_sem_config_usa_literais(self, db_session):
        # sem nenhum PUT /config: _get_config NÃO é chamado aqui, então config pode ser None.
        # garantimos comportamento: endpoint responde 200 e resolvidos vem vazio/seguro.
        orc_id, _ = _criar_orcamento_com_item(db_session, sufixo="prop2")
        r = client.get(f"/api/v1/orcamentos/{orc_id}/proposta")
        assert r.status_code == 200, r.text
        body = r.json()
        # sem config no banco → config None, resolvidos {} (ver impl)
        assert body["config"] is None
        assert body["resolvidos"] == {}
```

Nota sobre `test_proposta_sem_config_usa_literais`: o endpoint consulta `ConfigSistema` direto (não usa `_get_config`, que criaria a linha singleton). Se nenhum `PUT /config` rodou neste teste isolado, a tabela está vazia → `config is None` → `resolvidos == {}`. Esse é o contrato definido no spec (linha `montar_proposta(orc, config) if config else {}`).

- [ ] **Step 2: Rodar e confirmar falha**

Run: `py -m pytest tests/test_proposta_for077.py::TestEndpointProposta -v`
Expected: FAIL — rota `/proposta` não existe (404 onde se espera 200; o teste de 404-inexistente pode passar por coincidência, ignore).

- [ ] **Step 3: Adicionar o endpoint GET proposta**

Em `backend/routers/orcamento_routers.py`, adicione após `obter_orcamento` (o GET `/orcamentos/{id}`). Importe `ConfigSistema` e `montar_proposta` dentro da função (padrão de import local já usado no arquivo):

```python
@router.get("/orcamentos/{id}/proposta", tags=["orcamentos"])
def obter_proposta(id: int, db: Session = Depends(get_db)) -> dict:
    """FOR-077 — monta a proposta resolvendo fallback ConfigSistema.

    Fonte única consumida por F2 (editor) e F3 (documento/PDF).
    """
    from backend.models.extra_models import ConfigSistema
    from backend.schemas.extra_schemas import ConfigSistemaRead
    from backend.services.proposta_fallback import montar_proposta

    orc = _get_or_404(db, Orcamento, id)
    config = db.query(ConfigSistema).order_by(ConfigSistema.id).first()
    itens = (
        db.query(OrcamentoItem).filter(OrcamentoItem.orcamento_id == id).all()
    )
    cliente = db.get(Cliente, orc.cliente_id)
    resolvidos = montar_proposta(orc, config) if config else {}
    return {
        "orcamento": OrcamentoRead.model_validate(orc).model_dump(mode="json"),
        "config": (
            ConfigSistemaRead.model_validate(config).model_dump(mode="json")
            if config
            else None
        ),
        "cliente": (
            ClienteRead.model_validate(cliente).model_dump(mode="json")
            if cliente
            else None
        ),
        "itens": [
            OrcamentoItemRead.model_validate(i).model_dump(mode="json") for i in itens
        ],
        "resolvidos": resolvidos,
        "garantia_texto": (
            f"Retenção de {resolvidos.get('garantia_retencao_pct')}%, com devolução "
            f"em {resolvidos.get('garantia_devolucao_dias')} dias após o termo de "
            "encerramento."
            if resolvidos
            else ""
        ),
    }
```

Nota: `garantia_texto` só é montado quando há `resolvidos` (config presente); sem config devolve `""` — coerente com `resolvidos == {}`.

- [ ] **Step 4: Rodar a classe e confirmar verde**

Run: `py -m pytest tests/test_proposta_for077.py::TestEndpointProposta -v`
Expected: 3 PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/routers/orcamento_routers.py tests/test_proposta_for077.py
git commit -m "feat(proposta): GET /orcamentos/{id}/proposta com fallback resolvido (FOR-077)"
```

---

## Task 6: Seed FOR-077 no `ConfigSistema`

**Files:**
- Modify: `backend/seeds.py:290-302` (função `seed_extra`)
- Test: `tests/test_proposta_for077.py`

O teste do seed roda `seed_extra` numa sessão de teste e confere os defaults. Os textos longos (cláusula tributária, reajustamento, declarações) ficam em constantes no topo de `seeds.py` para legibilidade.

- [ ] **Step 1: Escrever o teste do seed**

Adicione ao arquivo de teste:

```python
class TestSeedFor077:
    def test_seed_extra_popula_config_for077(self, db_session):
        from backend.models.extra_models import ConfigSistema
        from backend.seeds import seed_extra

        seed_extra(db_session)
        db_session.commit()
        cfg = db_session.query(ConfigSistema).order_by(ConfigSistema.id).first()
        assert cfg is not None
        assert cfg.cnpj == "20.945.724/0001-15"
        assert cfg.banco == "Bradesco"
        assert cfg.agencia == "0110"
        assert cfg.conta_corrente == "0287852-6"
        assert cfg.diretor_cpf == "277.540.838-92"
        assert cfg.contato_comercial_nome == "Milaini Carvalho Miranda"
        assert cfg.contato_comercial_email == "comercial@altanoroeste.com.br"
        assert cfg.garantia_retencao_padrao_pct == Decimal("5")
        assert cfg.garantia_devolucao_padrao_dias == 60
        assert "IBS/CBS" in cfg.clausula_tributaria_padrao
        assert "IPCA" in cfg.reajustamento_padrao
        # declaracoes_padrao tem 12 bullets separados por \n
        assert cfg.declaracoes_padrao.count("\n") >= 11
```

- [ ] **Step 2: Rodar e confirmar falha**

Run: `py -m pytest tests/test_proposta_for077.py::TestSeedFor077 -v`
Expected: FAIL — `cfg.cnpj` é None (seed atual só passa `nome_empresa`).

- [ ] **Step 3: Adicionar constantes de texto e atualizar `seed_extra`**

No topo de `backend/seeds.py` (após os imports, junto de outras constantes de módulo se houver), adicione:

```python
_FOR077_CLAUSULA_TRIBUTARIA = (
    "Os preços apresentados nesta proposta contemplam a carga tributária atual "
    "exigida pela legislação pertinente. Eventuais contratos com execuções ou "
    "vigência posterior a 31/12/2026 estarão sujeitos a revisão e renegociação "
    "obrigatória, visando o repasse dos impactos tributários causados pela "
    "transição da Reforma Tributária (IBS/CBS)."
)

_FOR077_REAJUSTAMENTO = (
    "Os preços poderão ser atualizados anualmente, mediante aplicação do índice de "
    "menor variação acumulada no período entre o Índice Nacional de Preços ao "
    "Consumidor Amplo – IPCA ou o Índice Geral de Preços do Mercado – IGPM. A "
    "data-base para fins de reajuste será a data de assinatura do contrato."
)

_FOR077_DECLARACOES = "\n".join(
    [
        "Que respeita integralmente as condições estabelecidas na TR.ENG.{numero}.",
        "Que possui conhecimento das Políticas de Meio Ambiente, corporativa sobre "
        "Mudanças Climáticas e de Responsabilidade Social.",
        "Que possui conhecimento e que cumpre a legislação anticorrupção e, em "
        "especial a Lei 12.846/13;",
        "Que executará os serviços de acordo com o projeto e suas modificações, ordem "
        "de serviço, e de acordo com as normas e especificações técnicas;",
        "Que se obriga a dispor, para emprego imediato, de todos os recursos "
        "necessários para a execução dos serviços contratados, no prazo estipulado, "
        "sem custos adicionais;",
        "Que tem pleno conhecimento das condições locais necessárias para a formação "
        "dos preços;",
        "Que não possui em seu quadro de empregados, menor de 18 anos em trabalho "
        "noturno, insalubre ou perigoso, e, ainda, não possuir empregado menor de 16 "
        "anos;",
        "Que a proponente não mantém qualquer relação ou vínculo de qualquer natureza "
        "com a Contratante ou empresas do mesmo Conglomerado econômico a qual "
        "pertence;",
        "Que conhece o Código de Ética e Integridade, constantes nos documentos "
        "recebidos.",
        "Se comprometer a estar instalado e pronto para o início dos serviços no prazo "
        "imposto no termo de referência;",
        "Que em seu preço estão inclusas todas as despesas com a prestação dos "
        "serviços, equipamentos, mão-de-obra, tributos, encargos, impostos, lucro, e "
        "as demais despesas diretas e indiretas que possam recair sobre a presente "
        "prestação de serviços;",
        "Que executará todos os serviços de acordo com o preço e o prazo, estipulados "
        "nesta carta;",
        "Que tem pleno conhecimento sobre a retenção de X% das medições sobre o valor "
        "bruto da medição a título de caução.",
    ]
)
```

Verifique que `Decimal` está importado no topo de `seeds.py` (`from decimal import Decimal`); se não estiver, adicione. Depois substitua a linha `db.add(ConfigSistema(nome_empresa="ALTA NOROESTE"))` em `seed_extra` por:

```python
    db.add(
        ConfigSistema(
            nome_empresa="ALTA NOROESTE",
            cnpj="20.945.724/0001-15",
            banco="Bradesco",
            agencia="0110",
            conta_corrente="0287852-6",
            diretor_cpf="277.540.838-92",
            contato_comercial_nome="Milaini Carvalho Miranda",
            contato_comercial_funcao="Comercial",
            contato_comercial_fone="(18) 99683-6472",
            contato_comercial_email="comercial@altanoroeste.com.br",
            garantia_retencao_padrao_pct=Decimal("5"),
            garantia_devolucao_padrao_dias=60,
            clausula_tributaria_padrao=_FOR077_CLAUSULA_TRIBUTARIA,
            reajustamento_padrao=_FOR077_REAJUSTAMENTO,
            declaracoes_padrao=_FOR077_DECLARACOES,
        )
    )
```

- [ ] **Step 4: Rodar e confirmar verde**

Run: `py -m pytest tests/test_proposta_for077.py::TestSeedFor077 -v`
Expected: 1 PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/seeds.py tests/test_proposta_for077.py
git commit -m "feat(seed): ConfigSistema populado com defaults FOR-077"
```

---

## Task 7: Suíte completa + regressão

**Files:** (nenhum novo — verificação)

- [ ] **Step 1: Rodar a suíte FOR-077 inteira**

Run: `py -m pytest tests/test_proposta_for077.py -v`
Expected: todos PASS (PATCH 4 + Config 3 + Montar 3 + Endpoint 3 + Seed 1 = 14).

- [ ] **Step 2: Rodar a suíte de testes completa (regressão — inclui os 2 que o handoff cita: test_deletar_bdi, test_deletar_ficha_equipe)**

Run: `py -m pytest -q`
Expected: tudo verde. Se `test_deletar_bdi` / `test_deletar_ficha_equipe` falharem, é regressão pré-existente (handoff diz que o parceiro já corrigiu com `ff0e6cb`) — confirme `git log --oneline | findstr soft-delete` antes de investigar.

- [ ] **Step 3: Commit final (se houver ajustes) ou seguir para F2**

Se a suíte passou sem mudanças adicionais, F1 está completa. Atualize o handoff marcando F1 como concluída e apontando F2 (editor) como próxima fase.

```bash
git add docs/superpowers/HANDOFF-proposta-for077.md
git commit -m "docs: handoff FOR-077 — F1 backend concluída, próxima F2 editor"
```

---

## Self-Review (cobertura do spec)

| Requisito do spec | Task que cobre |
|---|---|
| 1.1 Schema `OrcamentoItemDescricaoPatch` (`extra=forbid`) | Task 1 |
| 1.1 PATCH grava `descricao_cliente`, guard rascunho, 404 item, 422 extra | Task 2 |
| 1.2 PUT /config `exclude_unset` (18 campos + limpar via null) | Task 3 |
| 1.4 Helper `montar_proposta` fallback + literais | Task 4 |
| 1.4 Endpoint `GET /orcamentos/{id}/proposta` + `garantia_texto` | Task 5 |
| 1.3 Seed FOR-077 no `ConfigSistema` | Task 6 |
| 1.5 Testes TDD de tudo | Tasks 1-6 (teste antes da impl em cada) + Task 7 regressão |

**Desvios conscientes do spec (corrigidos no plano, não no spec):**
- Spec dizia "17 campos" no config; o real é 18 (inclui `nome_empresa`). Plano usa `exclude_unset` que cobre todos automaticamente — contagem não importa.
- Spec usava `db.get(OrcamentoItem, item_id)` + checagem manual no PATCH; plano usa o padrão query-filter já existente no arquivo (consistência).
- `seeds_prod.py` não cria `ConfigSistema` (verificado) — fora de escopo, ao contrário do "idem se aplicável" do spec.
- `garantia_texto` devolve `""` quando não há config (em vez de texto com `None`), coerente com `resolvidos == {}`.
```