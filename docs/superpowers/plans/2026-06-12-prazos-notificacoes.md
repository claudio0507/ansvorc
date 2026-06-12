# Prazos + Notificações Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar sino de notificações de prazo no topbar e calendário de prazos no dashboard, alimentados por dois endpoints backend que computam orçamentos rascunho/reprovado com data_limite iminente.

**Architecture:** Backend FastAPI expõe `/notificacoes` (até amanhã, p/ sino) e `/prazos?mes=` (mês inteiro, p/ calendário). Frontend React Router monta um sino (DropdownMenu + polling) no header e um calendário (shadcn Calendar via react-day-picker) no dashboard.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy 2, pytest; TypeScript, React 19, react-router, react-day-picker v9 + date-fns v4, shadcn ui.

**Spec:** `docs/superpowers/specs/2026-06-12-prazos-notificacoes-design.md`

---

## File Structure

- `backend/routers/relatorio_routers.py` — 2 endpoints (`/notificacoes`, `/prazos`).
- `backend/middleware.py` — 2 entradas RBAC.
- `tests/test_notificacoes.py` — testes dos 2 endpoints (novo).
- `frontend/package.json` — deps react-day-picker + date-fns.
- `frontend/app/components/ui/calendar.tsx` — componente shadcn (novo).
- `frontend/app/components/notification-bell.tsx` — sino (novo).
- `frontend/app/components/prazos-calendar.tsx` — calendário (novo).
- `frontend/app/lib/api.ts` — notificacaoApi + prazoApi.
- `frontend/app/routes/_app.tsx` — monta o sino.
- `frontend/app/routes/dashboard.tsx` — monta o calendário.

---

## Task 1: Backend — endpoints /notificacoes e /prazos (TDD)

**Files:**
- Modify: `backend/routers/relatorio_routers.py`
- Modify: `backend/middleware.py`
- Create: `tests/test_notificacoes.py`

- [ ] **Step 1: Escrever testes (falham primeiro)**

Criar `tests/test_notificacoes.py`. Replica a infra mínima do test_orcamentos.py (engine in-memory, client sponsor, setup_db autouse, fixture cliente_id) — OU, mais simples, importar o `client` e fixtures definindo-os localmente. Como as fixtures (`client`, `cliente_id`, `db_session`, `setup_db`) NÃO estão em conftest (estão em test_orcamentos.py), replicar o bloco de setup (engine StaticPool in-memory + override_get_db + `client = TestClient(app, headers=...)` + autouse `setup_db` + `db_session` + `cliente_id`) copiando o padrão de test_orcamentos.py linhas 1-70.

```python
from datetime import date, timedelta
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.auth import criar_token
from backend.database import Base, get_db
from backend.main import app
from backend.models.orcamento_models import Cliente, Orcamento

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

@pytest.fixture
def db_session():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def cliente_id(db_session):
    c = Cliente(nome="ACME", cnpj_cpf="00.000.000/0001-91")
    db_session.add(c); db_session.commit(); db_session.refresh(c)
    return c.id

def _mk(db_session, cliente_id, numero, status, dlimite):
    o = Orcamento(
        numero=numero, cliente_id=cliente_id, uf_execucao="PR",
        status=status, data_limite=dlimite,
    )
    db_session.add(o); db_session.commit()


class TestNotificacoes:
    def test_so_rascunho_reprovado_ate_amanha(self, db_session, cliente_id):
        hoje = date.today()
        _mk(db_session, cliente_id, "N-ATRASO", "rascunho", hoje - timedelta(days=2))
        _mk(db_session, cliente_id, "N-HOJE", "reprovado", hoje)
        _mk(db_session, cliente_id, "N-AMANHA", "rascunho", hoje + timedelta(days=1))
        _mk(db_session, cliente_id, "N-FUTURO", "rascunho", hoje + timedelta(days=5))  # fora
        _mk(db_session, cliente_id, "N-ENVIADO", "enviado", hoje)  # fora (status)
        d = client.get("/api/v1/notificacoes").json()
        numeros = {n["numero"] for n in d["notificacoes"]}
        assert numeros == {"N-ATRASO", "N-HOJE", "N-AMANHA"}
        assert d["total"] == 3
        urg = {n["numero"]: n["urgencia"] for n in d["notificacoes"]}
        assert urg["N-ATRASO"] == "atrasado"
        assert urg["N-HOJE"] == "hoje"
        assert urg["N-AMANHA"] == "amanha"

    def test_vazio(self):
        d = client.get("/api/v1/notificacoes").json()
        assert d["total"] == 0
        assert d["notificacoes"] == []


class TestPrazos:
    def test_filtra_por_mes(self, db_session, cliente_id):
        hoje = date.today()
        _mk(db_session, cliente_id, "P-ESTE", "rascunho", date(hoje.year, hoje.month, 15))
        # mês seguinte (fora do filtro do mês atual)
        prox = date(hoje.year + (hoje.month == 12), (hoje.month % 12) + 1, 10)
        _mk(db_session, cliente_id, "P-PROX", "rascunho", prox)
        mes_str = f"{hoje.year}-{hoje.month:02d}"
        lista = client.get(f"/api/v1/prazos?mes={mes_str}").json()
        numeros = {p["numero"] for p in lista}
        assert "P-ESTE" in numeros
        assert "P-PROX" not in numeros
```

