# Orçamento + Proposta Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refinar o editor de orçamento (Enter→Calcular, fixar valores, preço unit final), adicionar diretor comercial e unidade-do-Produto no backend, e redesenhar a proposta comercial (cabeçalho/rodapé, edição inline, QR WhatsApp).

**Architecture:** Backend FastAPI/SQLAlchemy ganha 4 campos de diretor no ConfigSistema singleton, um campo texto_topo_proposta no Orcamento, e um ajuste cirúrgico no resolver de unidade. Frontend React redesenha proposta.tsx (3-col header, footer A, edição inline gravando descricao_cliente/textos), gera QR via qrcode.react, e melhora o editor. Motor de cálculo intocado.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy 2, pytest; TypeScript, React 19, react-router, qrcode.react v4, shadcn ui.

**Spec:** `docs/superpowers/specs/2026-06-12-orcamento-proposta-design.md`

---

## File Structure

- `backend/models/extra_models.py` — 4 campos diretor em ConfigSistema.
- `backend/models/orcamento_models.py` — texto_topo_proposta.
- `backend/schemas/extra_schemas.py` — diretor em ConfigSistemaRead/Update.
- `backend/schemas/orcamento_schemas.py` — texto_topo_proposta em Update/Read.
- `backend/routers/extra_routers.py` — PUT /config seta diretor.
- `backend/routers/orcamento_routers.py` — unidade do Produto no ramo ficha_produto.
- `tests/test_orcamentos.py` + `tests/test_config_diretor.py` (novo).
- `frontend/package.json` — qrcode.react.
- `frontend/app/routes/parametros.tsx` — inputs diretor em EmpresaConfig.
- `frontend/app/routes/proposta.tsx` — redesign + edição inline + QR.
- `frontend/app/routes/orcamentos.$id.tsx` — Enter→Calcular + reforço de fixar valores.

---

## Task 1: Backend — diretor comercial no ConfigSistema (TDD)

**Files:**
- Modify: `backend/models/extra_models.py`, `backend/schemas/extra_schemas.py`, `backend/routers/extra_routers.py`
- Create: `tests/test_config_diretor.py`

- [ ] **Step 1: Teste (falha primeiro)**

Criar `tests/test_config_diretor.py`. Replicar a infra de TestClient in-memory (mesmo padrão de tests/test_notificacoes.py: engine StaticPool, override_get_db, sponsor client, autouse setup_db). Config é singleton lazy-criado, então o GET cria o registro.

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.auth import criar_token
from backend.database import Base, get_db
from backend.main import app

