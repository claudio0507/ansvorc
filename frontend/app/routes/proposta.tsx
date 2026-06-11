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
  const nomeEmpresa = config?.nome_empresa ?? "ALTA NOROESTE"
  const hoje = new Date().toLocaleDateString("pt-BR")

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
        <div className="flex items-start justify-between border-b pb-5">
          <div className="flex items-center gap-3">
            {config?.logo_path ? (
              <img src={config.logo_path} alt="logo" className="h-12 max-w-[160px] object-contain" />
            ) : (
              <div className="bg-primary text-primary-foreground flex size-12 items-center justify-center">
                <svg viewBox="0 0 24 24" className="size-6 fill-current">
                  <path d="M12 2L2 7l10 5 10-5-10-5zm0 10L2 7v10l10 5 10-5V7l-10 5z" />
                </svg>
              </div>
            )}
            <div>
              <div className="text-xl font-bold tracking-tight">orcOS</div>
              <div className="text-muted-foreground text-xs font-medium tracking-[0.1em] uppercase">
                {nomeEmpresa}
              </div>
            </div>
          </div>
          <div className="text-right text-xs">
            <div className="font-semibold">Proposta {orc.numero}</div>
            <div className="text-muted-foreground">Emissão: {hoje}</div>
            {orc.validade_proposta && (
              <div className="text-muted-foreground">Validade: {orc.validade_proposta}</div>
            )}
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
                        {it.descricao_cliente || it.descricao}
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
          {descontoTotal > 0 && (
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

        {orc.condicoes_pagamento && (
          <div className="text-muted-foreground mt-5 text-xs">
            <span className="font-medium">Condições de pagamento: </span>
            {orc.condicoes_pagamento}
          </div>
        )}
        {orc.texto_livre_proposta && (
          <p className="text-muted-foreground mt-2 text-xs whitespace-pre-wrap">{orc.texto_livre_proposta}</p>
        )}

        <p className="text-muted-foreground/70 mt-8 text-center text-[0.625rem]">
          Desenvolvido por Viaxis Tech HUB
        </p>
      </Card>
    </>
  )
}