- [ ] **Step 2: Rodar — espera FAIL (404, endpoints não existem)**

Run: `py -m pytest tests/test_notificacoes.py -v`
Expected: FAIL (404 / KeyError). Se `py` indisponível, tentar `python -m pytest`.

- [ ] **Step 3: Implementar os endpoints em relatorio_routers.py**

Garantir imports no topo: `from datetime import date, timedelta` (o arquivo já importa `datetime` como módulo — adicionar `date, timedelta` de forma compatível; se já há `import datetime`, usar `datetime.date`/`datetime.timedelta` OU adicionar `from datetime import date, timedelta`. Conferir o estilo existente e seguir). `Orcamento` já está importado.

Adicionar ao final do arquivo (ou junto dos outros endpoints), usando o mesmo `router`:

```python
@router.get("/notificacoes")
def listar_notificacoes(db: Session = Depends(get_db)) -> dict:
    """Prazos de envio iminentes (rascunho/reprovado, até amanhã)."""
    hoje = date.today()
    amanha = hoje + timedelta(days=1)
    orcs = (
        db.query(Orcamento)
        .filter(Orcamento.status.in_(["rascunho", "reprovado"]))
        .filter(Orcamento.data_limite.isnot(None))
        .filter(Orcamento.data_limite <= amanha)
        .order_by(Orcamento.data_limite)
        .all()
    )

    def _urg(d):
        return "atrasado" if d < hoje else "hoje" if d == hoje else "amanha"

    itens = [
        {
            "id": o.id, "numero": o.numero, "obra": o.obra,
            "data_limite": o.data_limite, "urgencia": _urg(o.data_limite),
        }
        for o in orcs
    ]
    return {"total": len(itens), "notificacoes": itens}


@router.get("/prazos")
def listar_prazos(mes: str | None = None, db: Session = Depends(get_db)) -> list[dict]:
    """Orçamentos rascunho/reprovado com data_limite no mês (para o calendário)."""
    hoje = date.today()
    if mes:
        ano, m = int(mes[:4]), int(mes[5:7])
    else:
        ano, m = hoje.year, hoje.month
    inicio = date(ano, m, 1)
    fim = date(ano + (m == 12), (m % 12) + 1, 1)
    orcs = (
        db.query(Orcamento)
        .filter(Orcamento.status.in_(["rascunho", "reprovado"]))
        .filter(Orcamento.data_limite.isnot(None))
        .filter(Orcamento.data_limite >= inicio, Orcamento.data_limite < fim)
        .order_by(Orcamento.data_limite)
        .all()
    )

    def _urg(d):
        if d < hoje:
            return "atrasado"
        if d == hoje:
            return "hoje"
        if d == hoje + timedelta(days=1):
            return "amanha"
        return "futuro"

    return [
        {
            "id": o.id, "numero": o.numero, "obra": o.obra,
            "data_limite": o.data_limite, "urgencia": _urg(o.data_limite),
        }
        for o in orcs
    ]
```