engine_test = create_engine(
    "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
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


class TestConfigDiretor:
    def test_get_inclui_campos_diretor(self):
        d = client.get("/api/v1/config").json()
        for chave in ("diretor_nome", "diretor_funcao", "diretor_telefone", "diretor_email"):
            assert chave in d

    def test_put_persiste_diretor(self):
        r = client.put("/api/v1/config", json={
            "diretor_nome": "Carlos Mendes",
            "diretor_funcao": "Diretor Comercial",
            "diretor_telefone": "(41) 9 8888-7777",
            "diretor_email": "carlos@empresa.com",
        })
        assert r.status_code == 200
        d = r.json()
        assert d["diretor_nome"] == "Carlos Mendes"
        # persistiu (novo GET)
        d2 = client.get("/api/v1/config").json()
        assert d2["diretor_funcao"] == "Diretor Comercial"
        assert d2["diretor_email"] == "carlos@empresa.com"
```

- [ ] **Step 2: Rodar — espera FAIL (campos não existem)**

Run: `py -m pytest tests/test_config_diretor.py -v` → FAIL.

- [ ] **Step 3: Model — 4 campos em ConfigSistema**

Em `backend/models/extra_models.py`, na classe `ConfigSistema`, após `logo_path`:
```python
    diretor_nome: Mapped[str | None] = mapped_column(String(200), nullable=True)
    diretor_funcao: Mapped[str | None] = mapped_column(String(100), nullable=True)
    diretor_telefone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    diretor_email: Mapped[str | None] = mapped_column(String(150), nullable=True)
```
(`String`, `Mapped`, `mapped_column` já importados.)

- [ ] **Step 4: Schemas — diretor em Read/Update**

Em `backend/schemas/extra_schemas.py`:
`ConfigSistemaRead` (após `logo_path: str | None`):
```python
    diretor_nome: str | None = None
    diretor_funcao: str | None = None
    diretor_telefone: str | None = None
    diretor_email: str | None = None
```
`ConfigSistemaUpdate` (após `nome_empresa: str | None = None`):
```python
    diretor_nome: str | None = None
    diretor_funcao: str | None = None
    diretor_telefone: str | None = None
    diretor_email: str | None = None
```

- [ ] **Step 5: Router — PUT /config seta diretor**

Em `backend/routers/extra_routers.py`, na função `atualizar_config`, após `if payload.nome_empresa is not None: cfg.nome_empresa = payload.nome_empresa`:
```python
    for campo in ("diretor_nome", "diretor_funcao", "diretor_telefone", "diretor_email"):
        valor = getattr(payload, campo)
        if valor is not None:
            setattr(cfg, campo, valor)
```

- [ ] **Step 6: Rodar — espera PASS**

Run: `py -m pytest tests/test_config_diretor.py -v` → 2 pass.
Smoke: `python -c "import backend.main; print('ok')"`.

- [ ] **Step 7: Commit**

```bash
git add backend/models/extra_models.py backend/schemas/extra_schemas.py backend/routers/extra_routers.py tests/test_config_diretor.py
git commit -m "feat(D): diretor comercial no ConfigSistema + testes"
```

---

## Task 2: Backend — unidade do Produto + texto_topo_proposta (TDD)

**Files:**
- Modify: `backend/routers/orcamento_routers.py`, `backend/models/orcamento_models.py`, `backend/schemas/orcamento_schemas.py`
- Modify: `tests/test_orcamentos.py`

- [ ] **Step 1: Teste de texto_topo_proposta (falha primeiro)**

Em `tests/test_orcamentos.py`, adicionar ao final um teste de round-trip do novo campo (reusa fixtures `client`, `cliente_id`):
```python
class TestTextoTopoProposta:
    def test_round_trip(self, cliente_id):
        r = client.post("/api/v1/orcamentos", json={
            "numero": "TT-1", "cliente_id": cliente_id, "uf_execucao": "PR",
        })
        oid = r.json()["id"]
        r2 = client.put(f"/api/v1/orcamentos/{oid}", json={"texto_topo_proposta": "Apresentação da proposta"})
        assert r2.status_code == 200
        assert r2.json()["texto_topo_proposta"] == "Apresentação da proposta"
```
Nota: o ajuste de unidade do ramo `ficha_produto` é difícil de testar isoladamente sem fixtures de Produto+UnidadeMedida+ItemFicha. Validar por leitura + um teste leve se as fixtures existentes permitirem; caso contrário, cobrir só `texto_topo_proposta` aqui e validar a unidade por review. NÃO inventar fixtures complexas.

- [ ] **Step 2: Rodar — espera FAIL (campo não existe)**

Run: `py -m pytest tests/test_orcamentos.py::TestTextoTopoProposta -v` → FAIL.

- [ ] **Step 3: Model — texto_topo_proposta**

Em `backend/models/orcamento_models.py`, classe `Orcamento`, junto de `texto_livre_proposta`:
```python
    texto_topo_proposta: Mapped[str | None] = mapped_column(Text, nullable=True)
```
(`Text` já importado.)

- [ ] **Step 4: Schema — texto_topo_proposta em Update/Read**

Em `backend/schemas/orcamento_schemas.py`:
`OrcamentoUpdate` (junto de `texto_livre_proposta`):
```python
    texto_topo_proposta: str | None = None
```
`OrcamentoRead` (junto de `texto_livre_proposta`):
```python
    texto_topo_proposta: str | None = None
```

- [ ] **Step 5: Unidade do Produto no ramo ficha_produto**

Em `backend/routers/orcamento_routers.py`, na função `_custo_e_unidade_da_ficha`, o ramo `if body.ficha_produto_id:` hoje retorna `Decimal(f.custo_total), f.unidade, "produto"`. Ajustar para preferir a unidade do cadastro Produto quando houver um Produto vinculado a essa ficha. Substituir esse `return` por:
```python
        unidade = f.unidade
        prod_vinc = (
            db.query(Produto)
            .join(ItemFicha, ItemFicha.produto_id == Produto.id)
            .filter(ItemFicha.ficha_produto_id == f.id)
            .first()
        )
        if prod_vinc and prod_vinc.unidade_id:
            um = db.get(UnidadeMedida, prod_vinc.unidade_id)
            if um:
                unidade = um.sigla
        return Decimal(f.custo_total), unidade, "produto"
```
CONFERIR que `Produto`, `ItemFicha`, `UnidadeMedida` já estão importados no arquivo (o ramo produto_id acima já usa `UnidadeMedida` e `ItemFicha`; `Produto` também). Se algum faltar, adicionar o import.

- [ ] **Step 6: Rodar — espera PASS + sem regressão**

Run: `py -m pytest tests/test_orcamentos.py -q` → todos passam.
Smoke: `python -c "import backend.routers.orcamento_routers; print('ok')"`.

- [ ] **Step 7: Commit**

```bash
git add backend/models/orcamento_models.py backend/schemas/orcamento_schemas.py backend/routers/orcamento_routers.py tests/test_orcamentos.py
git commit -m "feat(D): unidade do Produto em ficha_produto + texto_topo_proposta"
```

---

## Task 3: Frontend — diretor na aba Empresa (Parâmetros)

**Files:**
- Modify: `frontend/app/routes/parametros.tsx`

- [ ] **Step 1: Ler EmpresaConfig**

`EmpresaConfig` (~linha 149) tem estado `nome` + form de logo, salvando via `configApi.update({ nome_empresa })`. Adicionar 4 campos do diretor.

- [ ] **Step 2: Estado + load + save dos campos diretor**

No componente `EmpresaConfig`, adicionar estado:
```tsx
  const [diretor, setDiretor] = useState({ nome: "", funcao: "", telefone: "", email: "" })
```
No `load()` (após `setNome(c.nome_empresa ?? "")`):
```tsx
      setDiretor({
        nome: c.diretor_nome ?? "", funcao: c.diretor_funcao ?? "",
        telefone: c.diretor_telefone ?? "", email: c.diretor_email ?? "",
      })
```
Na função que salva (a `salvarNome`/equivalente), trocar o payload de `configApi.update({ nome_empresa: nome })` para incluir o diretor:
```tsx
      const c = await configApi.update({
        nome_empresa: nome,
        diretor_nome: diretor.nome || null,
        diretor_funcao: diretor.funcao || null,
        diretor_telefone: diretor.telefone || null,
        diretor_email: diretor.email || null,
      })
```

- [ ] **Step 3: Inputs do diretor na UI**

Dentro do `EmpresaConfig`, adicionar uma seção (após o campo de nome da empresa, antes/depois do logo — seguir o padrão de markup de campo já existente no componente, com `<Label>` + `<Input>`):
```tsx
      <div className="border-t pt-4">
        <div className="text-muted-foreground text-[0.625rem] font-semibold uppercase tracking-wider mb-2">Diretor Comercial (Aprovado por)</div>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div className="flex flex-col gap-1">
            <Label>Nome</Label>
            <Input value={diretor.nome} onChange={(e) => setDiretor((d) => ({ ...d, nome: e.target.value }))} />
          </div>
          <div className="flex flex-col gap-1">
            <Label>Função</Label>
            <Input value={diretor.funcao} onChange={(e) => setDiretor((d) => ({ ...d, funcao: e.target.value }))} />
          </div>
          <div className="flex flex-col gap-1">
            <Label>Telefone</Label>
            <Input value={diretor.telefone} onChange={(e) => setDiretor((d) => ({ ...d, telefone: e.target.value }))} />
          </div>
          <div className="flex flex-col gap-1">
            <Label>E-mail</Label>
            <Input value={diretor.email} onChange={(e) => setDiretor((d) => ({ ...d, email: e.target.value }))} />
          </div>
        </div>
      </div>
```
Confirmar que `Label` e `Input` já estão importados em parametros.tsx (estão — EmpresaConfig já os usa). O botão "Salvar" existente já dispara o save com o novo payload.

- [ ] **Step 4: Self-check**

Sem node_modules → sem typecheck. Confirmar: `configApi.update` aceita objeto arbitrário (sim, `(body) => api.put("/config", body)`); imports presentes; sem cor nova.

- [ ] **Step 5: Commit**

```bash
git add frontend/app/routes/parametros.tsx
git commit -m "feat(D): diretor comercial na aba Empresa dos Parametros"
```

---

## Task 4: Frontend — qrcode.react + editor (Enter→Calcular, fixar valores)

**Files:**
- Modify: `frontend/package.json`, `frontend/app/routes/orcamentos.$id.tsx`

- [ ] **Step 1: Add dep qrcode.react (usada na Task 5)**

Em `frontend/package.json` dependencies, adicionar (React 19 compatível):
```json
    "qrcode.react": "^4.2.0",
```

- [ ] **Step 2: Enter→Calcular no editor**

Em `frontend/app/routes/orcamentos.$id.tsx`, identificar os `<Input>` editáveis (quantidade, margem, desconto) — eles usam `onBlur`/`salvarCampo`/`salvarDesconto`. Adicionar a cada um `onKeyDown`:
```tsx
              onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); (e.target as HTMLInputElement).blur(); calcular() } }}
