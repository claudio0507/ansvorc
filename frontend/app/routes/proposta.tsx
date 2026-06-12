import { useEffect, useState } from "react"
import { Link, useParams } from "react-router"
import { toast } from "sonner"
import { ArrowLeftIcon, DownloadSimpleIcon } from "@phosphor-icons/react"

import { Button } from "~/components/ui/button"
import { Card } from "~/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "~/components/ui/table"
import { QRCodeSVG } from "qrcode.react"

import { auth, clienteApi, configApi, orcamentistaApi, orcamentoApi } from "~/lib/api"
import { fmtBRL, fmtData } from "~/lib/format"

const BLOCOS_PROPOSTA = [
  { key: "servicos", titulo: "Serviços" },
  { key: "produtos", titulo: "Produtos" },
]

export default function Proposta() {
  const { id } = useParams()
  const orcId = Number(id)
  const [orc, setOrc] = useState<any>(null)
  const [itens, setItens] = useState<any[]>([])
  const [cliente, setCliente] = useState<any>(null)
  const [orcamentista, setOrcamentista] = useState<any>(null)
  const [config, setConfig] = useState<any>(null)
  const [erro, setErro] = useState("")

  useEffect(() => {
    async function load() {
      try {
        const [o, its, cfg] = await Promise.all([
          orcamentoApi.get(orcId),
          orcamentoApi.listItens(orcId),
          configApi.get().catch(() => null),
        ])
        setOrc(o)
        setItens(its)
        setConfig(cfg)
        if (o.cliente_id) clienteApi.get(o.cliente_id).then(setCliente).catch(() => {})
        if (o.orcamentista_id) {
          orcamentistaApi
            .list()
            .then((l) => setOrcamentista(l.find((x) => x.id === o.orcamentista_id)))
            .catch(() => {})
        }
      } catch (e: any) {
        setErro(e.message)
      }
    }
    load()
  }, [orcId])

  async function exportarPdf() {
    try {
      const token = auth.getAccessToken()
      const resp = await fetch(`/api/v1/orcamentos/${orcId}/export/pdf`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
      if (!resp.ok) throw new Error(`Erro ${resp.status}`)
      const blob = await resp.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `proposta_${orc.numero}.pdf`
      a.click()
      URL.revokeObjectURL(url)
    } catch (e: any) {
      toast.error(`Erro ao gerar PDF: ${e.message}`)
    }
  }

  if (erro) return <div className="text-destructive py-12 text-center">{erro}</div>
  if (!orc) return <div className="text-muted-foreground py-12 text-center">Carregando…</div>

  // Só blocos faturáveis vão para a proposta; usa descrição do cliente quando houver.
  const linhas = (bloco: string) => itens.filter((i) => i.bloco === bloco)
  const subtotal = itens
    .filter((i) => ["servicos", "produtos"].includes(i.bloco))
    .reduce((s, i) => s + (parseFloat(i.preco_venda_total) || 0), 0)
  const descontoTotal = itens
    .filter((i) => ["servicos", "produtos"].includes(i.bloco))
    .reduce((s, i) => s + (parseFloat(i.desconto_rateado) || 0), 0)
  const totalLiquido = subtotal - descontoTotal
  const hoje = new Date().toLocaleDateString("pt-BR")

  const editavel = orc ? ["rascunho", "reprovado"].includes(orc.status) : false

  const waLink = (tel?: string) => {
    const dig = (tel ?? "").replace(/\D/g, "")
    if (!dig) return null
    return `https://wa.me/${dig.startsWith("55") ? dig : "55" + dig}`
  }
  const waOrc = waLink(orcamentista?.telefone)

  async function salvarDescricaoItem(itemId: number, valor: string) {
    try {
      await orcamentoApi.updateItem(orcId, itemId, { descricao_cliente: valor })
      setItens((arr) => arr.map((i) => (i.id === itemId ? { ...i, descricao_cliente: valor } : i)))
    } catch (e: any) {
      toast.error(`Erro: ${e.message}`)
    }
  }

  async function salvarTextoOrc(campo: string, valor: string) {
    try {
      await orcamentoApi.update(orcId, { [campo]: valor })
      setOrc((o: any) => ({ ...o, [campo]: valor }))
    } catch (e: any) {
      toast.error(`Erro: ${e.message}`)
    }
  }

  return (
    <>
      <div className="mb-4 flex items-center justify-between">
        <Button asChild variant="ghost" size="sm">
          <Link to={`/orcamentos/${orcId}`}>
            <ArrowLeftIcon className="size-4" /> Voltar ao orçamento
          </Link>
        </Button>
        <Button size="sm" onClick={exportarPdf}>
          <DownloadSimpleIcon className="size-4" /> Exportar PDF
        </Button>
      </div>

      <Card className="mx-auto max-w-4xl p-8">
        {/* Cabeçalho */}
        <div className="grid grid-cols-3 items-center border-b pb-5">
          <div className="flex items-center">
            {config?.logo_path ? (
              <img src={config.logo_path} alt="logo" className="h-12 max-w-[160px] object-contain" />
            ) : (
              <div className="bg-primary text-primary-foreground flex size-12 items-center justify-center rounded">
                <svg viewBox="0 0 24 24" className="size-6 fill-current"><path d="M12 2L2 7l10 5 10-5-10-5zm0 10L2 7v10l10 5 10-5V7l-10 5z" /></svg>
              </div>
            )}
          </div>
          <div className="text-center text-lg font-bold tracking-wide uppercase">Proposta Comercial</div>
          <div className="text-right text-xs">
            {orc.obra && <div className="font-semibold">{orc.obra}</div>}
            <div className="text-muted-foreground">Proposta {orc.numero} · v{orc.versao ?? 1}</div>
            <div className="text-muted-foreground">Emissão: {hoje}</div>
          </div>
        </div>

        {/* Dados cliente + orçamentista */}
        <div className="grid grid-cols-1 gap-4 border-b py-5 text-sm sm:grid-cols-2">
          <div>
            <div className="text-muted-foreground mb-1 text-[0.625rem] font-medium uppercase">Cliente</div>
            <div className="font-medium">{cliente?.nome ?? `#${orc.cliente_id}`}</div>
            {cliente?.cnpj_cpf && <div className="text-muted-foreground text-xs">{cliente.cnpj_cpf}</div>}
            {cliente?.contato_nome && <div className="text-muted-foreground text-xs">{cliente.contato_nome}</div>}
            {orc.obra && <div className="text-muted-foreground mt-1 text-xs">Obra: {orc.obra}</div>}
          </div>
          <div className="sm:text-right">
            <div className="text-muted-foreground mb-1 text-[0.625rem] font-medium uppercase">Responsável</div>
            <div className="font-medium">{orcamentista?.nome_completo ?? "—"}</div>
            {orcamentista?.funcao && <div className="text-muted-foreground text-xs">{orcamentista.funcao}</div>}
            {orcamentista?.telefone && <div className="text-muted-foreground text-xs">{orcamentista.telefone}</div>}
            {orcamentista?.email && <div className="text-muted-foreground text-xs">{orcamentista.email}</div>}
          </div>
        </div>

        {(orc.texto_topo_proposta || editavel) && (
          <div className="border-b py-3">
            {editavel ? (
              <textarea
                defaultValue={orc.texto_topo_proposta ?? ""}
                placeholder="Texto de apresentação (aparece antes dos itens)…"
                onBlur={(e) => salvarTextoOrc("texto_topo_proposta", e.target.value)}
                className="text-muted-foreground w-full resize-none rounded border bg-transparent p-2 text-xs"
                rows={2}
              />
            ) : (
              <p className="text-muted-foreground text-xs whitespace-pre-wrap">{orc.texto_topo_proposta}</p>
            )}
          </div>
        )}

        {/* Corpo: só Serviços + Produtos */}
        {BLOCOS_PROPOSTA.map((b) => {
          const ls = linhas(b.key)
          if (ls.length === 0) return null
          return (
            <div key={b.key} className="py-4">
              <div className="text-muted-foreground mb-2 text-[0.625rem] font-bold tracking-wide uppercase">
                {b.titulo}
              </div>
              <Table className="text-xs">
                <TableHeader>
                  <TableRow>
                    <TableHead>Descrição</TableHead>
                    <TableHead className="text-right">QTD</TableHead>
                    <TableHead>Un</TableHead>
                    <TableHead className="text-right">Preço Unit</TableHead>
                    <TableHead className="text-right">Preço Total</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {ls.map((it) => (
                    <TableRow key={it.id}>
                      <TableCell className="font-medium">
                        {editavel ? (
                          <input
                            defaultValue={it.descricao_cliente ?? it.descricao}
                            onBlur={(e) => salvarDescricaoItem(it.id, e.target.value)}
                            className="w-full rounded border bg-transparent px-1 py-0.5 text-xs"
                          />
                        ) : (
                          it.descricao_cliente || it.descricao
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        {Number(it.quantidade).toLocaleString("pt-BR", { maximumFractionDigits: 1 })}
                      </TableCell>
                      <TableCell>{it.unidade}</TableCell>
                      <TableCell className="text-right">
                        {fmtBRL(it.preco_venda_unitario_final || it.preco_venda_unitario)}
                      </TableCell>
                      <TableCell className="text-right font-medium">{fmtBRL(it.preco_venda_total)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )
        })}

        {/* Rodapé financeiro */}
        <div className="mt-4 flex flex-col items-end gap-1 border-t pt-4 text-sm">
          <div className="flex w-56 justify-between">
            <span className="text-muted-foreground">Subtotal</span>
            <span>{fmtBRL(subtotal)}</span>
          </div>
          {descontoTotal > 0 && (orc.versao ?? 1) >= 2 && (
            <div className="flex w-56 justify-between">
              <span className="text-muted-foreground">Desconto ({Number(orc.desconto_percentual).toFixed(2)}%)</span>
              <span>- {fmtBRL(descontoTotal)}</span>
            </div>
          )}
          <div className="flex w-56 justify-between border-t pt-1 font-bold">
            <span>Total da Proposta</span>
            <span className="text-primary">{fmtBRL(totalLiquido)}</span>
          </div>
        </div>

        {orc.prazo_entrega && (
          <div className="text-muted-foreground mt-4 text-xs">
            <span className="font-medium">Prazo de entrega: </span>
            {orc.prazo_entrega}
          </div>
        )}
        {orc.tipo_frete && (
          <div className="text-muted-foreground mt-1 text-xs">
            <span className="font-medium">Tipo de frete: </span>
            {orc.tipo_frete}
          </div>
        )}
        {orc.condicoes_pagamento && (
          <div className="text-muted-foreground mt-1 text-xs">
            <span className="font-medium">Condições de pagamento: </span>
            {orc.condicoes_pagamento}
          </div>
        )}
        {(orc.texto_livre_proposta || editavel) && (
          editavel ? (
            <textarea
              defaultValue={orc.texto_livre_proposta ?? ""}
              placeholder="Condições, validade, observações…"
              onBlur={(e) => salvarTextoOrc("texto_livre_proposta", e.target.value)}
              className="text-muted-foreground mt-2 w-full resize-none rounded border bg-transparent p-2 text-xs"
              rows={2}
            />
          ) : (
            <p className="text-muted-foreground mt-2 text-xs whitespace-pre-wrap">{orc.texto_livre_proposta}</p>
          )
        )}

        {/* Rodapé: Aprovado por (diretor) + Elaborado por (orçamentista) + QR */}
        <div className="mt-8 flex items-start justify-between border-t pt-4 text-xs">
          <div>
            <div className="text-muted-foreground mb-1 text-[0.625rem] font-semibold uppercase">Aprovado por</div>
            <div className="font-semibold">{config?.diretor_nome ?? "—"}</div>
            {config?.diretor_funcao && <div className="text-muted-foreground">{config.diretor_funcao}</div>}
            {config?.diretor_telefone && <div className="text-muted-foreground">{config.diretor_telefone}</div>}
            {config?.diretor_email && <div className="text-muted-foreground">{config.diretor_email}</div>}
          </div>
          <div className="flex items-start gap-3">
            <div className="text-right">
              <div className="text-muted-foreground mb-1 text-[0.625rem] font-semibold uppercase">Elaborado por</div>
              <div className="font-semibold">{orcamentista?.nome_completo ?? "—"}</div>
              {orcamentista?.funcao && <div className="text-muted-foreground">{orcamentista.funcao}</div>}
              {orcamentista?.telefone && <div className="text-muted-foreground">{orcamentista.telefone}</div>}
            </div>
            {waOrc && <QRCodeSVG value={waOrc} size={60} level="M" className="shrink-0" />}
          </div>
        </div>

        <p className="text-muted-foreground/70 mt-6 text-center text-[0.625rem]">
          Desenvolvido por Viaxis Tech HUB
        </p>
      </Card>
    </>
  )
}
