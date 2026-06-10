/** Helpers de formatação pt-BR (port de dashboard.js / orcamentos.js). */

export function fmtBRL(v: number | string | null | undefined): string {
  const n = typeof v === "number" ? v : parseFloat(String(v ?? 0)) || 0
  return n.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })
}

export function fmtPct(v: number | string | null | undefined, frac = 2): string {
  const n = typeof v === "number" ? v : parseFloat(String(v ?? 0)) || 0
  return (n * 100).toFixed(frac) + "%"
}

export function fmtPctMlr(v: number | string | null | undefined): string {
  const n = typeof v === "number" ? v : parseFloat(String(v ?? 0)) || 0
  return (
    (n * 100).toLocaleString("pt-BR", {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    }) + "%"
  )
}

export function fmtNum(v: number | string | null | undefined): string {
  const n = typeof v === "number" ? v : parseFloat(String(v ?? 0)) || 0
  return n.toLocaleString("pt-BR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 4,
  })
}

export function fmtData(iso: string | null | undefined): string {
  if (!iso) return "—"
  return new Date(iso).toLocaleDateString("pt-BR")
}
