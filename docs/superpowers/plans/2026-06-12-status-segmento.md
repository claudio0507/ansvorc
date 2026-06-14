# Status + Segmento + data_limite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Evoluir status do orçamento para funil de 6 estados, adicionar segmentos multi-valor (classificação) e a coluna `data_limite`, sem introduzir cores novas no UI.

**Architecture:** Backend SQLAlchemy + FastAPI; status como slug minúsculo guardado por máquina de transições; segmentos em tabela de junção `orcamento_segmentos`. Frontend React Router + componentes shadcn existentes. DB descartável — sem migration, só seed.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy 2 (Mapped), Pydantic v2, pytest; TypeScript, React Router, sonner toast.

**Spec:** `docs/superpowers/specs/2026-06-12-status-segmento-design.md`

---

## File Structure

- `backend/models/extra_models.py` — novo model `OrcamentoSegmento`.
- `backend/models/orcamento_models.py` — coluna `data_limite`, relationship `segmentos`.
- `backend/schemas/orcamento_schemas.py` — `_STATUS_VALIDOS` (6), `segmentos`/`data_limite` em Create/Update/Read.
- `backend/routers/orcamento_routers.py` — `_TRANSICOES_STATUS` (6), `_guard_rascunho`→lógica editável, persistência de segmentos no create/update, remoção de `/aprovar`.
- `backend/seeds.py` — orçamentos exemplo com status novos + segmentos.
- `frontend/app/components/status-badge.tsx` — 6 estados, variantes existentes.
- `frontend/app/lib/api.ts` — passar campos novos (sem rota nova).
- `frontend/app/routes/orcamentos.novo.tsx`, `orcamentos.$id.tsx` — form + dropdown status.
- `tests/test_status_transicoes.py` (novo), `tests/test_orcamentos.py` (estender).

---

## Task 1: Model OrcamentoSegmento + data_limite

**Files:**
- Modify: `backend/models/extra_models.py`
- Modify: `backend/models/orcamento_models.py`

- [ ] **Step 1: Adicionar `data_limite` e relationship em `Orcamento`**

Em `backend/models/orcamento_models.py`, garantir `Date` no import do sqlalchemy (linha de imports `from sqlalchemy import ...`) e adicionar `date` ao import de `datetime`. Depois, dentro de `class Orcamento`, após a linha `validade_proposta` (orcamento_models.py:84), inserir:

```python
    data_limite: Mapped[date | None] = mapped_column(Date, nullable=True)
```

E após a relationship `itens` (orcamento_models.py:102-105), inserir:

```python
    segmentos: Mapped[list["OrcamentoSegmento"]] = relationship(
        "OrcamentoSegmento",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
```

Topo do arquivo, garantir imports:
```python
from datetime import date, datetime
from sqlalchemy import Date  # somar à lista de imports já existente
```

- [ ] **Step 2: Criar model `OrcamentoSegmento` em extra_models.py**

Em `backend/models/extra_models.py`, somar `UniqueConstraint` ao import do sqlalchemy:
```python
from sqlalchemy import (
    DECIMAL, Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, func,
)
```

E adicionar ao final do arquivo:

```python
class OrcamentoSegmento(Base):
    """BLOCO A — segmentos (multi) classificando o orçamento. Só etiqueta."""

    __tablename__ = "orcamento_segmentos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    orcamento_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orcamentos.id", ondelete="CASCADE"), nullable=False
    )
    seguimento: Mapped[str] = mapped_column(String(50), nullable=False)

    __table_args__ = (
        UniqueConstraint("orcamento_id", "seguimento", name="uq_orc_segmento"),
    )
```

- [ ] **Step 3: Verificar import circular do relationship**

`Orcamento.segmentos` referencia `"OrcamentoSegmento"` por string — ok sem import direto. Confirmar que `extra_models` importa `Base` do mesmo lugar (`from backend.database import Base`) — já importa.

Run:
```bash
python -c "from backend.models.orcamento_models import Orcamento; from backend.models.extra_models import OrcamentoSegmento; print('models OK')"
```
Expected: `models OK` (mais o UserWarning de JWT_SECRET, ignorável).

- [ ] **Step 4: Commit**

```bash
git add backend/models/orcamento_models.py backend/models/extra_models.py
git commit -m "feat(A): model OrcamentoSegmento + coluna data_limite"
```

---

