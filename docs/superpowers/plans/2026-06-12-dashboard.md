# Dashboard (métricas por status + Shadcn Charts) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redefinir as métricas do dashboard por status (Total Orçado=enviado; Margem R$ e Margem %=fechado), com filtro mês/acumulado, e migrar os gráficos do dashboard e do bi-precos para Shadcn UI Charts sem introduzir cores novas.

**Architecture:** Backend FastAPI/SQLAlchemy agrega `/dashboard` por status. Frontend React Router renderiza 5 cards + 2 gráficos via o primitive `~/components/ui/chart` (ChartContainer wrapping recharts), reusando os tokens `--chart-1..5` já no tema.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy 2, pytest; TypeScript, React Router, recharts ^3.8 via shadcn chart primitive.

**Spec:** `docs/superpowers/specs/2026-06-12-dashboard-design.md`

---

## File Structure

- `backend/routers/relatorio_routers.py` — `/dashboard` métricas por status (helpers + return).
- `tests/test_orcamentos.py` — `TestDashboard` estendido.
- `frontend/app/routes/dashboard.tsx` — 5 cards + 2 gráficos Shadcn, remove radar cru.
- `frontend/app/routes/bi-precos.tsx` — MiniBarChart → Shadcn BarChart.

---

## Task 1: Backend — métricas por status no /dashboard

**Files:**
- Modify: `backend/routers/relatorio_routers.py`
- Test: `tests/test_orcamentos.py` (TestDashboard)

- [ ] **Step 1: Escrever testes (falham primeiro)**

Substituir a classe `TestDashboard` (tests/test_orcamentos.py:596-616) por uma versão estendida. Ela cria orçamentos em status diferentes manipulando o status via DB direto (mais simples que dirigir transições). Usa o fixture `db_session` e o model `Orcamento`. Adicionar no topo do arquivo, se ausente, `from backend.models.orcamento_models import Orcamento` (já importa `Cliente` de lá — somar `Orcamento`).

```python
class TestDashboard:
    def _mk_orc(self, db_session, cliente_id, numero, status, total, custo):
        from decimal import Decimal
        from backend.models.orcamento_models import Orcamento
        o = Orcamento(
            numero=numero, cliente_id=cliente_id, uf_execucao="PR",
            status=status, total_proposta=Decimal(total),
            total_custo_direto=Decimal(custo),
            margem_liquida_real=Decimal("0.20"),
        )
        db_session.add(o)
        db_session.commit()

    def test_dashboard_vazio_200(self):
        d = client.get("/api/v1/dashboard").json()
        for chave in (
            "total_orcado_mes", "total_orcado_acumulado",
            "margem_rs_mes", "margem_rs_acumulado",
            "margem_pct_mes", "margem_pct_acumulado",
            "por_status", "total_orcamentos", "orcamentos_recentes",
        ):
            assert chave in d, chave

    def test_total_orcado_conta_so_enviado(self, db_session, cliente_id):
        self._mk_orc(db_session, cliente_id, "ENV-1", "enviado", "1000", "600")
        self._mk_orc(db_session, cliente_id, "RAS-1", "rascunho", "5000", "100")
        d = client.get("/api/v1/dashboard").json()
        assert float(d["total_orcado_acumulado"]) == 1000.0

    def test_margem_conta_so_fechado(self, db_session, cliente_id):
        self._mk_orc(db_session, cliente_id, "FEC-1", "fechado", "1000", "600")
        self._mk_orc(db_session, cliente_id, "ENV-2", "enviado", "9000", "100")
        d = client.get("/api/v1/dashboard").json()
        # margem R$ = total_proposta - total_custo_direto = 400 (só o fechado)
        assert float(d["margem_rs_acumulado"]) == 400.0
        # margem % = avg(margem_liquida_real) dos fechado = 0.20
        assert abs(float(d["margem_pct_acumulado"]) - 0.20) < 0.0001
```

- [ ] **Step 2: Rodar — espera FAIL (chaves novas ausentes)**

