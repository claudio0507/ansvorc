import { useEffect, useState } from "react"
import { Link } from "react-router"
import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts"
import {
  ClockIcon,
  TrendUpIcon,
  FileTextIcon,
  FoldersIcon,
} from "@phosphor-icons/react"

import { PageHeader } from "~/components/page-header"
import { StatusBadge } from "~/components/status-badge"
import { Card, CardContent, CardHeader, CardTitle } from "~/components/ui/card"
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "~/components/ui/chart"
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
import { api } from "~/lib/api"
import { fmtBRL, fmtData, fmtPctMlr } from "~/lib/format"

interface DashboardData {
  total_orcamentos?: number
  por_status?: Record<string, number>
  orcamentos_recentes?: any[]
  total_orcado_mes?: number | string
  margem_media?: number | string
}

const STATUS_LABELS: Record<string, string> = {
  rascunho: "Rascunho",
  enviado: "Enviado",
  aprovado: "Aprovado",
  reprovado: "Reprovado",
  perdida: "Perdida",
  fechado: "Fechado",
}

const chartConfig: ChartConfig = {
  n: { label: "Orçamentos", color: "var(--chart-2)" },
}

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [erro, setErro] = useState("")

  useEffect(() => {
    api
      .get<DashboardData>("/dashboard")
      .then(setData)
      .catch((e) => setErro(e.message))
  }, [])

  if (erro) {
    return (
      <>
        <PageHeader title="Dashboard" subtitle="Visão geral das propostas comerciais" />
        <p className="text-destructive">{erro}</p>
      </>
    )
  }

  if (!data) {
    return (
      <>
        <PageHeader title="Dashboard" subtitle="Visão geral das propostas comerciais" />
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
      </>
    )
  }

  const porStatus = data.por_status ?? {}
  const total = data.total_orcamentos ?? 0
  const recentes = data.orcamentos_recentes ?? []
  const pendentes = (porStatus.rascunho ?? 0) + (porStatus.enviado ?? 0)

  const chartData = Object.keys(STATUS_LABELS)
    .map((key) => ({ status: STATUS_LABELS[key], n: porStatus[key] ?? 0 }))
    .filter((d) => d.n > 0)

  const fluxo = Object.keys(STATUS_LABELS).map((key) => ({
    key,
    label: STATUS_LABELS[key],
    n: porStatus[key] ?? 0,
  }))

  const cards = [
    { label: "Total Orçado (mês)", value: fmtBRL(data.total_orcado_mes ?? 0), icon: ClockIcon },
    { label: "Margem Média (MLR)", value: fmtPctMlr(data.margem_media ?? 0), icon: TrendUpIcon },
    { label: "Propostas Pendentes", value: String(pendentes), icon: FileTextIcon },
    { label: "Total de Orçamentos", value: String(total), icon: FoldersIcon },
  ]

  return (
    <>
      <PageHeader title="Dashboard" subtitle="Visão geral das propostas comerciais" />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {cards.map((c) => (
          <Card key={c.label}>
            <CardContent className="flex items-center gap-4">
              <div className="bg-primary/10 text-primary flex size-11 shrink-0 items-center justify-center">
                <c.icon className="size-5" />
              </div>
              <div className="min-w-0">
                <div className="truncate text-xl font-semibold">{c.value}</div>
                <div className="text-muted-foreground text-xs">{c.label}</div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Orçamentos por Status</CardTitle>
          </CardHeader>
          <CardContent>
            {chartData.length === 0 ? (
              <p className="text-muted-foreground py-8 text-center text-sm">
                Nenhum orçamento cadastrado.
              </p>
            ) : (
              <ChartContainer config={chartConfig} className="h-56 w-full">
                <BarChart accessibilityLayer data={chartData} layout="vertical" margin={{ left: 8 }}>
                  <CartesianGrid horizontal={false} />
                  <XAxis type="number" hide />
                  <YAxis
                    type="category"
                    dataKey="status"
                    tickLine={false}
                    axisLine={false}
                    width={80}
                    className="text-xs"
                  />
                  <ChartTooltip content={<ChartTooltipContent />} />
                  <Bar dataKey="n" fill="var(--color-n)" radius={0} />
                </BarChart>
              </ChartContainer>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Fluxo de Aprovação</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              {fluxo.map((s) => (
                <div key={s.key} className="bg-muted/50 flex flex-col items-center gap-1 p-3 text-center">
                  <span className="text-2xl font-semibold">{s.n}</span>
                  <StatusBadge status={s.key} />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader className="flex-row items-center justify-between">
            <CardTitle className="text-sm">Propostas Recentes</CardTitle>
            <Button asChild variant="ghost" size="sm">
              <Link to="/orcamentos">Ver todas →</Link>
            </Button>
          </CardHeader>
          <CardContent className="px-0">
            {recentes.length === 0 ? (
              <p className="text-muted-foreground py-6 text-center text-sm">
                Nenhum orçamento cadastrado.
              </p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Nº Proposta</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Total</TableHead>
                    <TableHead>Data</TableHead>
                    <TableHead></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {recentes.map((o) => (
                    <TableRow key={o.id}>
                      <TableCell className="text-primary font-mono text-xs">
                        {o.numero}
                      </TableCell>
                      <TableCell>
                        <StatusBadge status={o.status} />
                      </TableCell>
                      <TableCell className="text-right font-semibold">
                        {fmtBRL(o.total_proposta)}
                      </TableCell>
                      <TableCell className="text-muted-foreground text-xs">
                        {fmtData(o.created_at)}
                      </TableCell>
                      <TableCell>
                        <Button asChild variant="ghost" size="sm">
                          <Link to={`/orcamentos/${o.id}`}>Abrir →</Link>
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </>
  )
}