## Task 2: Schemas — status 6 estados, segmentos, data_limite

**Files:**
- Modify: `backend/schemas/orcamento_schemas.py`

- [ ] **Step 1: Estender `_STATUS_VALIDOS` para 6 estados**

Substituir orcamento_schemas.py:85:
```python
_STATUS_VALIDOS = {"rascunho", "enviado", "aprovado", "rejeitado"}
```
por:
```python
_STATUS_VALIDOS = {
    "rascunho", "enviado", "aprovado", "reprovado", "perdida", "fechado",
}
```

- [ ] **Step 2: Adicionar `segmentos` e `data_limite` em Create/Update/Read**

Garantir import no topo: `from datetime import date` (somar se ausente).

Em `OrcamentoCreate` (após `orcamentista_id`, orcamento_schemas.py:107):
```python
    data_limite: date | None = None
    segmentos: list[str] = []
```

Em `OrcamentoUpdate` (após `texto_livre_proposta`, orcamento_schemas.py:129):
```python
    data_limite: date | None = None
    segmentos: list[str] | None = None
```

Em `OrcamentoRead` (após `texto_livre_proposta`, orcamento_schemas.py:170):
```python
    data_limite: date | None = None
    segmentos: list[str] = []

    @field_validator("segmentos", mode="before")
    @classmethod
    def _serializa_segmentos(cls, v):
        # Aceita relationship (list[OrcamentoSegmento]) ou list[str] já pronta.
        if v and not isinstance(v[0], str):
            return [s.seguimento for s in v]
        return v or []
```

(`field_validator` já está importado neste arquivo.)

- [ ] **Step 3: Verificar parse**

Run:
```bash
python -c "import ast; ast.parse(open('backend/schemas/orcamento_schemas.py',encoding='utf-8').read()); print('parse OK')"
```
Expected: `parse OK`

- [ ] **Step 4: Commit**

```bash
git add backend/schemas/orcamento_schemas.py
git commit -m "feat(A): schemas status 6 estados, segmentos, data_limite"
```

---

## Task 3: Router — máquina de transições + editabilidade

**Files:**
- Modify: `backend/routers/orcamento_routers.py`

- [ ] **Step 1: Substituir `_TRANSICOES_STATUS` (orcamento_routers.py:70-75)**

```python
_TRANSICOES_STATUS: dict[str, frozenset[str]] = {
    "rascunho": frozenset({"enviado"}),
    "enviado": frozenset({"aprovado", "reprovado", "perdida"}),
    "aprovado": frozenset({"fechado", "perdida"}),
    "reprovado": frozenset({"rascunho"}),
    "perdida": frozenset(),
    "fechado": frozenset(),
}
```

- [ ] **Step 2: Trocar a lógica de `_guard_rascunho` (orcamento_routers.py:61-66)**

Manter o nome (6 callsites) mas mudar a regra para permitir `rascunho` e `reprovado`:

```python
_EDITAVEIS = frozenset({"rascunho", "reprovado"})


def _guard_rascunho(orc: Orcamento) -> None:
    """Itens só editam em status editável (rascunho/reprovado). Demais congelam."""
    if orc.status not in _EDITAVEIS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Orçamento com status '{orc.status}' está congelado e não "
            "permite alterações de itens.",
        )
```

- [ ] **Step 3: Run sanity de transições**

Run:
```bash
python -c "from backend.routers.orcamento_routers import _TRANSICOES_STATUS as T; assert T['enviado']=={'aprovado','reprovado','perdida'}; assert T['perdida']==frozenset(); print('transicoes OK')"
```
Expected: `transicoes OK`

- [ ] **Step 4: Commit**

```bash
git add backend/routers/orcamento_routers.py
git commit -m "feat(A): maquina de transicoes 6 estados + freeze ao enviar"
```

---

## Task 4: Router — persistir segmentos + remover /aprovar

**Files:**
- Modify: `backend/routers/orcamento_routers.py`

- [ ] **Step 1: Helper de persistência de segmentos**

Adicionar após `_guard_rascunho` (perto da linha 67). Importa `OrcamentoSegmento` e `ParametroSeguimento` no topo do bloco de imports do arquivo (junto dos outros `from backend.models...`):

```python
from backend.models.extra_models import OrcamentoSegmento
from backend.models.param_models import ParametroSeguimento
```