Run: `py -m pytest tests/test_orcamentos.py::TestDashboard -v`
Expected: FAIL (`margem_rs_mes` etc. não existem ainda).

- [ ] **Step 3: Implementar helpers + return no relatorio_routers.py**

Em `backend/routers/relatorio_routers.py`, dentro da função `dashboard` (após a query de `por_status`, antes do `return`), substituir o cálculo antigo de `total_orcado_mes`/`margem_media`/`total_orcado_acumulado`/`margem_acumulada`. Adicionar helpers no nível do módulo (antes da função `dashboard`):

```python
def _soma_proposta_status(db, status_val, desde=None):
    q = db.query(func.sum(Orcamento.total_proposta)).filter(
        Orcamento.status == status_val
    )
    if desde is not None:
        q = q.filter(Orcamento.created_at >= desde)
    return Decimal(str(q.scalar() or 0))


def _soma_margem_rs(db, desde=None):
    q = db.query(
        func.sum(Orcamento.total_proposta - Orcamento.total_custo_direto)
    ).filter(Orcamento.status == "fechado")
    if desde is not None:
        q = q.filter(Orcamento.created_at >= desde)
    return Decimal(str(q.scalar() or 0))


def _media_margem_pct(db, desde=None):
    q = db.query(func.avg(Orcamento.margem_liquida_real)).filter(
        Orcamento.status == "fechado"
    )
    if desde is not None:
        q = q.filter(Orcamento.created_at >= desde)
    r = q.scalar()
    return (
        Decimal(str(r)).quantize(Decimal("0.000001"))
        if r is not None
        else Decimal("0")
    )
```

Substituir o dicionário de retorno da função `dashboard` por (mantendo `por_status`, `total_orcamentos`, `orcamentos_recentes` como já calculados; `primeiro_dia_mes` já existe na função):

```python
    return {
        "total_orcado_mes": _soma_proposta_status(db, "enviado", primeiro_dia_mes),
        "total_orcado_acumulado": _soma_proposta_status(db, "enviado"),
        "margem_rs_mes": _soma_margem_rs(db, primeiro_dia_mes),
        "margem_rs_acumulado": _soma_margem_rs(db),
        "margem_pct_mes": _media_margem_pct(db, primeiro_dia_mes),
        "margem_pct_acumulado": _media_margem_pct(db),
        # alias compat (front antigo / outras telas)
        "margem_media": _media_margem_pct(db, primeiro_dia_mes),
        "margem_acumulada": _media_margem_pct(db),
        "por_status": por_status,
        "total_orcamentos": total_orcamentos,
        "orcamentos_recentes": orcamentos_recentes,
    }
```

Remover as variáveis antigas agora não usadas (`total_orcado_mes`/`resultado_mes`/`margem_media`/`total_acum`/`margem_acumulada` calculadas no corpo) para não deixar código morto — manter apenas `primeiro_dia_mes`, `por_status`, `total_orcamentos`, `recentes`/`orcamentos_recentes`. Confirmar que `Decimal`, `func`, `Orcamento` já estão importados (estão).

- [ ] **Step 4: Rodar — espera PASS**

Run: `py -m pytest tests/test_orcamentos.py::TestDashboard -v`
Expected: PASS (4 testes). Rodar a suíte inteira para garantir zero regressão: `py -m pytest tests/test_orcamentos.py -q` → todos passam (exceto as 2 falhas pré-existentes de soft-delete em test_bd_crud/test_fichas, que não estão neste arquivo).

- [ ] **Step 5: Commit**

```bash
git add backend/routers/relatorio_routers.py tests/test_orcamentos.py
git commit -m "feat(C): dashboard metricas por status (enviado/fechado) + testes"
```

---

## Task 2: Frontend — 5 cards de métricas

**Files:**
- Modify: `frontend/app/routes/dashboard.tsx`

- [ ] **Step 1: Ajustar a derivação de dados**

No corpo do componente `Dashboard` (após `const recentes = ...`), substituir as derivações de valor para selecionar o sufixo conforme o filtro:

