import { Badge } from "~/components/ui/badge"

const STATUS_MAP: Record<string, { variant: "secondary" | "warning" | "success" | "destructive"; label: string }> = {
  /* Discord Dark: monocromático — só Rejeitado usa vermelho */
  rascunho:  { variant: "secondary",   label: "RASCUNHO" },
  enviado:   { variant: "warning",     label: "ENVIADO" },
  aprovado:  { variant: "success",     label: "APROVADO" },
  rejeitado: { variant: "destructive", label: "REJEITADO" },
}

/** Badge de status de orçamento — monocromático (Discord Dark). */
export function StatusBadge({ status }: { status: string }) {
  const cfg = STATUS_MAP[status] ?? { variant: "secondary" as const, label: status.toUpperCase() }
  return <Badge variant={cfg.variant}>{cfg.label}</Badge>
}