- [ ] **Step 4: Registrar RBAC no middleware.py**

Em `backend/middleware.py`, no `_RBAC` (lista de tuplas), adicionar ANTES do `]` de fechamento da lista (junto das outras entradas `_TODOS_PAPEIS`):
```python
    ("/api/v1/notificacoes", _TODOS_PAPEIS),
    ("/api/v1/prazos", _TODOS_PAPEIS),
```

- [ ] **Step 5: Rodar — espera PASS**

Run: `py -m pytest tests/test_notificacoes.py -v` → todos passam.
Smoke do import: `python -c "import backend.main; print('ok')"`.

- [ ] **Step 6: Commit**

```bash
git add backend/routers/relatorio_routers.py backend/middleware.py tests/test_notificacoes.py
git commit -m "feat(B): endpoints /notificacoes e /prazos + RBAC + testes"
```

---

## Task 2: Frontend — deps + componente shadcn Calendar

**Files:**
- Modify: `frontend/package.json`
- Create: `frontend/app/components/ui/calendar.tsx`

- [ ] **Step 1: Adicionar deps ao package.json**

Em `frontend/package.json`, na seção `dependencies`, adicionar (React 19 compatível):
```json
    "react-day-picker": "^9.4.0",
    "date-fns": "^4.1.0",
```
(Manter ordenação alfabética se o arquivo seguir essa convenção; senão adicionar perto das outras libs UI.)

- [ ] **Step 2: Criar ui/calendar.tsx (componente shadcn oficial)**

Criar `frontend/app/components/ui/calendar.tsx`. Este é o wrapper shadcn padrão sobre react-day-picker v9, usando o `buttonVariants` e o util `cn` do projeto. CONFERIR primeiro que `~/lib/utils` exporta `cn` e que `~/components/ui/button` exporta `buttonVariants` (padrão shadcn — provavelmente sim; se o nome diferir, ajustar o import).

```tsx
import * as React from "react"
import { ChevronLeftIcon, ChevronRightIcon } from "@phosphor-icons/react"
import { DayPicker } from "react-day-picker"

import { cn } from "~/lib/utils"
import { buttonVariants } from "~/components/ui/button"

export type CalendarProps = React.ComponentProps<typeof DayPicker>

function Calendar({ className, classNames, showOutsideDays = true, ...props }: CalendarProps) {
  return (
    <DayPicker
      showOutsideDays={showOutsideDays}
      className={cn("p-3", className)}
      classNames={{
        months: "flex flex-col sm:flex-row gap-2",
        month: "flex flex-col gap-4",
        caption: "flex justify-center pt-1 relative items-center w-full",
        caption_label: "text-sm font-medium",
        nav: "flex items-center gap-1",
        nav_button: cn(
          buttonVariants({ variant: "outline" }),
          "size-7 bg-transparent p-0 opacity-50 hover:opacity-100"
        ),
        nav_button_previous: "absolute left-1",
        nav_button_next: "absolute right-1",
        table: "w-full border-collapse space-x-1",
        head_row: "flex",
        head_cell: "text-muted-foreground rounded-md w-8 font-normal text-[0.8rem]",
        row: "flex w-full mt-2",
        cell: "relative p-0 text-center text-sm focus-within:relative focus-within:z-20",
        day: cn(
          buttonVariants({ variant: "ghost" }),
          "size-8 p-0 font-normal aria-selected:opacity-100"
        ),
        day_selected:
          "bg-primary text-primary-foreground hover:bg-primary hover:text-primary-foreground focus:bg-primary focus:text-primary-foreground",
        day_today: "bg-accent text-accent-foreground",
        day_outside: "text-muted-foreground opacity-50",
        day_disabled: "text-muted-foreground opacity-50",
        day_hidden: "invisible",
        ...classNames,
      }}
      components={{
        IconLeft: () => <ChevronLeftIcon className="size-4" />,
        IconRight: () => <ChevronRightIcon className="size-4" />,
      }}
      {...props}
    />
  )
}

export { Calendar }
```
Nota: react-day-picker v9 mudou alguns nomes de classNames vs v8. Se ao rodar o typecheck/build aparecerem props inválidas, consultar a doc v9 e ajustar (ex.: `nav_button`→`button_previous`/`button_next` em v9). O implementador DEVE validar contra a versão instalada; se houver divergência de API, seguir a v9 real. Sem cores novas — só tokens (`bg-primary`, `bg-accent`, `text-muted-foreground`) já existentes.