```tsx
  const sfx = filtro === "mes" ? "mes" : "acumulado"
  const totalOrcado = dados[`total_orcado_${sfx}`] ?? 0
  const margemRs = dados[`margem_rs_${sfx}`] ?? 0
  const margemPct = dados[`margem_pct_${sfx}`] ?? 0
```

Remover a derivação antiga `margemAcumulada`/`totalOrcado` baseada em `total_orcado_acumulado ?? total_orcado_mes`.

- [ ] **Step 2: Substituir o grid de cards (4 → 5)**

Trocar o `<div className="grid grid-cols-2 gap-4 lg:grid-cols-4">...</div>` por um grid de 5, mantendo o padrão de markup de Card existente:

```tsx
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
        <Card className="p-4">
          <div className="text-muted-foreground text-[0.625rem] font-semibold uppercase tracking-wider">
            {filtro === "mes" ? "Orçado no Mês" : "Total Orçado"}
          </div>
          <div className="text-2xl font-bold mt-2 tabular-nums text-primary">{fmtBRL(totalOrcado)}</div>
          <div className="text-muted-foreground text-[0.5625rem] mt-1">status Enviado</div>
        </Card>
        <Card className="p-4">
          <div className="text-muted-foreground text-[0.625rem] font-semibold uppercase tracking-wider">Margem Líquida</div>
          <div className="text-2xl font-bold mt-2 tabular-nums text-success">{fmtBRL(margemRs)}</div>
          <div className="text-muted-foreground text-[0.5625rem] mt-1">status Fechado</div>
        </Card>
        <Card className="p-4">
          <div className="text-muted-foreground text-[0.625rem] font-semibold uppercase tracking-wider">Margem Média</div>
          <div className="text-2xl font-bold mt-2 tabular-nums">
            {typeof Number(margemPct) === "number" ? `${(Number(margemPct) * 100).toFixed(2)}%` : "—"}
          </div>
          <div className="text-muted-foreground text-[0.5625rem] mt-1">status Fechado</div>
        </Card>
        <Card className="p-4">
          <div className="text-muted-foreground text-[0.625rem] font-semibold uppercase tracking-wider">Total Orçamentos</div>
          <div className="text-2xl font-bold mt-2 tabular-nums">{dados.total_orcamentos || 0}</div>
        </Card>
        <Card className="p-4">
          <div className="text-muted-foreground text-[0.625rem] font-semibold uppercase tracking-wider">Aprovados</div>
          <div className="text-2xl font-bold mt-2 tabular-nums text-success">{porStatus.aprovado || 0}</div>
        </Card>
      </div>
```

- [ ] **Step 3: Commit (parcial — cards prontos, gráficos na Task 3)**

```bash
git add frontend/app/routes/dashboard.tsx
git commit -m "feat(C): dashboard 5 cards de metricas por status"
```

---

## Task 3: Frontend — gráficos do dashboard em Shadcn Charts

**Files:**
- Modify: `frontend/app/routes/dashboard.tsx`

- [ ] **Step 1: Trocar os imports de chart**

No bloco de imports do topo de `dashboard.tsx`, REMOVER os imports diretos de recharts do radar:
```tsx
import { PolarAngleAxis, PolarGrid, Radar, RadarChart } from "recharts"
```
e ADICIONAR os componentes recharts permitidos + o primitive shadcn:
```tsx
import { Bar, BarChart, CartesianGrid, XAxis } from "recharts"
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "~/components/ui/chart"
```

- [ ] **Step 2: Substituir a montagem do radarData por dados de barras + funil**

Trocar o bloco `const fullMark = ...; const radarData = [...]` por:

```tsx
  const statusConfig = {
    value: { label: "Orçamentos", color: "var(--chart-1)" },
  } satisfies ChartConfig

  const statusData = [
    { label: "Rascunho", value: porStatus.rascunho || 0 },
    { label: "Enviado", value: porStatus.enviado || 0 },
    { label: "Aprovado", value: porStatus.aprovado || 0 },
    { label: "Reprovado", value: porStatus.reprovado || 0 },
    { label: "Perdida", value: porStatus.perdida || 0 },
    { label: "Fechado", value: porStatus.fechado || 0 },
  ]

  const funilData = [
    { label: "Enviado", value: porStatus.enviado || 0 },
    { label: "Aprovado", value: porStatus.aprovado || 0 },
    { label: "Fechado", value: porStatus.fechado || 0 },
  ]
```

