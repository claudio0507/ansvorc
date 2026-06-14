# Sub-projeto C — Dashboard (métricas por status + Shadcn Charts)

**Data:** 2026-06-12
**Branch alvo:** feat/melhorias-v2
**Contexto:** Terceiro de 4 sub-projetos da demanda v2 (A=status ✅, B=prazos/notificações, C=dashboard, D=orçamento+proposta). Depende de A (os 6 estados já existem). O dashboard pós-merge já tem um radar (recharts cru) com os 6 estados e cards que somam TODOS os orçamentos — C redefine as métricas por status e migra os gráficos para Shadcn Charts.

## Objetivo

1. Redefinir métricas: **Total Orçado** = Σ dos `enviado`; **Margem Líquida (R$)** e **Margem Média (%)** = dos `fechado`.
2. Migrar todos os gráficos (dashboard + bi-precos) para **Shadcn UI Charts** (`ChartContainer`), reusando os tokens `--chart-1..5` já definidos (sem cor nova).
3. Dashboard ganha gráfico de barras por status + funil de conversão.

## Decisões travadas (brainstorm)

- Total Orçado = Σ `total_proposta` dos `enviado`. Margem Líquida = Σ (`total_proposta − total_custo_direto`) dos `fechado` (lucro bruto R$). Margem Média = `avg(margem_liquida_real)` dos `fechado` (%).
- Filtro **mês/acumulado** existente aplica às métricas por status.
- **5 cards**: Total Orçado, Margem Líquida (R$), Margem Média (%), Total Orçamentos, Aprovados.
- Migrar **dashboard E bi-precos** para Shadcn Charts agora.
- Dashboard: **barras por status + funil de conversão** (substitui o radar cru).
- **Sem cor nova** — usar `var(--chart-N)` já no tema.

## Seção 1 — Backend: métricas por status

Endpoint `GET /dashboard` em `backend/routers/relatorio_routers.py`. Substituir os cálculos de total orçado e margem por versões filtradas por status, retornando mês + acumulado para o front alternar sem refetch.

```python
def _soma_total_proposta(db, status_val, desde=None):
    q = db.query(func.sum(Orcamento.total_proposta)).filter(Orcamento.status == status_val)
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
    q = db.query(func.avg(Orcamento.margem_liquida_real)).filter(Orcamento.status == "fechado")
    if desde is not None:
        q = q.filter(Orcamento.created_at >= desde)
    r = q.scalar()
    return Decimal(str(r)).quantize(Decimal("0.000001")) if r is not None else Decimal("0")
```

Retorno do endpoint (mantém `por_status`, `total_orcamentos`, `orcamentos_recentes`; adiciona/renomeia):

```python
return {
    "total_orcado_mes": _soma_total_proposta(db, "enviado", primeiro_dia_mes),
    "total_orcado_acumulado": _soma_total_proposta(db, "enviado"),
    "margem_rs_mes": _soma_margem_rs(db, primeiro_dia_mes),
    "margem_rs_acumulado": _soma_margem_rs(db),
    "margem_pct_mes": _media_margem_pct(db, primeiro_dia_mes),
    "margem_pct_acumulado": _media_margem_pct(db),
    "por_status": por_status,            # 6 estados (já correto)
    "total_orcamentos": total_orcamentos,
    "orcamentos_recentes": orcamentos_recentes,
}
```

Compatibilidade: manter as chaves antigas `margem_media`/`margem_acumulada` como alias dos novos `margem_pct_*` se algo externo depender — opcional; o front será atualizado de qualquer forma.

## Seção 2 — Frontend: 5 cards

`frontend/app/routes/dashboard.tsx`. Grid `lg:grid-cols-5`. Cada card de status mostra subtítulo da base ("status Enviado"/"status Fechado") para clareza.

| Card | Fonte | Formato |
|------|-------|---------|
| Total Orçado | total_orcado_{mes/acumulado} | fmtBRL |
| Margem Líquida | margem_rs_{mes/acumulado} | fmtBRL |
| Margem Média | margem_pct_{mes/acumulado} × 100 | % 2 casas |
| Total Orçamentos | total_orcamentos | número |
| Aprovados | por_status.aprovado | número |

O filtro mês/acumulado (Select existente no PageHeader) seleciona o sufixo `_mes`/`_acumulado`. Cores só com tokens existentes (`text-primary`, `text-success`, `text-foreground`).

## Seção 3 — Frontend: gráficos Shadcn Charts

O primitive `frontend/app/components/ui/chart.tsx` já existe e exporta `ChartContainer`, `ChartTooltip`, `ChartTooltipContent`, `ChartConfig`. recharts (`^3.8.0`) já instalado. Tokens `--chart-1..5` já no tema (`app.css`).

### Dashboard — dois gráficos (substitui o radar cru)

1. Distribuição por status — `BarChart` dos 6 estados a partir de `por_status`.
2. Funil de conversão — `BarChart` (layout horizontal) de Enviado → Aprovado → Fechado.

```tsx
const statusConfig = { value: { label: "Orçamentos", color: "var(--chart-1)" } } satisfies ChartConfig

<ChartContainer config={statusConfig} className="h-[200px] w-full">
  <BarChart data={statusData} accessibilityLayer>
    <CartesianGrid vertical={false} />
    <XAxis dataKey="label" tickLine={false} axisLine={false} tick={{ fontSize: 10 }} />
    <ChartTooltip content={<ChartTooltipContent />} />
    <Bar dataKey="value" fill="var(--color-value)" radius={4} />
  </BarChart>
</ChartContainer>
```

`statusData = [{label:"Rascunho", value:porStatus.rascunho||0}, ... 6 estados]`.
`funilData = [{label:"Enviado",...},{label:"Aprovado",...},{label:"Fechado",...}]`.

Remover do dashboard: o `RadarChart`/`PolarGrid`/`PolarAngleAxis`/`Radar` crus e seus imports diretos de `recharts`; substituir por imports de `~/components/ui/chart` + os componentes recharts permitidos (`BarChart`, `Bar`, `XAxis`, `CartesianGrid`).

### bi-precos — MiniBarChart → Shadcn

`frontend/app/routes/bi-precos.tsx`: substituir a função caseira `MiniBarChart` (CSS bars) por `BarChart` dentro de `ChartContainer`. Dois consumidores (`barrasMensais`, `barrasCliente`), mesma forma `{label, value}`. Remover a função `MiniBarChart` e `fmtNum` se ficar órfão.

## Testes

- Backend: estender `tests/test_orcamentos.py::TestDashboard` — criar orçamentos em `enviado`, `fechado` e outros; assertar que `total_orcado_*` conta só enviado, `margem_rs_*`/`margem_pct_*` contam só fechado, e `por_status` reflete todos.
- Frontend: sem typecheck no sandbox (sem node_modules). Validar por review/grep — imports corretos, sem refs órfãos a recharts cru/MiniBarChart, sem cor nova.

## Arquivos tocados

- `backend/routers/relatorio_routers.py`
- `frontend/app/routes/dashboard.tsx`
- `frontend/app/routes/bi-precos.tsx`
- `tests/test_orcamentos.py`

## Fora de escopo (B/D)

Notificações, sino, calendário de data_limite (B). Proposta, Enter→Calcular, unidade do Produto, preço dinâmico (D).
