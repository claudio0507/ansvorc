import { useCallback, useEffect, useState } from "react"
import { Link, useNavigate, useParams } from "react-router"
import { toast } from "sonner"
import {
  ArrowLeftIcon,
  CalculatorIcon,
  CheckIcon,
  ArrowsClockwiseIcon,
  TrashIcon,
  PlusIcon,
} from "@phosphor-icons/react"

import { AddItemModal } from "~/components/add-item-modal"
import { StatusBadge } from "~/components/status-badge"
import { Badge } from "~/components/ui/badge"
import { Button } from "~/components/ui/button"
import { Card } from "~/components/ui/card"
import { Input } from "~/components/ui/input"
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

// Blocos agrupados (docs/05): cada um vira uma tabela com cabeçalho colorido.
const BLOCOS: { key: string; titulo: string; cor: string; faturavel: boolean }[] = [
  { key: "servicos", titulo: "1. SERVIÇOS", cor: "bg-primary/10 text-primary", faturavel: true },
  { key: "produtos", titulo: "2. PRODUTOS", cor: "bg-secondary text-secondary-foreground", faturavel: true },
  { key: "operacional", titulo: "3. ESTRUTURA OPERACIONAL", cor: "bg-warning/15 text-warning", faturavel: false },
  { key: "excepcionais", titulo: "4. CUSTOS EXCEPCIONAIS", cor: "bg-destructive/10 text-destructive", faturavel: false },
]

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

  const readonly = orc && orc.status !== "rascunho"

  const carregar = useCallback(async () => {
    setCarregando(true)
    setErro("")
    try {
      const [o, its] = await Promise.all([
        orcamentoApi.get(orcId),
        orcamentoApi.listItens(orcId),
      ])
      setOrc(o)
      setItens(its)
      setDesconto(String(o.desconto_percentual ?? "0"))
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

  async function salvarQuantidade(itemId: number, raw: string, atual: string) {
    if (raw === String(atual)) return
    setResultado(null)
    try {
      const updated = await orcamentoApi.updateItem(orcId, itemId, { quantidade: raw })
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

  async function aprovar() {
    if (!confirm("Aprovar este orçamento? Os valores serão congelados (somente leitura).")) return
    try {
      await orcamentoApi.update(orcId, { status: "enviado" })
      const atualizado = await orcamentoApi.update(orcId, { status: "aprovado" })
      setOrc(atualizado)
      toast.success("Orçamento aprovado e congelado")
    } catch (err: any) {
      toast.error(`Erro: ${err.message}`)
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

  const calculado = resultado !== null || itens.some((i) => parseFloat(i.preco_venda_unitario) > 0)

  // Painel: apenas MLR (verde) e Total (primária) coloridos.
  const subtotalFat = resultado ? fmtBRL(resultado.subtotal_faturavel) : "—"
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
            <Button size="sm" variant="secondary" onClick={novaVersao}>
              <ArrowsClockwiseIcon className="size-4" /> Nova Versão
            </Button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 items-start gap-5 lg:grid-cols-[1fr_280px]">
        <div className="space-y-4">
          {BLOCOS.map((b) => {
            const linhas = itens.filter((i) => i.bloco === b.key)
            return (
              <Card key={b.key} className="overflow-hidden py-0">
                <div className={`flex items-center justify-between px-4 py-2 text-xs font-bold tracking-wide ${b.cor}`}>
                  <span>{b.titulo}</span>
                  {!readonly && (
                    <Button size="sm" variant="ghost" className="h-6 px-2" onClick={() => setAddBloco(b.key)}>
                      <PlusIcon className="size-3.5" /> Adicionar
                    </Button>
                  )}
                </div>
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Descrição</TableHead>
                        <TableHead className="w-12">Und</TableHead>
                        <TableHead className="w-24 text-right">QTD</TableHead>
                        {b.faturavel && <TableHead className="w-20 text-right">Margem</TableHead>}
                        {b.faturavel && <TableHead className="w-24">MOD FAT</TableHead>}
                        <TableHead className="w-28 text-right">Custo Unit</TableHead>
                        <TableHead className="w-28 text-right">Preço Total</TableHead>
                        {!readonly && <TableHead className="w-10"></TableHead>}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {linhas.length === 0 ? (
                        <TableRow>
                          <TableCell colSpan={9} className="text-muted-foreground py-4 text-center text-sm">
                            Nenhum item neste bloco.
                          </TableCell>
                        </TableRow>
                      ) : (
                        linhas.map((it) => {
                          const hasPrices = parseFloat(it.preco_venda_total) > 0
                          return (
                            <TableRow key={it.id}>
                              <TableCell className="max-w-48">
                                <div className="truncate text-sm font-medium" title={it.descricao}>{it.descricao}</div>
                                {it.flag_aprovacao && <Badge variant="warning" className="mt-1">APROVAÇÃO</Badge>}
                              </TableCell>
                              {/* Unidade READONLY (definida no cadastro) */}
                              <TableCell className="text-muted-foreground text-xs">{it.unidade}</TableCell>
                              <TableCell className="text-right">
                                {readonly ? (
                                  <span className="text-sm">{fmtNum(it.quantidade)}</span>
                                ) : (
                                  <Input
                                    type="number"
                                    defaultValue={it.quantidade}
                                    min="0.0001"
                                    step="0.01"
                                    className="h-8 w-20 text-right"
                                    onBlur={(e) => salvarQuantidade(it.id, e.target.value, it.quantidade)}
                                  />
                                )}
                              </TableCell>
                              {b.faturavel && (
                                <TableCell className="text-muted-foreground text-right text-sm">
                                  {Number(it.margem_lucro).toFixed(1)}%
                                </TableCell>
                              )}
                              {b.faturavel && (
                                <TableCell className="text-muted-foreground text-xs">{it.mod_fat}</TableCell>
                              )}
                              <TableCell className="text-right text-sm">{fmtBRL(it.custo_direto_unitario)}</TableCell>
                              <TableCell className="text-right">
                                {hasPrices ? (
                                  <span className="text-primary text-sm font-semibold">{fmtBRL(it.preco_venda_total)}</span>
                                ) : (
                                  <span className="text-muted-foreground text-xs">—</span>
                                )}
                              </TableCell>
                              {!readonly && (
                                <TableCell>
                                  <Button variant="ghost" size="icon" title="Remover" onClick={() => removerItem(it.id)}>
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
