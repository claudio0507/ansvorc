# Sub-projeto B — Prazos + Notificações

**Data:** 2026-06-12
**Branch alvo:** feat/melhorias-v2
**Contexto:** Quarto/último dos sub-projetos da demanda v2 (A=status ✅, C=dashboard ✅, B=prazos/notificações, D=proposta). Depende de A (`data_limite` já existe no orçamento). Não há infra de notificação no projeto — construído do zero.

## Objetivo

1. Sino de notificações no topbar com badge de contagem de prazos de envio iminentes/atrasados.
2. Motor de alerta no backend: orçamentos `rascunho`/`reprovado` com `data_limite` atrasado, hoje (D-0) ou amanhã (D-1).
3. Calendário de prazos no dashboard (shadcn Calendar) + lista lateral dos prazos do dia.

## Decisões travadas (brainstorm)

- Lógica de alerta no **backend** (endpoint), frontend só exibe.
- Alerta só orçamentos em **rascunho/reprovado** (ainda não enviados) com `data_limite` não-nula.
- 3 urgências: `atrasado` (< hoje), `hoje` (== hoje), `amanha` (== hoje+1).
- Sem estado lida/não-lida — **badge = contagem de pendentes**.
- Sino atualiza por **polling ~5min + ao montar** (sem WebSocket).
- Calendário: **shadcn Calendar** (adiciona `react-day-picker` + `date-fns` + `ui/calendar.tsx`) + **lista lateral** dos prazos do dia.
- Badge e marcação de dia usam **`bg-destructive`** (token existente, sem cor nova).

## Seção 1 — Backend: `/notificacoes`

`GET /api/v1/notificacoes` em `backend/routers/relatorio_routers.py`. Computa prazos que exigem ação.

```python
from datetime import date, timedelta

@router.get("/notificacoes")
def listar_notificacoes(db: Session = Depends(get_db)) -> dict:
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
    def urg(d):
        return "atrasado" if d < hoje else "hoje" if d == hoje else "amanha"
    itens = [
        {"id": o.id, "numero": o.numero, "obra": o.obra,
         "data_limite": o.data_limite, "urgencia": urg(o.data_limite)}
        for o in orcs
    ]
    return {"total": len(itens), "notificacoes": itens}
```

RBAC: registrar `("/api/v1/notificacoes", _TODOS_PAPEIS)` no `backend/middleware.py`.

## Seção 2 — Backend: `/prazos`

`GET /api/v1/prazos?mes=YYYY-MM` (default mês atual) em `relatorio_routers.py`. Todos os orçamentos `rascunho`/`reprovado` com `data_limite` no mês (para o calendário, que mostra além de D-1).

```python
@router.get("/prazos")
def listar_prazos(mes: str | None = None, db: Session = Depends(get_db)) -> list[dict]:
    hoje = date.today()
    if mes:
        ano, m = int(mes[:4]), int(mes[5:7])
    else:
        ano, m = hoje.year, hoje.month
    inicio = date(ano, m, 1)
    fim = date(ano + (m == 12), (m % 12) + 1, 1)  # 1º dia do mês seguinte
    orcs = (
        db.query(Orcamento)
        .filter(Orcamento.status.in_(["rascunho", "reprovado"]))
        .filter(Orcamento.data_limite.isnot(None))
        .filter(Orcamento.data_limite >= inicio, Orcamento.data_limite < fim)
        .order_by(Orcamento.data_limite)
        .all()
    )
    def urg(d):
        return "atrasado" if d < hoje else "hoje" if d == hoje else (
            "amanha" if d == hoje + timedelta(days=1) else "futuro"
        )
    return [
        {"id": o.id, "numero": o.numero, "obra": o.obra,
         "data_limite": o.data_limite, "urgencia": urg(o.data_limite)}
        for o in orcs
    ]
```

RBAC: `("/api/v1/prazos", _TODOS_PAPEIS)` no middleware. (Nota: o prefixo `/api/v1/prazos` é distinto, não colide com outros prefixos RBAC existentes.)

## Seção 3 — Frontend: sino de notificações

Novo `frontend/app/components/notification-bell.tsx`, montado no header de `frontend/app/routes/_app.tsx` (dentro do `<div className="ml-auto flex items-center gap-1">`, entre o toggle dark e o botão Sair).

```tsx
export function NotificationBell() {
  const [data, setData] = useState<{ total: number; notificacoes: any[] }>({ total: 0, notificacoes: [] })
  useEffect(() => {
    const load = () => api.get("/notificacoes").then(setData).catch(() => {})
    load()
    const t = setInterval(load, 5 * 60 * 1000)
    return () => clearInterval(t)
  }, [])
  // DropdownMenu (ui/dropdown-menu.tsx já existe) com BellIcon, badge bg-destructive(total),
  // lista de notificações (numero, obra, chip urgencia, link /orcamentos/{id}),
  // empty "Nenhum prazo próximo."
}
```

- Badge: círculo sobreposto com `total`, `bg-destructive`, some quando `total === 0`.
- Chip de urgência: Atrasado/Hoje/Amanhã com tokens existentes.
- `api.get("/notificacoes")` — método novo `notificacaoApi` em `lib/api.ts`.

## Seção 4 — Frontend: calendário de prazos no dashboard

Deps novas: `react-day-picker`, `date-fns` em `frontend/package.json`. Novo `frontend/app/components/ui/calendar.tsx` (componente oficial shadcn, tokens do tema, sem cor nova).

Novo `frontend/app/components/prazos-calendar.tsx`, renderizado no dashboard abaixo dos gráficos:

- `<Calendar mode="single" selected={dia} onSelect={...} month={mes} onMonthChange={...} modifiers={{ comPrazo: datasComPrazo }} modifiersClassNames={{ comPrazo: "bg-destructive/20 ..." }} />` — dias com prazo marcados.
- Troca de mês → `prazoApi.list(mesStr)` recarrega.
- Lista lateral: orçamentos com `data_limite` no dia selecionado (default hoje) — numero, obra, chip urgência, link. Empty "Sem prazos neste dia."
- `prazoApi` em `lib/api.ts`: `list: (mes?: string) => api.get("/prazos" + (mes ? "?mes=" + mes : ""))`.

Montagem no dashboard: importar e renderizar `<PrazosCalendar />` em `frontend/app/routes/dashboard.tsx` após o bloco de gráficos.

## Testes

- Backend: novo `tests/test_notificacoes.py` — criar orçamentos com `data_limite` ontem/hoje/amanhã/depois e status variados; assertar `/notificacoes` traz só rascunho/reprovado até amanhã com urgência correta, e `/prazos?mes=` filtra por mês corretamente. Rodar via `py -m pytest`.
- Frontend: sem typecheck no sandbox (sem node_modules). Validar por review/grep — imports, sem cor nova, montagem correta.

## Arquivos tocados

- `backend/routers/relatorio_routers.py` (2 endpoints)
- `backend/middleware.py` (2 entradas RBAC)
- `frontend/package.json` (2 deps)
- `frontend/app/components/ui/calendar.tsx` (novo, shadcn)
- `frontend/app/components/notification-bell.tsx` (novo)
- `frontend/app/components/prazos-calendar.tsx` (novo)
- `frontend/app/routes/_app.tsx` (monta o sino)
- `frontend/app/routes/dashboard.tsx` (monta o calendário)
- `frontend/app/lib/api.ts` (notificacaoApi, prazoApi)
- `tests/test_notificacoes.py` (novo)

## Fora de escopo

Notificações de outros eventos (aprovação, rejeição); estado lida/não-lida persistido; WebSocket/real-time; lembrete por e-mail.
