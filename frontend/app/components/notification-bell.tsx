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
    const load = () => notificacaoApi.list().then(setData).catch(() => {})
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