- [ ] **Step 3: Verificar utils**

Run: `grep -n "export.*cn" frontend/app/lib/utils.ts` e `grep -n "buttonVariants" frontend/app/components/ui/button.tsx`
Confirmar ambos existem. Se `cn` estiver em outro caminho, ajustar o import.

- [ ] **Step 4: Commit**

```bash
git add frontend/package.json frontend/app/components/ui/calendar.tsx
git commit -m "feat(B): adiciona react-day-picker/date-fns + componente shadcn Calendar"
```

---

## Task 3: Frontend — API methods + sino de notificações

**Files:**
- Modify: `frontend/app/lib/api.ts`
- Create: `frontend/app/components/notification-bell.tsx`
- Modify: `frontend/app/routes/_app.tsx`

- [ ] **Step 1: Adicionar notificacaoApi e prazoApi em lib/api.ts**

Ao final de `frontend/app/lib/api.ts`, adicionar (seguir o padrão dos outros `*Api` que usam o helper `api`):
```tsx
export const notificacaoApi = {
  list: () => api.get<{ total: number; notificacoes: any[] }>("/notificacoes"),
}

export const prazoApi = {
  list: (mes?: string) =>
    api.get<any[]>(`/prazos${mes ? `?mes=${encodeURIComponent(mes)}` : ""}`),
}
```
CONFERIR que existe um helper `api.get` (usado por outros Api). Se o padrão for `api.get<T>(path)`, usar como acima.

- [ ] **Step 2: Criar notification-bell.tsx**

Criar `frontend/app/components/notification-bell.tsx`:
```tsx
import { useEffect, useState } from "react"
import { Link } from "react-router"
import { BellIcon } from "@phosphor-icons/react"

import { Button } from "~/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "~/components/ui/dropdown-menu"
import { notificacaoApi } from "~/lib/api"

const URG_LABEL: Record<string, string> = {
  atrasado: "Atrasado",
  hoje: "Hoje",
  amanha: "Amanhã",
}

export function NotificationBell() {
  const [data, setData] = useState<{ total: number; notificacoes: any[] }>({
    total: 0,
    notificacoes: [],
  })

  useEffect(() => {
    const load = () =>
      notificacaoApi.list().then(setData).catch(() => {})
    load()
    const t = setInterval(load, 5 * 60 * 1000)
    return () => clearInterval(t)
  }, [])

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="relative" aria-label="Notificações">
          <BellIcon className="size-4" />
          {data.total > 0 && (
            <span className="bg-destructive text-destructive-foreground absolute -top-0.5 -right-0.5 flex size-4 items-center justify-center rounded-full text-[0.5625rem] font-bold tabular-nums">
              {data.total}
            </span>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-72">
        <div className="text-muted-foreground px-2 py-1.5 text-[0.625rem] font-semibold uppercase tracking-wider">
          Prazos de Envio
        </div>
        {data.notificacoes.length === 0 ? (
          <div className="text-muted-foreground px-2 py-4 text-center text-xs">
            Nenhum prazo próximo.
          </div>
        ) : (
          data.notificacoes.map((n) => (
            <Link
              key={n.id}
              to={`/orcamentos/${n.id}`}
              className="hover:bg-accent flex flex-col gap-0.5 rounded-sm px-2 py-2"
            >
              <div className="flex items-center justify-between gap-2">
                <span className="text-xs font-medium">{n.numero}</span>
                <span className="bg-destructive/15 text-destructive rounded px-1.5 py-0.5 text-[0.5625rem] font-semibold">
                  {URG_LABEL[n.urgencia] ?? n.urgencia}
                </span>
              </div>
              {n.obra && <span className="text-muted-foreground truncate text-[0.625rem]">{n.obra}</span>}
            </Link>
          ))
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
```
CONFERIR que `~/components/ui/dropdown-menu` exporta `DropdownMenu`, `DropdownMenuTrigger`, `DropdownMenuContent` (padrão shadcn — sim). Se algum não existir, usar os exports reais do arquivo.

