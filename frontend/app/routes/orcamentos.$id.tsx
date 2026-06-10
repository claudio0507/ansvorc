import { useCallback, useEffect, useState } from "react"
import { Link, useParams } from "react-router"
import { toast } from "sonner"
import {
  ArrowLeftIcon,
  CalculatorIcon,
  CheckIcon,
  DownloadSimpleIcon,
  ArrowsClockwiseIcon,
  TrashIcon,
  WarningIcon,
} from "@phosphor-icons/react"

import { AddItemModal } from "~/components/add-item-modal"
import { StatusBadge } from "~/components/status-badge"
import { Badge } from "~/components/ui/badge"
import { Button } from "~/components/ui/button"
import { Card } from "~/components/ui/card"
import { Input } from "~/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "~/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "~/components/ui/table"
import { auth, fichaApi, orcamentoApi } from "~/lib/api"
import { fmtBRL, fmtNum, fmtPct } from "~/lib/format"

const MOD_FAT_OPTS = ["BDI-MO", "BDI-MAT+MO", "BDI+ICMS", "FAT DIR SIMP"]
const BLOCOS_NAO_FAT = new Set(["operacional", "excepcionais"])

const BLOCO_LABEL: Record<string, { label: string; variant: "default" | "secondary" | "warning" | "destructive" }> = {
  servicos: { label: "Serviço", variant: "default" },
  produtos: { label: "Produto", variant: "secondary" },
  operacional: { label: "Oper.", variant: "warning" },
  excepcionais: { label: "Excep.", variant: "destructive" },
}

function BlocoBadge({ bloco }: { bloco: string }) {
  const cfg = BLOCO_LABEL[bloco] ?? { label: bloco, variant: "secondary" as const }
  return <Badge variant={cfg.variant}>{cfg.label}</Badge>
}

interface Resultado {
  subtotal_faturavel?: number | string
  total_nao_faturavel?: number | string
  total_proposta?: number | string
  margem_liquida_real?: number | string
  fator_k_percentual?: number | string
  itens?: any[]
}

