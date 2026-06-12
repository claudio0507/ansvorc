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