Helper:
```python
def _aplicar_segmentos(db: Session, orc: Orcamento, segmentos: list[str]) -> None:
    """Substitui em bloco os segmentos do orçamento. Valida contra ParametroSeguimento."""
    validos = {
        s.nome for s in db.query(ParametroSeguimento).all()
    }  # ajuste o atributo .nome conforme o model (ver Step 1b)
    for seg in segmentos:
        if seg not in validos:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Segmento inválido: '{seg}'. Cadastre em Parâmetros.",
            )
    orc.segmentos.clear()  # delete-orphan remove os antigos
    db.flush()
    for seg in segmentos:
        orc.segmentos.append(OrcamentoSegmento(seguimento=seg))
```

- [ ] **Step 1b: Confirmar nome do campo em ParametroSeguimento**

Run:
```bash
python -c "from backend.models.param_models import ParametroSeguimento as P; print([c.name for c in P.__table__.columns])"
```
Use o nome real da coluna de valor (provavelmente `nome` ou `seguimento`) no `validos = {...}` acima. Corrigir se diferente.

- [ ] **Step 2: Tratar `segmentos` no `criar_orcamento` (orcamento_routers.py:194-200)**

`Orcamento(**body.model_dump())` quebra com `segmentos` (não é coluna). Substituir o corpo:

```python
def criar_orcamento(body: OrcamentoCreate, db: Session = Depends(get_db)):
    _get_or_404(db, Cliente, body.cliente_id)
    dados = body.model_dump()
    segmentos = dados.pop("segmentos", [])
    obj = Orcamento(**dados)
    db.add(obj)
    db.flush()
    _aplicar_segmentos(db, obj, segmentos)
    db.commit()
    db.refresh(obj)
    return obj
```

- [ ] **Step 3: Tratar `segmentos` no `atualizar_orcamento` (orcamento_routers.py:208-227)**

Após o bloco de status e antes de `if dados:`, extrair segmentos. Versão final do handler:

```python
def atualizar_orcamento(id: int, body: OrcamentoUpdate, db: Session = Depends(get_db)):
    obj = _get_or_404(db, Orcamento, id)
    dados = body.model_dump(exclude_none=True)

    segmentos = dados.pop("segmentos", None)

    if "status" in dados:
        novo = dados.pop("status")
        _guard_transicao_status(obj.status, novo)
        obj.status = novo
        if novo == "aprovado":
            obj.aprovado_em = datetime.now(timezone.utc)

    if dados:
        _guard_rascunho(obj)
        for k, v in dados.items():
            setattr(obj, k, v)

    if segmentos is not None:
        _aplicar_segmentos(db, obj, segmentos)

    db.commit()
    db.refresh(obj)
    return obj
```

- [ ] **Step 4: Remover o endpoint `/aprovar` (orcamento_routers.py:230-253+)**

Deletar o decorator `@router.post("/orcamentos/{id}/aprovar", ...)` e toda a função `aprovar_orcamento` (até o `return` dela). O histórico de desconto (BLOCO 1.3) que vivia ali: se ainda for desejado, migra para a transição `→ aprovado` no `atualizar_orcamento`. Para este sub-projeto, mover a gravação de `HistoricoDesconto` para dentro do bloco `if novo == "aprovado":` do Step 3:

```python
        if novo == "aprovado":
            obj.aprovado_em = datetime.now(timezone.utc)
            _gravar_historico_desconto(db, obj)
```

E criar `_gravar_historico_desconto` reusando o corpo que estava em `aprovar_orcamento` (cálculo de `subtotal_fat`, `HistoricoDesconto(...)`). Mantém o comportamento BLOCO 1.3 sem o endpoint legado.

- [ ] **Step 5: Run import + parse**

Run:
```bash
python -c "import backend.routers.orcamento_routers; print('router import OK')"
```
Expected: `router import OK`

- [ ] **Step 6: Commit**

```bash
git add backend/routers/orcamento_routers.py
git commit -m "feat(A): persistir segmentos no orcamento, remover /aprovar legado"
```

---

## Task 5: Testes de transição e segmento (TDD)

**Files:**
- Create: `tests/test_status_transicoes.py`
- Modify: `tests/test_orcamentos.py`

- [ ] **Step 1: Escrever testes de transição (falham primeiro)**

`tests/test_status_transicoes.py`. Reusar fixtures de `conftest.py` (`client`, `db_session`, `orcamento_id`). Inspecionar `tests/conftest.py` para os nomes exatos antes de escrever.

