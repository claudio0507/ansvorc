import { useEffect, useState } from "react"
import { Link } from "react-router"
import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts"
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "~/components/ui/chart"
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

  const sfx = filtro === "mes" ? "mes" : "acumulado"
  const totalOrcado = dados[`total_orcado_${sfx}`] ?? 0
  const margemRs = dados[`margem_rs_${sfx}`] ?? 0
  const margemPct = dados[`margem_pct_${sfx}`] ?? 0
  const porStatus = dados.por_status || {}
  const recentes = dados.orcamentos_recentes || []

  const statusConfig = {
    value: { label: "Orçamentos", color: "var(--chart-1)" },
  } satisfies ChartConfig

  const statusData = [
    { label: "Rascunho", value: porStatus.rascunho || 0 },
    { label: "Enviado", value: porStatus.enviado || 0 },
    { label: "Aprovado", value: porStatus.aprovado || 0 },
    { label: "Reprovado", value: porStatus.reprovado || 0 },
    { label: "Perdida", value: porStatus.perdida || 0 },
    { label: "Fechado", value: porStatus.fechado || 0 },
  ]

  const funilData = [
    { label: "Enviado", value: porStatus.enviado || 0 },
    { label: "Aprovado", value: porStatus.aprovado || 0 },
    { label: "Fechado", value: porStatus.fechado || 0 },
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

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
        <Card className="p-4">
          <div className="text-muted-foreground text-[0.625rem] font-semibold uppercase tracking-wider">
            {filtro === "mes" ? "Orçado no Mês" : "Total Orçado"}
          </div>
          <div className="text-2xl font-bold mt-2 tabular-nums text-primary">{fmtBRL(totalOrcado)}</div>
          <div className="text-muted-foreground text-[0.5625rem] mt-1">status Enviado</div>
        </Card>
        <Card className="p-4">
          <div className="text-muted-foreground text-[0.625rem] font-semibold uppercase tracking-wider">Margem Líquida</div>
          <div className="text-2xl font-bold mt-2 tabular-nums text-success">{fmtBRL(margemRs)}</div>
          <div className="text-muted-foreground text-[0.5625rem] mt-1">status Fechado</div>
        </Card>
        <Card className="p-4">
          <div className="text-muted-foreground text-[0.625rem] font-semibold uppercase tracking-wider">Margem Média</div>
          <div className="text-2xl font-bold mt-2 tabular-nums">{`${(Number(margemPct) * 100).toFixed(2)}%`}</div>
          <div className="text-muted-foreground text-[0.5625rem] mt-1">status Fechado</div>
        </Card>
        <Card className="p-4">
          <div className="text-muted-foreground text-[0.625rem] font-semibold uppercase tracking-wider">Total Orçamentos</div>
          <div className="text-2xl font-bold mt-2 tabular-nums">{dados.total_orcamentos || 0}</div>
        </Card>
        <Card className="p-4">
          <div className="text-muted-foreground text-[0.625rem] font-semibold uppercase tracking-wider">Aprovados</div>
          <div className="text-2xl font-bold mt-2 tabular-nums text-success">{porStatus.aprovado || 0}</div>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card className="p-4">
          <div className="text-muted-foreground text-[0.625rem] font-semibold uppercase tracking-wider mb-3">
            Distribuição por Status
          </div>
          <ChartContainer config={statusConfig} className="h-[200px] w-full">
            <BarChart data={statusData} accessibilityLayer>
              <CartesianGrid vertical={false} />
              <XAxis dataKey="label" tickLine={false} axisLine={false} tick={{ fontSize: 10 }} />
              <ChartTooltip content={<ChartTooltipContent />} />
              <Bar dataKey="value" fill="var(--color-value)" radius={4} />
            </BarChart>
          </ChartContainer>
        </Card>
        <Card className="p-4">
          <div className="text-muted-foreground text-[0.625rem] font-semibold uppercase tracking-wider mb-3">
            Funil de Conversão
          </div>
          <ChartContainer config={statusConfig} className="h-[200px] w-full">
            <BarChart data={funilData} layout="vertical" accessibilityLayer>
              <CartesianGrid horizontal={false} />
              <XAxis type="number" hide />
              <YAxis dataKey="label" type="category" tickLine={false} axisLine={false} width={70} tick={{ fontSize: 10 }} />
              <ChartTooltip content={<ChartTooltipContent />} />
              <Bar dataKey="value" fill="var(--color-value)" radius={4} />
            </BarChart>
          </ChartContainer>
        </Card>
      </div>

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