- [ ] **Step 3: Substituir o Card do radar por dois Cards de BarChart**

Trocar o `<Card>` que contém o `RadarChart` por:

```tsx
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card className="p-4">
          <div className="text-muted-foreground text-[0.625rem] font-semibold uppercase tracking-wider mb-3">
            Distribuição por Status
          </div>
          <ChartContainer config={statusConfig} className="h-[200px] w-full">
            <BarChart data={statusData} accessibilityLayer>
              <CartesianGrid vertical={false} />
              <XAxis dataKey="label" tickLine={false} axisLine={false} tick={{ fontSize: 10 }} />
              <ChartTooltip content={<ChartTooltipContent />} />
              <Bar dataKey="value" fill="var(--color-value)" radius={4} />
            </BarChart>
          </ChartContainer>
        </Card>
        <Card className="p-4">
          <div className="text-muted-foreground text-[0.625rem] font-semibold uppercase tracking-wider mb-3">
            Funil de Conversão
          </div>
          <ChartContainer config={statusConfig} className="h-[200px] w-full">
            <BarChart data={funilData} layout="vertical" accessibilityLayer>
              <CartesianGrid horizontal={false} />
              <XAxis type="number" hide />
              <ChartTooltip content={<ChartTooltipContent />} />
              <Bar dataKey="value" fill="var(--color-value)" radius={4} />
            </BarChart>
          </ChartContainer>
        </Card>
      </div>
```
Nota: no BarChart vertical, o eixo de categorias precisa de `<YAxis dataKey="label" type="category" />`. Adicionar `YAxis` ao import de recharts (`import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts"`) e inserir `<YAxis dataKey="label" type="category" tickLine={false} axisLine={false} width={70} tick={{ fontSize: 10 }} />` dentro do BarChart do funil, antes do `<ChartTooltip>`.

- [ ] **Step 4: Verificar ausência de refs órfãos a recharts cru**

Run (grep): nenhum `RadarChart`, `PolarGrid`, `PolarAngleAxis`, `Radar`, `radarData`, `fullMark` deve restar em `dashboard.tsx`.
```bash
grep -nE "RadarChart|PolarGrid|PolarAngleAxis|\bRadar\b|radarData|fullMark" frontend/app/routes/dashboard.tsx || echo "limpo"
```
Expected: `limpo`.

- [ ] **Step 5: Typecheck se possível, senão self-check**

Se `frontend/node_modules` existir, rodar `npm run typecheck` (ou `build`) no dir frontend. Se ausente, NÃO instalar; confirmar manualmente que: todos os símbolos novos (`ChartContainer`, `ChartTooltip`, `ChartTooltipContent`, `ChartConfig`, `Bar`, `BarChart`, `CartesianGrid`, `XAxis`, `YAxis`) estão importados e que nenhum símbolo removido (radar) é referenciado.

- [ ] **Step 6: Commit**

```bash
git add frontend/app/routes/dashboard.tsx
git commit -m "feat(C): graficos do dashboard em Shadcn Charts (barras + funil)"
```

---

## Task 4: Frontend — bi-precos MiniBarChart → Shadcn

**Files:**
- Modify: `frontend/app/routes/bi-precos.tsx`

- [ ] **Step 1: Ler o arquivo e localizar os 2 usos**

`MiniBarChart` é definido (~linha 78) e usado em dois lugares: `<MiniBarChart data={barrasMensais} height={140} />` (~303) e `<MiniBarChart data={barrasCliente} height={120} />` (~313). Os dados têm forma `{ label, value, max }`.

- [ ] **Step 2: Adicionar imports do chart primitive**

No topo de `bi-precos.tsx`, adicionar:
```tsx
import { Bar, BarChart, CartesianGrid, XAxis } from "recharts"
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "~/components/ui/chart"
```