```
O `.blur()` força o salvamento do campo (onBlur) antes do recálculo. Só aplicar nos inputs que existem quando `!readonly` (eles já só renderizam nesse caso). NÃO adicionar em inputs read-only.

- [ ] **Step 3: Reforçar "fixar valores" — preço unitário final na coluna**

Localizar a coluna de preço unitário na tabela de itens. Hoje pode exibir `it.preco_venda_unitario`. Trocar para preferir o final (pós-desconto):
```tsx
{fmtBRL(it.preco_venda_unitario_final || it.preco_venda_unitario)}
```
Isso garante que o preço unitário reflete o desconto após o cálculo (e persiste no reload, pois vem do item). Os totais headline (`total`, `mlr`) já caem para `orc.total_proposta`/`orc.margem_liquida_real` persistidos quando `resultado` é null (linhas ~224-228) — manter esse fallback.

- [ ] **Step 4: Self-check**

Sem typecheck. Confirmar: `calcular` está no escopo do onKeyDown; `preco_venda_unitario_final` existe no item (existe — ItemRead). Sem cor nova.

- [ ] **Step 5: Commit**

```bash
git add frontend/package.json frontend/app/routes/orcamentos.$id.tsx
git commit -m "feat(D): editor Enter->Calcular + preco unitario final persistido"
```

---

## Task 5: Frontend — proposta: cabeçalho/rodapé redesenhados + QR

**Files:**
- Modify: `frontend/app/routes/proposta.tsx`

- [ ] **Step 1: Imports — QR + config diretor já vem em config**

No topo de `proposta.tsx`, adicionar:
```tsx
import { QRCodeSVG } from "qrcode.react"
```
`config` já é carregado via `configApi.get()` e agora traz `diretor_*`. `orc` agora traz `texto_topo_proposta`.

- [ ] **Step 2: Helper de telefone → wa.me**

Adicionar no corpo do componente (antes do return), um helper:
```tsx
  const waLink = (tel?: string) => {
    const dig = (tel ?? "").replace(/\D/g, "")
    if (!dig) return null
    return `https://wa.me/${dig.startsWith("55") ? dig : "55" + dig}`
  }
  const waOrc = waLink(orcamentista?.telefone)