```python
import pytest


def _set_status(client, orc_id, novo):
    return client.put(f"/api/v1/orcamentos/{orc_id}", json={"status": novo})


class TestTransicoes:
    def test_rascunho_para_enviado_ok(self, client, orcamento_id):
        r = _set_status(client, orcamento_id, "enviado")
        assert r.status_code == 200
        assert r.json()["status"] == "enviado"

    def test_rascunho_para_fechado_invalido(self, client, orcamento_id):
        r = _set_status(client, orcamento_id, "fechado")
        assert r.status_code == 422

    def test_enviado_para_perdida_ok(self, client, orcamento_id):
        _set_status(client, orcamento_id, "enviado")
        r = _set_status(client, orcamento_id, "perdida")
        assert r.status_code == 200

    def test_perdida_e_terminal(self, client, orcamento_id):
        _set_status(client, orcamento_id, "enviado")
        _set_status(client, orcamento_id, "perdida")
        r = _set_status(client, orcamento_id, "rascunho")
        assert r.status_code == 422

    def test_reprovado_reabre_para_rascunho(self, client, orcamento_id):
        _set_status(client, orcamento_id, "enviado")
        _set_status(client, orcamento_id, "reprovado")
        r = _set_status(client, orcamento_id, "rascunho")
        assert r.status_code == 200

    def test_freeze_bloqueia_edicao_de_item_em_enviado(
        self, client, orcamento_id, ficha_servico_id
    ):
        _set_status(client, orcamento_id, "enviado")
        r = client.post(
            f"/api/v1/orcamentos/{orcamento_id}/itens",
            json={
                "bloco": "servicos",
                "ficha_servico_id": ficha_servico_id,
                "descricao": "X",
                "unidade": "un",
                "quantidade": "1",
                "mod_fat": "BDI-MO",
                "margem_lucro": "10",
            },
        )
        assert r.status_code == 403
```

- [ ] **Step 2: Run — espera FAIL/ERROR (comportamento ainda não cabe nos testes antigos)**

Run: `python -m pytest tests/test_status_transicoes.py -v`
Expected: alguns FAIL se rodado antes das Tasks 3/4 estarem completas. Se rodado depois, devem passar. (Se ambiente não tem pytest, ver nota no fim.)

- [ ] **Step 3: Estender test_orcamentos.py com segmentos + data_limite**

Adicionar ao final de `tests/test_orcamentos.py` (assumindo `_seg_valido` = um segmento que o seed cria, ex. "EPS" — confirmar no seed):

```python
class TestSegmentosEDataLimite:
    def test_cria_com_segmentos(self, client, cliente_id):
        r = client.post("/api/v1/orcamentos", json={
            "numero": "SEG-1", "cliente_id": cliente_id,
            "uf_execucao": "PR", "data_limite": "2026-07-01",
            "segmentos": ["EPS"],
        })
        assert r.status_code == 201
        body = r.json()
        assert body["segmentos"] == ["EPS"]
        assert body["data_limite"] == "2026-07-01"

    def test_rejeita_segmento_inexistente(self, client, cliente_id):
        r = client.post("/api/v1/orcamentos", json={
            "numero": "SEG-2", "cliente_id": cliente_id,
            "uf_execucao": "PR", "segmentos": ["NAO_EXISTE_XYZ"],
        })
        assert r.status_code == 422

    def test_substitui_segmentos_no_put(self, client, cliente_id):
        r = client.post("/api/v1/orcamentos", json={
            "numero": "SEG-3", "cliente_id": cliente_id,
            "uf_execucao": "PR", "segmentos": ["EPS"],
        })
        oid = r.json()["id"]
        r2 = client.put(f"/api/v1/orcamentos/{oid}", json={"segmentos": ["VERTICAL"]})
        assert r2.status_code == 200
        assert r2.json()["segmentos"] == ["VERTICAL"]
```

Confirmar que `cliente_id`/`ficha_servico_id` são fixtures existentes em `conftest.py`; ajustar nomes se diferirem. Confirmar que "EPS" e "VERTICAL" existem no seed de `ParametroSeguimento`.

- [ ] **Step 4: Run suíte completa**

Run: `python -m pytest tests/test_status_transicoes.py tests/test_orcamentos.py -v`
Expected: PASS em todos.

- [ ] **Step 5: Commit**