export default function OrcamentoEditor() {
  const { id } = useParams()
  const orcId = Number(id)

  const [orc, setOrc] = useState<any>(null)
  const [itens, setItens] = useState<any[]>([])
  const [fichasServico, setFichasServico] = useState<any[]>([])
  const [fichasProduto, setFichasProduto] = useState<any[]>([])
  const [resultado, setResultado] = useState<Resultado | null>(null)
  const [dirty, setDirty] = useState<Set<number>>(new Set())
  const [erro, setErro] = useState("")
  const [carregando, setCarregando] = useState(true)
  const [addBloco, setAddBloco] = useState<string | null>(null)
  const [calculando, setCalculando] = useState(false)

  const readonly = orc && orc.status !== "rascunho"

  const carregar = useCallback(async () => {
    setCarregando(true)
    setErro("")
    try {
      const [o, its, fs, fp] = await Promise.all([
        orcamentoApi.get(orcId),
        orcamentoApi.listItens(orcId),
        fichaApi.listServicos().catch(() => []),
        fichaApi.listProdutos().catch(() => []),
      ])
      setOrc(o)
      setItens(its)
      setFichasServico(fs)
      setFichasProduto(fp)
      setDirty(new Set())
      setResultado(null)
    } catch (err: any) {
      setErro(err.message)
    } finally {
      setCarregando(false)
    }
  }, [orcId])

  useEffect(() => {
    carregar()
  }, [carregar])

  async function salvarCampo(itemId: number, field: string, raw: string) {
    let val = raw
    if (field === "margem_percentual") val = String(parseFloat(raw) / 100)
    setDirty((d) => new Set(d).add(itemId))
    setResultado(null)
    try {
      const updated = await orcamentoApi.updateItem(orcId, itemId, { [field]: val })
      setItens((arr) => arr.map((i) => (i.id === itemId ? { ...i, ...updated } : i)))
    } catch (err: any) {
      toast.error(`Erro ao salvar: ${err.message}`)
    }
  }

  async function removerItem(itemId: number) {
    try {
      await orcamentoApi.deleteItem(orcId, itemId)
      setItens((arr) => arr.filter((i) => i.id !== itemId))
      toast.success("Item removido")
    } catch (err: any) {
      toast.error(`Erro: ${err.message}`)
    }
  }

  async function calcular() {
    setCalculando(true)
    try {
      const r = await orcamentoApi.calcular(orcId)
      setItens(r.itens ?? itens)
      setOrc((o: any) => ({ ...o, total_proposta: r.total_proposta, margem_liquida_real: r.margem_liquida_real }))
      setResultado(r)
      setDirty(new Set())
      toast.success("Cálculo atualizado com sucesso")
    } catch (err: any) {
      toast.error(`Erro no cálculo: ${err.message}`)
    } finally {
      setCalculando(false)
    }
  }

  async function aprovar() {
    if (!confirm("Aprovar este orçamento? O grid ficará somente leitura e os valores serão congelados.")) return
    try {
      const atualizado = await orcamentoApi.update(orcId, { status: "aprovado" })
      setOrc(atualizado)
      toast.success("Orçamento aprovado e congelado")
    } catch (err: any) {
      toast.error(`Erro: ${err.message}`)
    }
  }

  async function exportarPdf() {
    try {
      const token = auth.getAccessToken()
      const resp = await fetch(`/api/v1/orcamentos/${orcId}/export/pdf`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}))
        throw new Error((err as any).detail ?? `Erro ${resp.status}`)
      }
      const blob = await resp.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `proposta_${orc.numero_proposta}.pdf`
      a.click()
      URL.revokeObjectURL(url)
      toast.success("PDF gerado com sucesso")
    } catch (err: any) {
      toast.error(`Erro ao gerar PDF: ${err.message}`)
    }
  }

  if (carregando) {
    return <div className="text-muted-foreground py-12 text-center">Carregando orçamento…</div>
  }
  if (erro || !orc) {
    return (
      <div className="py-12 text-center">
        <h3 className="text-lg font-semibold">Erro ao carregar orçamento</h3>
        <p className="text-muted-foreground mt-1">{erro}</p>
        <Button asChild variant="secondary" className="mt-4">
          <Link to="/orcamentos">← Voltar</Link>
        </Button>
      </div>
    )
  }

  const calculado = resultado !== null || itens.some((i) => parseFloat(i.preco_venda_unitario) > 0)

  const painel = {
    faturavel: resultado ? fmtBRL(resultado.subtotal_faturavel) : orc.total_proposta ? fmtBRL(orc.total_proposta) : "R$ —",
    diluir: resultado ? fmtBRL(resultado.total_nao_faturavel) : "R$ —",
    fatork: resultado ? `${(parseFloat(String(resultado.fator_k_percentual)) || 0).toFixed(2)}%` : "—",
    mlr: resultado ? fmtPct(resultado.margem_liquida_real) : orc.margem_liquida_real ? fmtPct(orc.margem_liquida_real) : "—",
    total: resultado ? fmtBRL(resultado.total_proposta) : orc.total_proposta ? fmtBRL(orc.total_proposta) : "R$ —",
  }

  return (
    <>
      <div className="mb-5 flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <Button asChild variant="ghost" size="icon">
              <Link to="/orcamentos" aria-label="Voltar"><ArrowLeftIcon className="size-4" /></Link>
            </Button>
            <h2 className="text-xl font-semibold">{orc.numero_proposta}</h2>
            <StatusBadge status={orc.status} />
            {orc.beneficio_reidi && <Badge variant="success">REIDI</Badge>}
            <Badge variant="secondary">{orc.uf_execucao}</Badge>
          </div>
          {orc.descricao_obra && <p className="text-muted-foreground mt-1 text-sm">{orc.descricao_obra}</p>}
        </div>
        <div className="flex flex-wrap gap-2">
          {!readonly ? (
            <>
              <Button size="sm" onClick={calcular} disabled={calculando}>
                <CalculatorIcon className="size-4" /> {calculando ? "Calculando…" : "Calcular"}
              </Button>
              <Button size="sm" variant="secondary" onClick={aprovar}>
                <CheckIcon className="size-4" /> Aprovar
              </Button>
            </>
          ) : (
            <Button size="sm" variant="secondary" onClick={() => toast.info("Nova versão: disponível na Fase 3")}>
              <ArrowsClockwiseIcon className="size-4" /> Nova Versão
            </Button>
          )}
          <Button size="sm" variant="ghost" onClick={exportarPdf}>
            <DownloadSimpleIcon className="size-4" /> Exportar
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 items-start gap-5 lg:grid-cols-[1fr_280px]">
        <div>
          {!readonly && (
            <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
              <span className="text-muted-foreground text-sm">
                {dirty.size > 0 ? `${dirty.size} linha(s) alterada(s) — clique em Calcular` : ""}
              </span>
              <div className="flex flex-wrap gap-2">
                <Button size="sm" variant="secondary" onClick={() => setAddBloco("servicos")}>+ Serviço</Button>
                <Button size="sm" variant="secondary" onClick={() => setAddBloco("produtos")}>+ Produto</Button>
                <Button size="sm" variant="ghost" onClick={() => setAddBloco("operacional")}>+ Operacional</Button>
                <Button size="sm" variant="ghost" className="text-warning" onClick={() => setAddBloco("excepcionais")}>
                  <WarningIcon className="size-4" /> Manual
                </Button>
              </div>
            </div>
          )}

          <Card className="overflow-x-auto py-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-24">Bloco</TableHead>
                  <TableHead>Descrição</TableHead>
                  <TableHead className="w-12">Und</TableHead>
                  <TableHead className="w-20 text-right">QTD</TableHead>
                  <TableHead className="w-28">MOD FAT</TableHead>
                  <TableHead className="w-20 text-right">Margem</TableHead>
                  <TableHead className="w-24 text-right">Custo Unit</TableHead>
                  <TableHead className="w-28 text-right">Preço Unit</TableHead>
                  <TableHead className="w-28 text-right">Preço Total</TableHead>
                  {!readonly && <TableHead className="w-10"></TableHead>}
                </TableRow>
              </TableHeader>
              <TableBody>
                {itens.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={readonly ? 9 : 10} className="text-muted-foreground py-8 text-center">
                      Nenhum item adicionado.{readonly ? "" : " Use os botões acima para inserir serviços, produtos ou custos operacionais."}
                    </TableCell>
                  </TableRow>
                ) : (
                  itens.map((item) => {
                    const naoFat = BLOCOS_NAO_FAT.has(item.bloco)
                    const hasPrices = parseFloat(item.preco_venda_unitario) > 0
                    const isDirty = dirty.has(item.id)
                    return (
                      <TableRow key={item.id} className={isDirty ? "bg-warning/10" : ""}>
                        <TableCell>
                          <BlocoBadge bloco={item.bloco} />
                          {item.demanda_aprovacao && (
                            <div className="mt-1"><Badge variant="warning">Aprovação</Badge></div>
                          )}
                        </TableCell>
                        <TableCell className="max-w-44">
                          <div className="truncate text-sm font-medium" title={item.descricao}>{item.descricao}</div>
                          <div className="text-muted-foreground text-xs">{item.unidade_medida}</div>
                        </TableCell>
                        <TableCell className="text-muted-foreground text-xs">{item.unidade_medida}</TableCell>
                        <TableCell className="text-right">
                          {readonly ? (
                            <span className="text-sm">{fmtNum(item.quantidade)}</span>
                          ) : (
                            <Input
                              type="number"
                              defaultValue={item.quantidade}
                              min="0.0001"
                              step="0.01"
                              className="h-8 w-20 text-right"
                              onBlur={(e) => e.target.value !== String(item.quantidade) && salvarCampo(item.id, "quantidade", e.target.value)}
                            />
                          )}
                        </TableCell>
                        <TableCell>
                          {readonly || naoFat ? (
                            <span className="text-muted-foreground text-xs">{item.mod_fat}</span>
                          ) : (
                            <Select defaultValue={item.mod_fat} onValueChange={(v) => salvarCampo(item.id, "mod_fat", v)}>
                              <SelectTrigger className="h-8 w-28"><SelectValue /></SelectTrigger>
                              <SelectContent>
                                {MOD_FAT_OPTS.map((m) => <SelectItem key={m} value={m}>{m}</SelectItem>)}
                              </SelectContent>
                            </Select>
                          )}
                        </TableCell>
                        <TableCell className="text-right">
                          {readonly || naoFat ? (
                            <span className="text-muted-foreground text-sm">{naoFat ? "Sombra" : fmtPct(item.margem_percentual)}</span>
                          ) : (
                            <div className="flex items-center justify-end gap-1">
                              <Input
                                type="number"
                                defaultValue={(parseFloat(item.margem_percentual) * 100).toFixed(1)}
                                min="0"
                                max="99.9"
                                step="0.1"
                                className="h-8 w-16 text-right"
                                onBlur={(e) => salvarCampo(item.id, "margem_percentual", e.target.value)}
                              />
                              <span className="text-xs">%</span>
                            </div>
                          )}
                        </TableCell>
                        <TableCell className="text-right text-sm">{fmtBRL(item.custo_direto_unitario)}</TableCell>
                        <TableCell className="text-right">
                          {hasPrices ? (
                            <>
                              <span className="text-sm font-medium">{fmtBRL(item.preco_final_unitario || item.preco_venda_unitario)}</span>
                              {item.rateio_absorvido > 0 && (
                                <div className="text-success text-xs">+{fmtBRL(item.rateio_absorvido)} K</div>
                              )}
                            </>
                          ) : (
                            <span className="text-muted-foreground text-xs">—</span>
                          )}
                        </TableCell>
                        <TableCell className="text-right">
                          {hasPrices ? (
                            <span className="text-primary text-sm font-semibold">{fmtBRL(item.preco_venda_total)}</span>
                          ) : (
                            <span className="text-muted-foreground text-xs">—</span>
                          )}
                        </TableCell>
                        {!readonly && (
                          <TableCell>
                            <Button variant="ghost" size="icon" title="Remover item" onClick={() => removerItem(item.id)}>
                              <TrashIcon className="text-destructive size-4" />
                            </Button>
                          </TableCell>
                        )}
                      </TableRow>
                    )
                  })
                )}
              </TableBody>
            </Table>
          </Card>
        </div>

        <Card className="p-4">
          <dl className="space-y-3 text-sm">
            <div>
              <dt className="text-muted-foreground">Subtotal Faturável</dt>
              <dd className="text-lg font-semibold">{painel.faturavel}</dd>
            </div>
            <div className="border-t pt-3">
              <dt className="text-destructive">Total a Diluir</dt>
              <dd className="text-destructive text-lg font-semibold">{painel.diluir}</dd>
            </div>
            <div className="border-t pt-3">
              <dt className="text-muted-foreground">Fator K</dt>
              <dd className="text-lg font-semibold">{painel.fatork}</dd>
            </div>
            <div className="border-t pt-3">
              <dt className="text-muted-foreground">Margem Líquida Real</dt>
              <dd className="text-success text-lg font-semibold">{painel.mlr}</dd>
            </div>
            <div className="border-t pt-3">
              <dt className="text-xs font-bold tracking-wide uppercase">Total da Proposta</dt>
              <dd className="text-primary text-2xl font-bold">{painel.total}</dd>
            </div>
          </dl>
          {!calculado && (
            <p className="text-warning bg-warning/10 mt-3 p-2.5 text-center text-xs">
              Clique em "Calcular" para obter os preços finais.
            </p>
          )}
        </Card>
      </div>

      <AddItemModal
        bloco={addBloco}
        orcId={orcId}
        fichasServico={fichasServico}
        fichasProduto={fichasProduto}
        onOpenChange={(v) => !v && setAddBloco(null)}
        onAdded={(novo) => {
          setItens((arr) => [...arr, novo])
          setResultado(null)
          setAddBloco(null)
        }}
      />
    </>
  )
}