```

- [ ] **Step 3: Cabeçalho 3 colunas (substitui o atual)**

Substituir o bloco do cabeçalho atual (a `<div className="flex items-start justify-between border-b pb-5">...</div>` que mostra logo+orcOS à esquerda e "Proposta {numero}" à direita) por:
```tsx
        <div className="grid grid-cols-3 items-center border-b pb-5">
          <div className="flex items-center">
            {config?.logo_path ? (
              <img src={config.logo_path} alt="logo" className="h-12 max-w-[160px] object-contain" />
            ) : (
              <div className="bg-primary text-primary-foreground flex size-12 items-center justify-center rounded">
                <svg viewBox="0 0 24 24" className="size-6 fill-current"><path d="M12 2L2 7l10 5 10-5-10-5zm0 10L2 7v10l10 5 10-5V7l-10 5z" /></svg>
              </div>
            )}
          </div>
          <div className="text-center text-lg font-bold tracking-wide uppercase">Proposta Comercial</div>
          <div className="text-right text-xs">
            {orc.obra && <div className="font-semibold">{orc.obra}</div>}
            <div className="text-muted-foreground">Proposta {orc.numero} · v{orc.versao ?? 1}</div>
            <div className="text-muted-foreground">Emissão: {hoje}</div>
          </div>
        </div>
