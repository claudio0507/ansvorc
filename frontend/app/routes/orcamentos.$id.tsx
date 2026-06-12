import { useCallback, useEffect, useState } from "react"
import { Link, useNavigate, useParams } from "react-router"
import { toast } from "sonner"
import {
  ArrowLeftIcon,
  CalculatorIcon,
  ArrowsClockwiseIcon,
  TrashIcon,
  PlusIcon,
  FileTextIcon,
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
import { orcamentoApi } from "~/lib/api"
import { fmtBRL, fmtNum, fmtPct } from "~/lib/format"

// Blocos do orçamento (visual do design-system-preview): Serviços = acento vermelho
// (bloco principal); Produtos/Operacional = neutro; Excepcionais = vermelho suave.
// Cada barra tem um "pill" de 3px à esquerda.
const BLOCOS: {
  key: string
  titulo: string
  faturavel: boolean
  bar: string
  pill: string
}[] = [
  {
    key: "servicos",
    titulo: "1. SERVIÇOS",
    faturavel: true,
    bar: "bg-secondary text-secondary-foreground",
    pill: "bg-muted-foreground/60",
  },
  {
    key: "produtos",
    titulo: "2. PRODUTOS",
    faturavel: true,
    bar: "bg-secondary text-secondary-foreground",
    pill: "bg-muted-foreground/60",
  },
  {
    key: "operacional",
    titulo: "3. ESTRUTURA OPERACIONAL",
    faturavel: false,
    bar: "bg-secondary text-secondary-foreground",
    pill: "bg-muted-foreground/50",
  },
  {
    key: "excepcionais",
    titulo: "4. CUSTOS EXCEPCIONAIS",
    faturavel: false,
    bar: "bg-secondary text-secondary-foreground",
    pill: "bg-muted-foreground/50",
  },
]
const MOD_FAT_OPTS = ["BDI-MAT+MO", "BDI-MO", "BDI+ICMS", "FAT DIR SIMP"]

// Máquina de transição de status (6 estados).
const TRANSICOES: Record<string, string[]> = {
  rascunho: ["enviado"],
  enviado: ["aprovado", "reprovado", "perdida"],
  aprovado: ["fechado", "perdida"],
  reprovado: ["rascunho"],
  perdida: [],
  fechado: [],
}
const STATUS_LABEL: Record<string, string> = {
  rascunho: "Rascunho",
  enviado: "Enviado",
  aprovado: "Aprovado",
  reprovado: "Reprovado",
  perdida: "Perdida",
  fechado: "Fechado",
}

export default function OrcamentoEditor() {
  const { id } = useParams()
  const orcId = Number(id)
  const navigate = useNavigate()

  const [orc, setOrc] = useState<any>(null)
  const [itens, setItens] = useState<any[]>([])
  const [resultado, setResultado] = useState<any>(null)
  const [erro, setErro] = useState("")
  const [carregando, setCarregando] = useState(true)
  const [addBloco, setAddBloco] = useState<string | null>(null)
  const [calculando, setCalculando] = useState(false)
  const [desconto, setDesconto] = useState("0")
  const [historico, setHistorico] = useState<any[]>([])

  const readonly = orc && !["rascunho", "reprovado"].includes(orc.status)

  const carregar = useCallback(async () => {
    setCarregando(true)
    setErro("")
    try {
      const [o, its, hist] = await Promise.all([
        orcamentoApi.get(orcId),
        orcamentoApi.listItens(orcId),
        orcamentoApi.historicoDescontos(orcId).catch(() => []),
      ])
      setOrc(o)
      setItens(its)
      setDesconto(String(o.desconto_percentual ?? "0"))
      setHistorico(hist)
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

  async function salvarCampo(itemId: number, campo: string, valor: string, atual: any) {
    if (valor === String(atual)) return
    setResultado(null)
    try {
      const updated = await orcamentoApi.updateItem(orcId, itemId, { [campo]: valor })
      setItens((arr) => arr.map((i) => (i.id === itemId ? { ...i, ...updated } : i)))
    } catch (err: any) {
      toast.error(`Erro ao salvar: ${err.message}`)
    }
  }

  const salvarQuantidade = (id: number, v: string, atual: string) =>
    salvarCampo(id, "quantidade", v, atual)

  async function removerItem(itemId: number) {
    try {
      await orcamentoApi.deleteItem(orcId, itemId)
      setItens((arr) => arr.filter((i) => i.id !== itemId))
      toast.success("Item removido")
    } catch (err: any) {
      toast.error(`Erro: ${err.message}`)
    }
  }

  async function salvarDesconto() {
    try {
      await orcamentoApi.update(orcId, { desconto_percentual: desconto })
      setOrc((o: any) => ({ ...o, desconto_percentual: desconto }))
      toast.success("Desconto atualizado — recalcule para aplicar")
      setResultado(null)
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
      toast.success("Cálculo atualizado com sucesso")
    } catch (err: any) {
      toast.error(`Erro no cálculo: ${err.message}`)
    } finally {
      setCalculando(false)
    }
  }

  async function mudarStatus(novo: string) {
    try {
      const atualizado = await orcamentoApi.update(orcId, { status: novo })
      setOrc(atualizado)
      toast.success(`Status: ${STATUS_LABEL[novo] ?? novo}`)
    } catch (e: any) {
      toast.error(`Erro: ${e.message}`)
    }
  }

  async function novaVersao() {
    try {
      const nova = await orcamentoApi.reabrir(orcId)
      toast.success(`Nova versão (v${nova.versao}) criada`)
      navigate(`/orcamentos/${nova.id}`)
    } catch (err: any) {
      toast.error(`Erro: ${err.message}`)
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

  // Totais: usa resultado do último cálculo ou valores persistidos no orc (item 9)
  const subtotalFat = resultado ? fmtBRL(resultado.subtotal_faturavel) : orc.total_custo_direto ? fmtBRL(orc.total_custo_direto) : "—"
  const totalDiluir = resultado ? fmtBRL(resultado.total_nao_faturavel) : "—"
  const fatorK = resultado ? `${(parseFloat(String(resultado.fator_k_percentual)) || 0).toFixed(2)}%` : "—"
  const mlr = resultado ? fmtPct(resultado.margem_liquida_real) : orc.margem_liquida_real ? fmtPct(orc.margem_liquida_real) : "—"
  const total = resultado ? fmtBRL(resultado.total_proposta) : orc.total_proposta ? fmtBRL(orc.total_proposta) : "R$ —"

  return (
    <>
      <div className="mb-5 flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <Button asChild variant="ghost" size="icon">
              <Link to="/orcamentos" aria-label="Voltar"><ArrowLeftIcon className="size-4" /></Link>
            </Button>
            <h2 className="text-xl font-semibold">{orc.numero}</h2>
            <StatusBadge status={orc.status} />
            {orc.versao > 1 && <Badge variant="secondary">V{orc.versao}</Badge>}
            {orc.beneficio_reidi && <Badge variant="success">REIDI</Badge>}
            <Badge variant="secondary">{orc.uf_execucao}</Badge>
          </div>
          {orc.obra && <p className="text-muted-foreground mt-1 text-sm">{orc.obra}</p>}
        </div>
        <div className="flex flex-wrap gap-2">
          <Button asChild size="sm" variant="ghost">
            <Link to={`/orcamentos/${orcId}/proposta`}>
              <FileTextIcon className="size-4" /> Proposta
            </Link>
          </Button>
          {!readonly && (
            <Button size="sm" onClick={calcular} disabled={calculando}>
              <CalculatorIcon className="size-4" /> {calculando ? "Calculando…" : "Calcular"}
            </Button>
          )}
          {readonly && (
            <Button size="sm" variant="secondary" onClick={novaVersao}>
              <ArrowsClockwiseIcon className="size-4" /> Nova Versão
            </Button>
          )}
          {TRANSICOES[orc.status]?.length > 0 && (
            <Select value="" onValueChange={mudarStatus}>
              <SelectTrigger className="h-8 w-auto gap-2">
                <SelectValue placeholder="Mudar status…" />
              </SelectTrigger>
              <SelectContent>
                {TRANSICOES[orc.status].map((s) => (
                  <SelectItem key={s} value={s}>{STATUS_LABEL[s]}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 items-start gap-5 lg:grid-cols-[1fr_280px]">
        <div className="space-y-4">
          {BLOCOS.map((b) => {
            const linhas = itens.filter((i) => i.bloco === b.key)
            return (
              <Card key={b.key} className="overflow-hidden py-0">
                <div className={`flex items-center justify-between px-3 py-1.5 text-[0.625rem] font-bold tracking-wide uppercase ${b.bar}`}>
                  <span className="flex items-center gap-2">
                    <span className={`inline-block h-3 w-[3px] rounded-sm ${b.pill}`} />
                    {b.titulo}
                  </span>
                  {!readonly && (
                    <Button size="sm" variant="ghost" className="h-5 px-2 text-[0.625rem]" onClick={() => setAddBloco(b.key)}>
                      <PlusIcon className="size-3" /> Adicionar
                    </Button>
                  )}
                </div>
                <div className="overflow-x-auto">
                  <Table className="text-[0.6875rem]">
                    <TableHeader>
                      <TableRow>
                        <TableHead className="h-7 text-[0.625rem]">Descrição</TableHead>
                        <TableHead className="h-7 w-12 text-[0.625rem]">Und</TableHead>
                        <TableHead className="h-7 w-24 text-right text-[0.625rem]">QTD</TableHead>
                        {b.faturavel && <TableHead className="h-7 w-16 text-right text-[0.625rem]">Margem</TableHead>}
                        {b.faturavel && <TableHead className="h-7 w-28 text-[0.625rem]">MOD FAT</TableHead>}
                        <TableHead className="h-7 w-24 text-right text-[0.625rem]">Custo Unit</TableHead>
                        <TableHead className="h-7 w-24 text-right text-[0.625rem]">Preço Unit</TableHead>
                        <TableHead className="h-7 w-24 text-right text-[0.625rem]">Preço Total</TableHead>
                        <TableHead className="h-7 w-24 text-right text-[0.625rem]">Desc. Rateado</TableHead>
                        {!readonly && <TableHead className="h-7 w-8"></TableHead>}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {linhas.length === 0 ? (
                        <TableRow>
                          <TableCell colSpan={10} className="text-muted-foreground py-3 text-center">
                            Nenhum item neste bloco.
                          </TableCell>
                        </TableRow>
                      ) : (
                        linhas.map((it) => {
                          const hasPrices = parseFloat(it.preco_venda_total) > 0
                          return (
                            <TableRow key={it.id}>
                              <TableCell className="max-w-48 px-2 py-0.5">
                                <div className="truncate font-medium" title={it.descricao}>{it.descricao}</div>
                                {it.flag_aprovacao && <Badge variant="warning" className="mt-0.5">APROVAÇÃO</Badge>}
                              </TableCell>
                              {/* Unidade READONLY (definida no cadastro) */}
                              <TableCell className="text-muted-foreground px-2 py-0.5">{it.unidade}</TableCell>
                              <TableCell className="px-2 py-0.5 text-right">
                                {readonly ? (
                                  <span className="tabular-nums">
                                    {Number(it.quantidade).toLocaleString("pt-BR", {
                                      minimumFractionDigits: 0,
                                      maximumFractionDigits: 2,
                                    })}
                                  </span>
                                ) : (
                                  <Input
                                    type="number"
                                    defaultValue={Number(it.quantidade).toLocaleString("pt-BR", { minimumFractionDigits: 0, maximumFractionDigits: 2 })}
                                    min="0"
                                    step="any"
                                    className="h-7 w-24 text-right text-[0.6875rem] tabular-nums"
                                    onBlur={(e) => salvarQuantidade(it.id, e.target.value, it.quantidade)}
                                    onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); (e.target as HTMLInputElement).blur(); calcular() } }}
                                  />
                                )}
                              </TableCell>
                              {b.faturavel && (
                                <TableCell className="px-2 py-0.5 text-right">
                                  {readonly ? (
                                    <span>{Number(it.margem_lucro).toFixed(1)}%</span>
                                  ) : (
                                    <div className="flex items-center justify-end gap-0.5">
                                      <Input
                                        type="number"
                                        defaultValue={Number(it.margem_lucro).toFixed(1)}
                                        min="0"
                                        max="99.9"
                                        step="0.1"
                                        className="h-7 w-14 text-right text-[0.6875rem] tabular-nums"
                                        onBlur={(e) => salvarCampo(it.id, "margem_lucro", e.target.value, Number(it.margem_lucro))}
                                        onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); (e.target as HTMLInputElement).blur(); calcular() } }}
                                      />
                                      <span className="text-muted-foreground">%</span>
                                    </div>
                                  )}
                                </TableCell>
                              )}
                              {b.faturavel && (
                                <TableCell className="px-2 py-0.5">
                                  {readonly ? (
                                    <span className="text-muted-foreground">{it.mod_fat}</span>
                                  ) : (
                                    <Select
                                      defaultValue={it.mod_fat}
                                      onValueChange={(v) => salvarCampo(it.id, "mod_fat", v, it.mod_fat)}
                                    >
                                      <SelectTrigger className="h-7 w-28 text-[0.6875rem]"><SelectValue /></SelectTrigger>
                                      <SelectContent>
                                        {MOD_FAT_OPTS.map((m) => <SelectItem key={m} value={m}>{m}</SelectItem>)}
                                      </SelectContent>
                                    </Select>
                                  )}
                                </TableCell>
                              )}
                              <TableCell className="px-2 py-0.5 text-right">{fmtBRL(it.custo_direto_unitario)}</TableCell>
                              <TableCell className="px-2 py-0.5 text-right">
                                {hasPrices ? (
                                  <span className="font-medium">{fmtBRL(it.preco_venda_unitario_final || it.preco_venda_unitario)}</span>
                                ) : (
                                  <span className="text-muted-foreground">—</span>
                                )}
                              </TableCell>
                              <TableCell className="px-2 py-0.5 text-right">
                                {hasPrices ? (
                                  <span className="text-primary font-semibold">{fmtBRL(it.preco_venda_total)}</span>
                                ) : (
                                  <span className="text-muted-foreground">—</span>
                                )}
                              </TableCell>
                              <TableCell className="text-muted-foreground px-2 py-0.5 text-right">
                                {parseFloat(it.desconto_rateado) > 0 ? `- ${fmtBRL(it.desconto_rateado)}` : "—"}
                              </TableCell>
                              {!readonly && (
                                <TableCell className="px-2 py-0.5">
                                  <Button variant="ghost" size="icon" className="size-6" title="Remover" onClick={() => removerItem(it.id)}>
                                    <TrashIcon className="text-destructive size-3.5" />
                                  </Button>
                                </TableCell>
                              )}
                            </TableRow>
                          )
                        })
                      )}
                    </TableBody>
                  </Table>
                </div>
              </Card>
            )
          })}
        </div>

        {/* Painel financeiro — só MLR e Total coloridos; resto neutro. */}
        <Card className="p-4">
          {!readonly && (
            <div className="mb-4 flex flex-col gap-2 border-b pb-4">
              <label className="text-muted-foreground text-xs font-medium uppercase">Desconto (%)</label>
              <div className="flex gap-2">
                <Input
                  type="number"
                  min="0"
                  max="100"
                  step="0.01"
                  value={desconto}
                  onChange={(e) => setDesconto(e.target.value)}
                  onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); salvarDesconto().then(calcular) } }}
                  className="h-8"
                />
                <Button size="sm" variant="secondary" onClick={salvarDesconto}>OK</Button>
              </div>
            </div>
          )}
          <dl className="space-y-3 text-sm">
            <div>
              <dt className="text-muted-foreground">Subtotal Faturável</dt>
              <dd className="text-foreground text-lg font-semibold">{subtotalFat}</dd>
            </div>
            <div className="border-t pt-3">
              <dt className="text-muted-foreground">Total a Diluir</dt>
              <dd className="text-foreground text-lg font-semibold">{totalDiluir}</dd>
            </div>
            <div className="border-t pt-3">
              <dt className="text-muted-foreground">Fator K</dt>
              <dd className="text-foreground text-lg font-semibold">{fatorK}</dd>
            </div>
            <div className="border-t pt-3">
              <dt className="text-muted-foreground">Margem Líquida Real</dt>
              <dd className="text-success text-lg font-bold">{mlr}</dd>
            </div>
            <div className="border-t pt-3">
              <dt className="text-xs font-bold tracking-wide uppercase">Total da Proposta</dt>
              <dd className="text-primary text-2xl font-bold">{total}</dd>
            </div>
          </dl>
          {!resultado && !orc.total_proposta && (
            <p className="text-warning bg-warning/10 mt-3 p-2.5 text-center text-xs">
              Clique em "Calcular" para obter os preços finais.
            </p>
          )}
        </Card>

        {/* BLOCO 1.4 — observações internas (gerenciamento, não vai p/ proposta) */}
        {orc.observacoes_internas && (
          <Card className="p-4">
            <div className="text-muted-foreground mb-1 text-xs font-medium uppercase">
              📝 Observações Internas
            </div>
            <p className="text-sm whitespace-pre-wrap">{orc.observacoes_internas}</p>
          </Card>
        )}

        {/* BLOCO 1.3 — histórico de descontos das versões */}
        {historico.length > 0 && (
          <Card className="p-4">
            <div className="text-muted-foreground mb-2 text-xs font-medium uppercase">
              Histórico de Descontos
            </div>
            <div className="space-y-1.5">
              {historico.map((h, i) => (
                <div key={i} className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">Versão {h.versao}</span>
                  <span>{Number(h.desconto_percentual).toFixed(2)}%</span>
                  <span className="text-muted-foreground">{fmtBRL(h.desconto_total)}</span>
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>

      <AddItemModal
        bloco={addBloco}
        orcId={orcId}
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
