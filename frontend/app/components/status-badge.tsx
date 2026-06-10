import { Badge } from "~/components/ui/badge"

const STATUS_MAP: Record<string, { variant: "secondary" | "warning" | "success" | "destructive"; label: string }> = {
  rascunho: { variant: "secondary", label: "Rascunho" },
  enviado: { variant: "warning", label: "Enviado" },
  aprovado: { variant: "success", label: "Aprovado" },
  rejeitado: { variant: "destructive", label: "Rejeitado" },
}

/** Badge de status de orçamento — cores de alerta (verde/âmbar/vermelho) mantidas. */
export function StatusBadge({ status }: { status: string }) {
  const cfg = STATUS_MAP[status] ?? { variant: "secondary" as const, label: status }
  return <Badge variant={cfg.variant}>{cfg.label}</Badge>
}