```
(Remove "orcOS" e o nome da empresa do cabeçalho, conforme spec.)

- [ ] **Step 4: Texto livre do topo (entre cabeçalho/cliente e itens)**

Após o bloco de dados do cliente/orçamentista e ANTES do corpo de itens (`{BLOCOS_PROPOSTA.map(...)}`), adicionar a renderização/edição do `texto_topo_proposta`. Edição só quando editável:
```tsx
        {(orc.texto_topo_proposta || editavel) && (
          <div className="border-b py-3">
            {editavel ? (
              <textarea
                defaultValue={orc.texto_topo_proposta ?? ""}
                placeholder="Texto de apresentação (aparece antes dos itens)…"
                onBlur={(e) => salvarTextoOrc("texto_topo_proposta", e.target.value)}
                className="text-muted-foreground w-full resize-none rounded border bg-transparent p-2 text-xs"
                rows={2}
              />
            ) : (
              <p className="text-muted-foreground text-xs whitespace-pre-wrap">{orc.texto_topo_proposta}</p>
            )}
          </div>
        )}
```
Onde `editavel` e `salvarTextoOrc` são definidos no Step 6.

- [ ] **Step 5: Descrição de item editável (grava descricao_cliente)**

Na célula de descrição de cada item (hoje `{it.descricao_cliente || it.descricao}`), quando `editavel`, tornar editável gravando `descricao_cliente`:
```tsx
                      <TableCell className="font-medium">
                        {editavel ? (
                          <input
                            defaultValue={it.descricao_cliente ?? it.descricao}
                            onBlur={(e) => salvarDescricaoItem(it.id, e.target.value)}
                            className="w-full rounded border bg-transparent px-1 py-0.5 text-xs"
                          />
                        ) : (
                          it.descricao_cliente || it.descricao
                        )}
                      </TableCell>
```
QTD, Un, Preço Unit, Preço Total permanecem read-only (não tocar).

- [ ] **Step 6: Estado/handlers de edição + editavel**

No corpo do componente, adicionar:
```tsx
  const editavel = orc ? ["rascunho", "reprovado"].includes(orc.status) : false

  async function salvarDescricaoItem(itemId: number, valor: string) {
    try {
      await orcamentoApi.updateItem(orcId, itemId, { descricao_cliente: valor })
      setItens((arr) => arr.map((i) => (i.id === itemId ? { ...i, descricao_cliente: valor } : i)))
    } catch (e: any) {
      toast.error(`Erro: ${e.message}`)
    }
  }

  async function salvarTextoOrc(campo: string, valor: string) {
    try {
      await orcamentoApi.update(orcId, { [campo]: valor })
      setOrc((o: any) => ({ ...o, [campo]: valor }))
    } catch (e: any) {
      toast.error(`Erro: ${e.message}`)
    }
  }
```
CONFERIR que `orcamentoApi.updateItem` e `orcamentoApi.update` existem (existem — usados no editor). `toast` já importado.

- [ ] **Step 7: Texto livre do rodapé editável (reusa texto_livre_proposta)**

O bloco que hoje renderiza `orc.texto_livre_proposta` (entre o total e o rodapé): quando `editavel`, trocar por um `<textarea>` análogo ao Step 4, gravando `texto_livre_proposta` via `salvarTextoOrc`. Quando não-editável, manter o `<p>` atual.

- [ ] **Step 8: Rodapé opção A — Aprovado por (diretor) + Elaborado por (orçamentista) + QR**

Substituir o bloco de rodapé atual (`{/* Rodapé: dados do orçamentista */}` ... a `<div>` com nome/função/telefone do orçamentista) por:
```tsx
        <div className="mt-8 flex items-start justify-between border-t pt-4 text-xs">
          <div>
            <div className="text-muted-foreground mb-1 text-[0.625rem] font-semibold uppercase">Aprovado por</div>
            <div className="font-semibold">{config?.diretor_nome ?? "—"}</div>
            {config?.diretor_funcao && <div className="text-muted-foreground">{config.diretor_funcao}</div>}
            {config?.diretor_telefone && <div className="text-muted-foreground">{config.diretor_telefone}</div>}
            {config?.diretor_email && <div className="text-muted-foreground">{config.diretor_email}</div>}
          </div>
          <div className="flex items-start gap-3">
            <div className="text-right">
              <div className="text-muted-foreground mb-1 text-[0.625rem] font-semibold uppercase">Elaborado por</div>
              <div className="font-semibold">{orcamentista?.nome_completo ?? "—"}</div>
              {orcamentista?.funcao && <div className="text-muted-foreground">{orcamentista.funcao}</div>}
              {orcamentista?.telefone && <div className="text-muted-foreground">{orcamentista.telefone}</div>}
            </div>
            {waOrc && (
              <QRCodeSVG value={waOrc} size={60} level="M" className="shrink-0" />
            )}
          </div>
        </div>
