import { useCallback, useEffect, useState } from "react"
import { toast } from "sonner"

import { PageHeader } from "~/components/page-header"
import { Badge } from "~/components/ui/badge"
import { Button } from "~/components/ui/button"
import { Card } from "~/components/ui/card"
import { Input } from "~/components/ui/input"
import { Label } from "~/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "~/components/ui/select"
import { Skeleton } from "~/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "~/components/ui/table"
import { Bar, BarChart, CartesianGrid, XAxis } from "recharts"
import { biApi, fichaApi, produtoApi } from "~/lib/api"
import { fmtBRL, fmtNum } from "~/lib/format"
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "~/components/ui/chart"

// ── Tipos ───────────────────────────────────────────────────────────────────

interface BiResponse {
  item: { tipo: string; id: number; nome: string }
  metricas: Metricas | null
  serie_temporal: SerieItem[]
  precos_por_cliente: ClienteItem[]
  dados_detalhados: Detalhe[]
  mensagem?: string
}

interface Metricas {
  preco_medio: number
  preco_max: number
  preco_min: number
  preco_atual: number
  variacao_pct: number
  num_orcamentos: number
  num_registros: number
}

interface SerieItem {
  mes: string
  preco_medio: number
  preco_min: number
  preco_max: number
  contagem: number
}

interface ClienteItem {
  cliente: string
  preco_medio: number
  preco_min: number
  preco_max: number
  contagem: number
}

interface Detalhe {
  data: string
  orcamento_numero: string
  cliente: string
  obra: string
  preco_unitario: number
  quantidade: number
  valor_total: number
}

// ── Gráfico de barras (Shadcn Charts) ──────────────────────────────────────

const biChartConfig = {
  value: { label: "Valor", color: "var(--chart-1)" },
} satisfies ChartConfig

function MiniBarChart({
  data,
  height = 160,
}: {
  data: { label: string; value: number; max?: number }[]
  height?: number
}) {
  if (!data.length)
    return <div className="text-muted-foreground text-xs py-8 text-center">Sem dados</div>
  return (
    <ChartContainer config={biChartConfig} style={{ height }} className="w-full">
      <BarChart data={data} accessibilityLayer>
        <CartesianGrid vertical={false} />
        <XAxis dataKey="label" tickLine={false} axisLine={false} tick={{ fontSize: 9 }} />
        <ChartTooltip content={<ChartTooltipContent />} />
        <Bar dataKey="value" fill="var(--color-value)" radius={3} />
      </BarChart>
    </ChartContainer>
  )
}

// ── Componente principal ────────────────────────────────────────────────────

