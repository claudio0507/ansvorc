import { useEffect, useState } from "react"
import { Link } from "react-router"
import {
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
} from "recharts"
import {
  ClockIcon,
  TrendUpIcon,
  FileTextIcon,
  FoldersIcon,
} from "@phosphor-icons/react"

import { PageHeader } from "~/components/page-header"
import { StatusBadge } from "~/components/status-badge"
import { Card } from "~/components/ui/card"
import { Skeleton } from "~/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "~/components/ui/table"
import { Button } from "~/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "~/components/ui/select"
import { api } from "~/lib/api"
import { fmtBRL } from "~/lib/format"

export default function Dashboard() {
  const [dados, setDados] = useState<any>(null)
  const [erro, setErro] = useState("")
  const [filtro, setFiltro] = useState<"mes" | "acumulado">("acumulado")

  useEffect(() => {
    api.get<any>("/dashboard").then(setDados).catch((e) => setErro(e.message))
  }, [])

  if (erro) return <div className="text-destructive py-12 text-center">{erro}</div>
  if (!dados) return <Skeleton className="h-64 w-full" />

  const totalOrcado = filtro === "mes" ? dados.total_orcado_mes : dados.total_orcado_acumulado ?? dados.total_orcado_mes
  const margemAcumulada = dados.margem_acumulada ?? dados.margem_media ?? 0
  const porStatus = dados.por_status || {}
  const recentes = dados.orcamentos_recentes || []

  // Radar data: status distribution
  const radarData = [
    { status: "Rascunho", value: porStatus.rascunho || 0, fullMark: Math.max(1, dados.total_orcamentos || 1) },
    { status: "Enviado", value: porStatus.enviado || 0, fullMark: Math.max(1, dados.total_orcamentos || 1) },
    { status: "Aprovado", value: porStatus.aprovado || 0, fullMark: Math.max(1, dados.total_orcamentos || 1) },
    { status: "Rejeitado", value: porStatus.rejeitado || 0, fullMark: Math.max(1, dados.total_orcamentos || 1) },
  ]

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard"
        subtitle="Painel de controle"
        actions={
          <Select value={filtro} onValueChange={(v) => setFiltro(v as "mes" | "acumulado")}>
            <SelectTrigger className="h-8 w-32 text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="acumulado">Acumulado</SelectItem>
              <SelectItem value="mes">Este Mês</SelectItem>
            </SelectContent>
          </Select>
        }
      />

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Card className="p-4">
          <div className="text-muted-foreground text-[0.625rem] font-semibold uppercase tracking-wider">
            {filtro === "mes" ? "Orçado no Mês" : "Total Orçado"}
          </div>
          <div className="text-2xl font-bold mt-2 tabular-nums text-primary">
            {fmtBRL(totalOrcado)}
          </div>
        </Card>
        <Card className="p-4">
          <div className="text-muted-foreground text-[0.625rem] font-semibold uppercase tracking-wider">
            Margem Líquida Acumulada
          </div>
          <div className="text-2xl font-bold mt-2 tabular-nums">
            {typeof margemAcumulada === "number" ? `${(margemAcumulada * 100).toFixed(2)}%` : "—"}
          </div>
        </Card>
        <Card className="p-4">
          <div className="text-muted-foreground text-[0.625rem] font-semibold uppercase tracking-wider">
            Total Orçamentos
          </div>
          <div className="text-2xl font-bold mt-2 tabular-nums">
            {dados.total_orcamentos || 0}
          </div>
        </Card>
        <Card className="p-4">
          <div className="text-muted-foreground text-[0.625rem] font-semibold uppercase tracking-wider">
            Aprovados
          </div>
          <div className="text-2xl font-bold mt-2 tabular-nums text-success">
            {porStatus.aprovado || 0}
          </div>
        </Card>
      </div>

      {/* Radar Chart */}
      <Card className="p-4">
        <div className="text-muted-foreground text-[0.625rem] font-semibold uppercase tracking-wider mb-3">
          Distribuição por Status
        </div>
        <div className="flex justify-center">
          <RadarChart width={280} height={200} data={radarData} cx="50%" cy="50%" outerRadius="70%">
            <PolarGrid stroke="oklch(0.55 0.005 250)" />
            <PolarAngleAxis
              dataKey="status"
              tick={{ fontSize: 10, fill: "oklch(0.55 0.005 250)" }}
            />
            <Radar
              dataKey="value"
              stroke="oklch(0.536 0.189 24.67)"
              fill="oklch(0.536 0.189 24.67)"
              fillOpacity={0.15}
            />
          </RadarChart>
        </div>
      </Card>

      {/* Últimos orçamentos */}
      <Card className="overflow-x-auto py-0">
        <div className="text-muted-foreground text-[0.625rem] font-semibold uppercase tracking-wider px-4 py-3 border-b border-border">
          Orçamentos Recentes
        </div>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="h-7 text-[0.625rem]">Número</TableHead>
              <TableHead className="h-7 text-[0.625rem]">Status</TableHead>
              <TableHead className="h-7 text-[0.625rem] text-right">Total</TableHead>
              <TableHead className="h-7 text-[0.625rem]">Data</TableHead>
              <TableHead className="h-7 text-[0.625rem] w-8"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {recentes.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="text-muted-foreground py-6 text-center text-xs">
                  Nenhum orçamento encontrado.
                </TableCell>
              </TableRow>
            ) : (
              recentes.map((o: any) => (
                <TableRow key={o.id}>
                  <TableCell className="font-medium text-xs">{o.numero ?? o.id}</TableCell>
                  <TableCell><StatusBadge status={o.status} /></TableCell>
                  <TableCell className="text-right text-xs tabular-nums">{fmtBRL(o.total_proposta)}</TableCell>
                  <TableCell className="text-muted-foreground text-xs">
                    {o.created_at ? new Date(o.created_at).toLocaleDateString("pt-BR") : "—"}
                  </TableCell>
                  <TableCell>
                    <Button asChild size="sm" variant="ghost" className="h-7 text-xs">
                      <Link to={`/orcamentos/${o.id}`}>Abrir</Link>
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </Card>
    </div>
  )
}