```

- [ ] **Step 9: Manter "Desenvolvido por Viaxis Tech HUB"**

O `<p>` "Desenvolvido por Viaxis Tech HUB" permanece como está, abaixo do rodapé.

- [ ] **Step 10: Self-check**

Sem typecheck. Confirmar por leitura: `QRCodeSVG` importado de `qrcode.react`; `editavel`/`salvarDescricaoItem`/`salvarTextoOrc`/`waOrc` definidos antes do uso; `config.diretor_*` e `orc.texto_topo_proposta` lidos; preços/qtd/totais NÃO editáveis; sem cor nova (tokens existentes). Grep: nenhum "orcOS" remanescente no cabeçalho da proposta.

- [ ] **Step 11: Commit**

```bash
git add frontend/app/routes/proposta.tsx
git commit -m "feat(D): proposta redesenhada (header 3-col, rodape A, edicao inline, QR)"
```

---

## Self-Review (preenchido)

**Spec coverage:**
- Enter→Calcular → Task 4 Step 2. ✓
- Fixar valores (resumo dos persistidos) → Task 4 Step 3 (preço unit final + fallback existente de total/mlr). ✓
- Preço unitário dinâmico → Task 4 Step 3. ✓
- Diretor no ConfigSistema → Task 1. ✓
- Unidade do Produto (ficha_produto) → Task 2 Step 5. ✓
- texto_topo_proposta → Task 2 Steps 3-4 + Task 5 Step 4. ✓
- Cabeçalho 3-col (logo/PROPOSTA COMERCIAL/nome+versão+data) → Task 5 Step 3. ✓
- Rodapé A (diretor + orçamentista + QR) → Task 5 Step 8. ✓
- 2 textos livres → Task 5 Steps 4 e 7. ✓
- Descrições editáveis (descricao_cliente) → Task 5 Step 5. ✓
- Trava por status → Task 5 Step 6 (`editavel`). ✓
- QR via qrcode.react → Task 4 Step 1 (dep) + Task 5 Steps 1,2,8. ✓
- Diretor na aba Empresa → Task 3. ✓
- Manter Viaxis → Task 5 Step 9. ✓
- Sem cor nova → tokens existentes em todas as tasks frontend. ✓
- PDF fora de escopo → não há task de PDF (correto). ✓

**Placeholder scan:** Os "CONFERIR/identificar/localizar" são verificações concretas com instrução de ajuste. Cada step de código mostra o código. A nota do Task 2 Step 1 sobre não inventar fixtures complexas para a unidade é uma decisão de escopo de teste explícita (cobre por review), não um placeholder. Aceitável.

**Type consistency:** `salvarDescricaoItem(itemId, valor)`, `salvarTextoOrc(campo, valor)`, `editavel`, `waLink/waOrc` consistentes entre os steps da Task 5. `diretor_nome/funcao/telefone/email` idênticos entre model (Task 1), schema (Task 1), router (Task 1), parametros (Task 3) e proposta (Task 5). `texto_topo_proposta` consistente entre Task 2 e Task 5. ✓

## Nota sobre versões / ambiente

- React 19 → `qrcode.react` v4 é compatível (exporta `QRCodeSVG`). Se `npm install` resolver outra versão, garantir compat com React 19 e que o named export `QRCodeSVG` existe.
- pytest roda via `py -m pytest`. Frontend sem typecheck no sandbox (sem node_modules) — validar por review/grep; typecheck real no ambiente do projeto após `npm install` (necessário também por causa das deps de B: react-day-picker/date-fns, e agora qrcode.react).