- [ ] **Step 3: Substituir a função MiniBarChart por um wrapper Shadcn**

Trocar toda a função `MiniBarChart` (linhas ~78-110) por:

```tsx
const biChartConfig = {
  value: { label: "Valor", color: "var(--chart-1)" },
} satisfies ChartConfig

function MiniBarChart({
  data,
  height = 160,
}: {
  data: { label: string; value: number; max?: number }[]
  height?: number
}) {
  if (!data.length)
    return <div className="text-muted-foreground text-xs py-8 text-center">Sem dados</div>
  return (
    <ChartContainer config={biChartConfig} style={{ height }} className="w-full">
      <BarChart data={data} accessibilityLayer>
        <CartesianGrid vertical={false} />
        <XAxis dataKey="label" tickLine={false} axisLine={false} tick={{ fontSize: 9 }} />
        <ChartTooltip content={<ChartTooltipContent />} />
        <Bar dataKey="value" fill="var(--color-value)" radius={3} />
      </BarChart>
    </ChartContainer>
  )
}
```
Mantém a mesma assinatura (`data`, `height`) e os mesmos dois callsites — não muda quem chama. `max` vira opcional (não mais usado).

- [ ] **Step 4: Remover import órfão de fmtNum se ficou sem uso**

`fmtNum` era usado dentro do MiniBarChart antigo. Verificar se ainda é usado em outro lugar do arquivo:
```bash
grep -n "fmtNum" frontend/app/routes/bi-precos.tsx
```
Se a única ocorrência restante for o import (`import { fmtBRL, fmtNum } from "~/lib/format"`), trocar para `import { fmtBRL } from "~/lib/format"`. Se ainda houver uso, deixar como está.

- [ ] **Step 5: Typecheck/self-check**

Mesma regra: typecheck se houver node_modules, senão self-check de imports. Grep `MiniBarChart` deve mostrar só a definição nova + 2 usos; nenhum CSS-bar antigo (`bg-primary/60` dentro do componente removido).

- [ ] **Step 6: Commit**

```bash
git add frontend/app/routes/bi-precos.tsx
git commit -m "feat(C): bi-precos MiniBarChart migrado para Shadcn Charts"
```

---

## Self-Review (preenchido)

**Spec coverage:**
- Total Orçado = enviado → Task 1 (`_soma_proposta_status`). ✓
- Margem Líquida R$ = fechado → Task 1 (`_soma_margem_rs`). ✓
- Margem Média % = fechado → Task 1 (`_media_margem_pct`). ✓
- Filtro mês/acumulado → Task 1 (retorna ambos) + Task 2 (sufixo `sfx`). ✓
- 5 cards → Task 2. ✓
- Dashboard barras + funil Shadcn → Task 3. ✓
- bi-precos → Shadcn → Task 4. ✓
- Sem cor nova → Tasks 3/4 usam `var(--chart-1)`/`var(--color-value)`. ✓
- Testes backend → Task 1 Steps 1-4. ✓

**Placeholder scan:** Os "ler arquivo / localizar usos / grep" são verificações concretas com comando, não placeholders. Cada step de código mostra o código. OK.

**Type consistency:** `MiniBarChart` mantém assinatura `{data, height}` em ambos callsites; `statusConfig`/`biChartConfig` usam `satisfies ChartConfig`; `var(--color-value)` deriva de `value` no config (convenção shadcn) consistente entre Tasks 3 e 4; chaves `margem_rs_*`/`margem_pct_*`/`total_orcado_*` consistentes entre Task 1 (return) e Task 2 (consumo via `sfx`). ✓

## Nota sobre testes

pytest roda via `py -m pytest` (pytest 9.0.3) — confirmado funcionando na sessão. As 2 falhas pré-existentes (`test_bd_crud::test_deletar_bdi`, `test_fichas::test_deletar_ficha_equipe`) são de soft-delete de outra feature, não tocadas aqui. Frontend sem typecheck no sandbox (sem node_modules) — validar por review/grep.
