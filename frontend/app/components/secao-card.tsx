import type { ReactNode } from "react"

import { Card } from "~/components/ui/card"

type Badge = "novo" | "existente" | "sistema"

const BADGE_STYLE: Record<Badge, string> = {
  novo: "bg-primary text-primary-foreground",
  existente: "bg-secondary text-secondary-foreground",
  sistema: "bg-success/15 text-success",
}
const BADGE_LABEL: Record<Badge, string> = {
  novo: "NOVO",
  existente: "EXISTENTE",
  sistema: "SISTEMA",
}

export function SecaoCard({
  id,
  titulo,
  badge,
  children,
}: {
  id: string
  titulo: string
  badge?: Badge
  children: ReactNode
}) {
  return (
    <Card id={id} className="scroll-mt-20 p-5">
      <div className="text-primary mb-3 flex items-center gap-2 border-b pb-2 text-xs font-bold tracking-wide uppercase">
        {titulo}
        {badge && (
          <span
            className={`rounded px-1.5 py-0.5 text-[0.625rem] font-bold ${BADGE_STYLE[badge]}`}
          >
            {BADGE_LABEL[badge]}
          </span>
        )}
      </div>
      <div className="space-y-3">{children}</div>
    </Card>
  )
}