```bash
git add tests/test_status_transicoes.py tests/test_orcamentos.py
git commit -m "test(A): transicoes de status, freeze, segmentos e data_limite"
```

---

## Task 6: Seed com status novos + segmentos

**Files:**
- Modify: `backend/seeds.py`

- [ ] **Step 1: Inspecionar seed atual de orçamentos**

Run: `grep -n "Orcamento(\|status=\|seed_orc\|seguimento" backend/seeds.py`
Identificar onde orçamentos exemplo são criados (se houver). Se não houver seed de orçamento, criar um pequeno em `seed_extra` ou função nova `seed_orcamentos_exemplo`.

- [ ] **Step 2: Garantir status válidos e ≥1 segmento**

Qualquer `status="rejeitado"` em seed vira `status="reprovado"`. Adicionar `segmentos` via append pós-flush:

```python
        orc = Orcamento(numero="EX-1", cliente_id=cli.id, uf_execucao="PR",
                        status="enviado", data_limite=date(2026, 7, 15))
        db.add(orc); db.flush()
        from backend.models.extra_models import OrcamentoSegmento
        orc.segmentos.append(OrcamentoSegmento(seguimento="EPS"))
```

(`from datetime import date` no topo do seed se ausente.)

- [ ] **Step 3: Run seed em DB limpo**

Run:
```bash
python -c "import backend.seeds as s; s.run()" 2>&1 | tail -5
```
Expected: sem exceção. (Apaga/recria DB conforme o fluxo do projeto.)

- [ ] **Step 4: Commit**

```bash
git add backend/seeds.py
git commit -m "feat(A): seed com status novos e segmento exemplo"
```

---

## Task 7: Frontend — StatusBadge 6 estados (sem cor nova)

**Files:**
- Modify: `frontend/app/components/status-badge.tsx`

- [ ] **Step 1: Estender STATUS_MAP**

Substituir o `STATUS_MAP` (status-badge.tsx:3-9) por:

```tsx
const STATUS_MAP: Record<string, { variant: "secondary" | "warning" | "success" | "destructive"; label: string }> = {
  /* Discord Dark — reusa variantes existentes; sem cor nova */
  rascunho:  { variant: "secondary",   label: "RASCUNHO" },
  enviado:   { variant: "warning",     label: "ENVIADO" },
  aprovado:  { variant: "success",     label: "APROVADO" },
  reprovado: { variant: "destructive", label: "REPROVADO" },
  perdida:   { variant: "secondary",   label: "PERDIDA" },
  fechado:   { variant: "success",     label: "FECHADO" },
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/app/components/status-badge.tsx
git commit -m "feat(A): StatusBadge cobre 6 estados reusando variantes"
```

---

## Task 8: Frontend — form de cadastro (data_limite + segmentos)

**Files:**
- Modify: `frontend/app/routes/orcamentos.novo.tsx`
- Modify: `frontend/app/lib/api.ts` (se `create` não repassar campos extras)

- [ ] **Step 1: Inspecionar o form atual**

Run: `grep -n "orcamentoApi.create\|useState\|<Input\|data_limite\|segmento" frontend/app/routes/orcamentos.novo.tsx`
Mapear o shape do payload de criação atual.

- [ ] **Step 2: Adicionar estado + inputs**

Adicionar `const [dataLimite, setDataLimite] = useState("")` e `const [segmentos, setSegmentos] = useState<string[]>([])`. Carregar opções de segmento via `parametroApi` (mesma fonte do modal de item — conferir nome do método em `lib/api.ts`, ex. `parametroApi.listSeguimentos()`).

Input data-limite:
```tsx
<Label>Data-limite de envio</Label>
<Input type="date" value={dataLimite} onChange={(e) => setDataLimite(e.target.value)} />
```

Multi-select de segmentos: usar o padrão de checkboxes/toggle já presente no projeto (conferir se há um `MultiSelect`; se não, lista de checkboxes simples). Cada toggle adiciona/remove de `segmentos`.

No submit, incluir no payload: `data_limite: dataLimite || null, segmentos`.

- [ ] **Step 3: Garantir que api.ts repassa o body inteiro**

`orcamentoApi.create` deve ser `(body) => api.post("/orcamentos", body)` — repassa tudo. Se já é assim, nada a mudar.

- [ ] **Step 4: Build frontend**