export default function BiPrecos() {
  const [tipo, setTipo] = useState("servico")
  const [itens, setItens] = useState<any[]>([])
  const [itemId, setItemId] = useState("")
  const [meses, setMeses] = useState("12")
  const [dados, setDados] = useState<BiResponse | null>(null)
  const [carregando, setCarregando] = useState(false)

  // Carregar lista de itens conforme tipo
  const carregarItens = useCallback(async () => {
    try {
      if (tipo === "servico") {
        const lista = await fichaApi.listServicos()
        setItens(lista.map((s: any) => ({ id: s.id, nome: s.nome || s.codigo })))
      } else if (tipo === "produto") {
        const lista = await produtoApi.listProdutos()
        setItens(lista.map((p: any) => ({ id: p.id, nome: p.nome })))
      } else {
        const lista = await produtoApi.listComponentes()
        setItens(lista.map((c: any) => ({ id: c.id, nome: c.nome })))
      }
      setItemId("")
    } catch (err: any) {
      toast.error(`Erro ao carregar itens: ${err.message}`)
    }
  }, [tipo])

  useEffect(() => {
    carregarItens()
  }, [carregarItens])

  async function consultar() {
    if (!itemId) {
      toast.error("Selecione um item")
      return
    }
    setCarregando(true)
    try {
      const res = await biApi.precos(tipo, Number(itemId), Number(meses))
      setDados(res)
    } catch (err: any) {
      toast.error(`Erro: ${err.message}`)
    } finally {
      setCarregando(false)
    }
  }

  // Preparar dados para gráficos
  const barrasMensais = (dados?.serie_temporal || []).map((s) => ({
    label: s.mes.slice(2).replace("-", "/"), // "24/01"
    value: Number(s.preco_medio),
    max: Math.max(...(dados?.serie_temporal || []).map((x) => Number(x.preco_max)), 1),
  }))

  const barrasCliente = (dados?.precos_por_cliente || []).map((c) => ({
    label: c.cliente.length > 10 ? c.cliente.slice(0, 10) + "…" : c.cliente,
    value: Number(c.preco_medio),
    max: Math.max(...(dados?.precos_por_cliente || []).map((x) => Number(x.preco_medio)), 1),
  }))

  // Export CSV
  function exportarCSV() {
    if (!dados?.dados_detalhados.length) return
    const linhas = [
      "Data;Orçamento;Cliente;Obra;Preço Unit;QTD;Valor Total",
      ...dados.dados_detalhados.map((d) =>
        [d.data?.slice(0, 10) || "", d.orcamento_numero, d.cliente, d.obra,
         d.preco_unitario, d.quantidade, d.valor_total].join(";")
      ),
    ]
    const blob = new Blob([linhas.join("\n")], { type: "text/csv;charset=utf-8" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `bi-precos-${dados.item.nome.replace(/\s+/g, "-")}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="BI — Histórico de Preços"
        subtitle="Acompanhamento estatístico de preços praticados em orçamentos aprovados"
      />

      {/* Filtros */}
      <Card className="p-4">
        <div className="flex flex-wrap gap-3 items-end">
          <div className="flex flex-col gap-1.5">
            <Label className="text-[0.625rem]">Tipo</Label>
            <Select value={tipo} onValueChange={(v) => setTipo(v)}>
              <SelectTrigger className="h-8 w-36 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="servico">Serviço</SelectItem>
                <SelectItem value="produto">Produto</SelectItem>
                <SelectItem value="componente">Componente</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex flex-col gap-1.5 flex-1 min-w-[200px]">
            <Label className="text-[0.625rem]">Item</Label>
            <Select value={itemId} onValueChange={setItemId}>
              <SelectTrigger className="h-8 text-xs">
                <SelectValue placeholder="Selecione..." />
              </SelectTrigger>
              <SelectContent>
                {itens.map((i: any) => (
                  <SelectItem key={i.id} value={String(i.id)}>
                    {i.nome}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label className="text-[0.625rem]">Período (meses)</Label>
            <Input
              type="number"
              min={1}
              max={60}
              value={meses}
              onChange={(e) => setMeses(e.target.value)}
              className="h-8 w-20 text-xs"
            />
          </div>
          <Button size="sm" onClick={consultar} disabled={carregando} className="h-8">
            {carregando ? "Consultando…" : "Consultar"}
          </Button>
          {dados?.dados_detalhados?.length ? (
            <Button size="sm" variant="secondary" onClick={exportarCSV} className="h-8">
              Exportar CSV
            </Button>
          ) : null}
        </div>
      </Card>

      {carregando && (
        <div className="space-y-4">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-40 w-full" />
          <Skeleton className="h-40 w-full" />
        </div>
      )}

      {dados && !carregando && (
        <>
          {/* Mensagem vazia */}
          {dados.mensagem && (
            <Card className="p-8 text-center text-muted-foreground text-sm">
              {dados.mensagem}
            </Card>
          )}

          {/* Métricas */}
          {dados.metricas && (
            <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
              {[
                { label: "Preço Médio", value: fmtBRL(dados.metricas.preco_medio) },
                { label: "Preço Máx", value: fmtBRL(dados.metricas.preco_max) },
                { label: "Preço Mín", value: fmtBRL(dados.metricas.preco_min) },
                { label: "Preço Atual", value: fmtBRL(dados.metricas.preco_atual) },
                {
                  label: "Variação",
                  value: `${dados.metricas.variacao_pct > 0 ? "+" : ""}${dados.metricas.variacao_pct.toFixed(1)}%`,
                  cor: dados.metricas.variacao_pct > 0 ? "text-destructive" : dados.metricas.variacao_pct < 0 ? "text-success" : "",
                },
                { label: "Nº Orçamentos", value: String(dados.metricas.num_orcamentos) },
              ].map((m, i) => (
                <Card key={i} className="p-3 text-center">
                  <div className="text-[0.5625rem] text-muted-foreground uppercase tracking-wider">
                    {m.label}
                  </div>
                  <div className={`text-sm font-bold mt-1 tabular-nums ${(m as any).cor || ""}`}>
                    {m.value}
                  </div>
                </Card>
              ))}
            </div>
          )}

          {/* Gráfico — Série temporal */}
          {barrasMensais.length > 0 && (
            <Card className="p-4">
              <div className="text-[0.625rem] font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                Preço Médio por Mês
              </div>
              <MiniBarChart data={barrasMensais} height={140} />
            </Card>
          )}

          {/* Gráfico — Por cliente */}
          {barrasCliente.length > 0 && (
            <Card className="p-4">
              <div className="text-[0.625rem] font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                Preço Médio por Cliente
              </div>
              <MiniBarChart data={barrasCliente} height={120} />
            </Card>
          )}

          {/* Tabela detalhada */}
          {dados.dados_detalhados.length > 0 && (
            <Card className="p-0 overflow-hidden">
              <div className="text-[0.625rem] font-semibold text-muted-foreground uppercase tracking-wider px-4 py-3 border-b border-border">
                Dados Detalhados
              </div>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="h-7 text-[0.625rem]">Data</TableHead>
                      <TableHead className="h-7 text-[0.625rem]">Orçamento</TableHead>
                      <TableHead className="h-7 text-[0.625rem]">Cliente</TableHead>
                      <TableHead className="h-7 text-[0.625rem]">Obra</TableHead>
                      <TableHead className="h-7 text-[0.625rem] text-right">Preço Unit</TableHead>
                      <TableHead className="h-7 text-[0.625rem] text-right">QTD</TableHead>
                      <TableHead className="h-7 text-[0.625rem] text-right">Valor Total</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {dados.dados_detalhados.map((d, i) => (
                      <TableRow key={i}>
                        <TableCell className="text-[0.6875rem]">
                          {d.data?.slice(0, 10) || "—"}
                        </TableCell>
                        <TableCell className="text-[0.6875rem] font-medium">
                          {d.orcamento_numero}
                        </TableCell>
                        <TableCell className="text-[0.6875rem]">{d.cliente}</TableCell>
                        <TableCell className="text-[0.6875rem] text-muted-foreground">
                          {d.obra || "—"}
                        </TableCell>
                        <TableCell className="text-[0.6875rem] text-right tabular-nums">
                          {fmtBRL(d.preco_unitario)}
                        </TableCell>
                        <TableCell className="text-[0.6875rem] text-right tabular-nums">
                          {fmtNum(d.quantidade)}
                        </TableCell>
                        <TableCell className="text-[0.6875rem] text-right tabular-nums font-medium">
                          {fmtBRL(d.valor_total)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </Card>
          )}
        </>
      )}

      {!dados && !carregando && (
        <Card className="p-12 text-center text-muted-foreground">
          <div className="text-4xl mb-3">📊</div>
          <div className="text-sm font-medium mb-1">Histórico de Preços</div>
          <div className="text-xs">
            Selecione um tipo, um item e o período para visualizar a análise.
          </div>
        </Card>
      )}
    </div>
  )
}