- [ ] **Step 3: Montar o sino no header de _app.tsx**

Em `frontend/app/routes/_app.tsx`, importar no topo:
```tsx
import { NotificationBell } from "~/components/notification-bell"
```
E dentro do `<div className="ml-auto flex items-center gap-1">` (linha ~66), inserir `<NotificationBell />` como PRIMEIRO filho (antes do botão de dark mode):
```tsx
          <div className="ml-auto flex items-center gap-1">
            <NotificationBell />
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleDark}
              ...
```

- [ ] **Step 4: Self-check**

Se `frontend/node_modules` existir, rodar `npm run typecheck`/`build`. Se ausente, NÃO instalar; confirmar por leitura: imports presentes, `notificacaoApi.list` existe, `bg-destructive` é token existente.

- [ ] **Step 5: Commit**

```bash
git add frontend/app/lib/api.ts frontend/app/components/notification-bell.tsx frontend/app/routes/_app.tsx
git commit -m "feat(B): sino de notificacoes no topbar (badge + dropdown)"
```

---

## Task 4: Frontend — calendário de prazos no dashboard

**Files:**
- Create: `frontend/app/components/prazos-calendar.tsx`
- Modify: `frontend/app/routes/dashboard.tsx`

- [ ] **Step 1: Criar prazos-calendar.tsx**

Criar `frontend/app/components/prazos-calendar.tsx`:
```tsx
import { useEffect, useMemo, useState } from "react"
import { Link } from "react-router"

import { Card } from "~/components/ui/card"
import { Calendar } from "~/components/ui/calendar"
import { prazoApi } from "~/lib/api"

const URG_LABEL: Record<string, string> = {
  atrasado: "Atrasado", hoje: "Hoje", amanha: "Amanhã", futuro: "Futuro",
}

function isoDay(d: Date) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`
}