Run (no diretório frontend, conforme o projeto): `npm run build` ou `npm run typecheck`
Expected: sem erro de tipo.

- [ ] **Step 5: Commit**

```bash
git add frontend/app/routes/orcamentos.novo.tsx frontend/app/lib/api.ts
git commit -m "feat(A): cadastro de orcamento com data-limite e segmentos"
```

---

## Task 9: Frontend — editor com dropdown de status (substitui Aprovar/Rejeitar)

**Files:**
- Modify: `frontend/app/routes/orcamentos.$id.tsx`

- [ ] **Step 1: Mapa de transições no front**

Adicionar constante espelhando o backend:

```tsx
const TRANSICOES: Record<string, string[]> = {
  rascunho: ["enviado"],
  enviado: ["aprovado", "reprovado", "perdida"],
  aprovado: ["fechado", "perdida"],
  reprovado: ["rascunho"],
  perdida: [],
  fechado: [],
}
const STATUS_LABEL: Record<string, string> = {
  rascunho: "Rascunho", enviado: "Enviado", aprovado: "Aprovado",
  reprovado: "Reprovado", perdida: "Perdida", fechado: "Fechado",
}
```

- [ ] **Step 2: Substituir botões Aprovar/Rejeitar por Select de status**

Localizar os botões atuais (procurar `aprovar`/`rejeitar`/`/aprovar` no arquivo). Trocar por um `Select` cujas opções são `TRANSICOES[orc.status]`, com label de `STATUS_LABEL`. On change chama `orcamentoApi.update(orcId, { status: novo })` com try/catch + toast (sucesso/erro). Em estados sem transições (`perdida`/`fechado`), renderizar só o `StatusBadge`, sem Select.

Remover qualquer chamada a `orcamentoApi.aprovar` / endpoint `/aprovar` (foi removido no backend).

- [ ] **Step 3: Bloquear edição de itens em status congelado**

`const editavel = ["rascunho", "reprovado"].includes(orc.status)`. Usar `editavel` para desabilitar botões de adicionar/remover item e o botão Calcular (já pode existir `readonly` — reusar/alinhar).

- [ ] **Step 4: Build frontend**

Run: `npm run build` ou `npm run typecheck`
Expected: sem erro.

- [ ] **Step 5: Commit**

```bash
git add frontend/app/routes/orcamentos.$id.tsx
git commit -m "feat(A): editor com dropdown de status e freeze de itens"
```

---

## Self-Review (preenchido)

**Spec coverage:**
- 6 estados → Task 2 (`_STATUS_VALIDOS`), Task 3 (`_TRANSICOES_STATUS`), Task 7/9 (UI). ✓
- Funil + re-edição → Task 3 transições + Task 4 (reprovado→rascunho reabre). ✓
- Congela ao enviar → Task 3 `_guard_rascunho`/`_EDITAVEIS`. ✓
- Multi-segmento tabela junção → Task 1 model, Task 4 persistência, Task 2 schema. ✓
- Segmento valida contra ParametroSeguimento → Task 4 `_aplicar_segmentos`. ✓
- data_limite coluna+cadastro → Task 1 coluna, Task 2 schema, Task 8 form. ✓
- slug minúsculo + label front → Task 2 (DB), Task 7/9 (label). ✓
- sem cor nova → Task 7 reusa variantes existentes. ✓
- remover /aprovar → Task 4 Step 4. ✓
- DB descartável, sem migration → Task 6 só seed. ✓

**Placeholder scan:** Os "inspecionar/confirmar nome" (Task 4 Step 1b, Task 5 Step 1/3, Task 8 Step 1) são verificações deliberadas de nomes reais do codebase, não placeholders de implementação — cada um tem comando concreto e instrução de ajuste. Aceitável.

**Type consistency:** `_guard_rascunho` mantido (6 callsites), `_aplicar_segmentos(db, orc, list[str])` usado igual em create/update, `segmentos: list[str]` consistente schema↔front, `TRANSICOES` front espelha `_TRANSICOES_STATUS` back. ✓

## Nota sobre testes

pytest pode não estar disponível no shell sandbox (visto na sessão anterior — sem pip/pytest no venv hermes). As Tasks 5 escrevem os testes mesmo assim; rode `python -m pytest` no venv do projeto. Se indisponível no momento da execução, validar via import/parse (mostrado em cada task) e marcar os testes como "escritos, execução pendente no venv do projeto".