export function PrazosCalendar() {
  const [mes, setMes] = useState<Date>(new Date())
  const [dia, setDia] = useState<Date>(new Date())
  const [prazos, setPrazos] = useState<any[]>([])

  useEffect(() => {
    const mesStr = `${mes.getFullYear()}-${String(mes.getMonth() + 1).padStart(2, "0")}`
    prazoApi.list(mesStr).then(setPrazos).catch(() => setPrazos([]))
  }, [mes])

  // datas (Date) que têm prazo, para marcar no calendário
  const datasComPrazo = useMemo(
    () =>
      prazos.map((p) => {
        const [y, m, d] = String(p.data_limite).slice(0, 10).split("-").map(Number)
        return new Date(y, m - 1, d)
      }),
    [prazos],
  )

  const diaStr = isoDay(dia)
  const doDia = prazos.filter((p) => String(p.data_limite).slice(0, 10) === diaStr)

  return (
    <Card className="grid grid-cols-1 gap-4 p-4 lg:grid-cols-[auto_1fr]">
      <div>
        <div className="text-muted-foreground text-[0.625rem] font-semibold uppercase tracking-wider mb-2">
          Calendário de Prazos
        </div>
        <Calendar
          mode="single"
          selected={dia}
          onSelect={(d) => d && setDia(d)}
          month={mes}
          onMonthChange={setMes}
          modifiers={{ comPrazo: datasComPrazo }}
          modifiersClassNames={{ comPrazo: "bg-destructive/20 font-semibold rounded-full" }}
        />
      </div>
      <div>
        <div className="text-muted-foreground text-[0.625rem] font-semibold uppercase tracking-wider mb-2">
          Prazos de {dia.toLocaleDateString("pt-BR")}
        </div>
        {doDia.length === 0 ? (
          <div className="text-muted-foreground py-6 text-center text-xs">Sem prazos neste dia.</div>
        ) : (
          <div className="flex flex-col gap-2">
            {doDia.map((p) => (
              <Link
                key={p.id}
                to={`/orcamentos/${p.id}`}
                className="hover:bg-accent flex items-center justify-between gap-2 rounded-sm border px-3 py-2"
              >
                <div className="min-w-0">
                  <div className="text-xs font-medium">{p.numero}</div>
                  {p.obra && <div className="text-muted-foreground truncate text-[0.625rem]">{p.obra}</div>}
                </div>
                <span className="bg-destructive/15 text-destructive shrink-0 rounded px-1.5 py-0.5 text-[0.5625rem] font-semibold">
                  {URG_LABEL[p.urgencia] ?? p.urgencia}
                </span>
              </Link>
            ))}
          </div>
        )}
      </div>
    </Card>
  )
}
```

- [ ] **Step 2: Montar no dashboard**

Em `frontend/app/routes/dashboard.tsx`, importar no topo:
```tsx
import { PrazosCalendar } from "~/components/prazos-calendar"
```
E renderizar `<PrazosCalendar />` DEPOIS do bloco dos dois gráficos (o `<div className="grid grid-cols-1 gap-4 lg:grid-cols-2">` que contém Distribuição/Funil) e ANTES da `<Card>` de "Orçamentos Recentes". Inserir como irmão dentro do `<div className="space-y-6">`.

- [ ] **Step 3: Self-check**

Se `node_modules` existir, `npm run typecheck`/`build`. Senão, NÃO instalar; confirmar por leitura: `Calendar` importado de `~/components/ui/calendar`, `prazoApi.list` existe, props do `<Calendar>` (mode/selected/onSelect/month/onMonthChange/modifiers/modifiersClassNames) são válidas em react-day-picker v9 (ajustar se a v9 instalada divergir — ex. `modifiersClassNames` é válido em v9). Sem cor nova.

- [ ] **Step 4: Commit**

```bash
git add frontend/app/components/prazos-calendar.tsx frontend/app/routes/dashboard.tsx
git commit -m "feat(B): calendario de prazos no dashboard (shadcn Calendar + lista)"
```

---

## Self-Review (preenchido)

**Spec coverage:**
- /notificacoes (rascunho/reprovado até amanhã, 3 urgências) → Task 1. ✓
- /prazos (mês) → Task 1. ✓
- RBAC liberado → Task 1 Step 4. ✓
- Sino topbar + badge bg-destructive + polling 5min + dropdown → Task 3. ✓
- shadcn Calendar (react-day-picker + date-fns) → Task 2. ✓
- Calendário + lista lateral no dashboard → Task 4. ✓
- Sem cor nova → bg-destructive/tokens existentes em Tasks 2/3/4. ✓
- Testes backend → Task 1 Steps 1-5. ✓

**Placeholder scan:** Os "CONFERIR que X exporta Y" são verificações concretas com comando grep e instrução de ajuste — não placeholders de implementação. O aviso sobre nomes de classNames da react-day-picker v9 é uma instrução real de validação contra a versão instalada (a API v9 difere da v8), com comando de fallback. Aceitável.

**Type consistency:** `notificacaoApi.list`/`prazoApi.list` definidos em Task 3 Step 1 e consumidos em Tasks 3/4 com as mesmas assinaturas. `urgencia` strings (atrasado/hoje/amanha/futuro) consistentes entre backend (Task 1) e `URG_LABEL` (Tasks 3/4). `Calendar` props consistentes entre Task 2 (componente) e Task 4 (uso). ✓

## Nota sobre versões / ambiente

- React 19 → react-day-picker v9 + date-fns v4 são compatíveis. Se o `npm install` resolver versões diferentes, o implementador deve garantir compat com React 19.
- A API de `classNames`/`components` da react-day-picker MUDOU da v8 para v9. O `calendar.tsx` no plano segue o shape comum; o implementador DEVE validar contra a v9 instalada (typecheck/build) e ajustar nomes divergentes seguindo a doc oficial v9. Sem isso, o calendário pode não estilizar corretamente.
- pytest roda via `py -m pytest`. Frontend sem typecheck no sandbox (sem node_modules) — validar por review/grep; o typecheck real deve rodar no ambiente do projeto após `npm install`.
