import { useCallback, useEffect, useState } from "react"
import { Link, useParams } from "react-router"
import { toast } from "sonner"
import { ArrowLeftIcon, FileTextIcon } from "@phosphor-icons/react"

import { StatusBadge } from "~/components/status-badge"
import { Button } from "~/components/ui/button"
import { orcamentoApi } from "~/lib/api"
import { SecaoCard } from "~/components/secao-card"
import { CampoTexto, CampoTextarea } from "~/components/campo-proposta"
import { fmtBRL, fmtData } from "~/lib/format"

const EDITAVEL = ["rascunho", "reprovado"]

export default function PropostaEditor() {
  const { id } = useParams()
  const orcId = Number(id)

  const [data, setData] = useState<any>(null)
  const [erro, setErro] = useState("")
  const [carregando, setCarregando] = useState(true)

  const carregar = useCallback(async () => {
    setCarregando(true)
    setErro("")
    try {
      setData(await orcamentoApi.getProposta(orcId))
    } catch (e: any) {
      setErro(e.message)
    } finally {
      setCarregando(false)
    }
  }, [orcId])

  useEffect(() => {
    carregar()
  }, [carregar])

  if (carregando) {
    return <div className="text-muted-foreground py-12 text-center">Carregando proposta…</div>
  }
  if (erro || !data?.orcamento) {
    return (
      <div className="py-12 text-center">
        <h3 className="text-lg font-semibold">Erro ao carregar proposta</h3>
        <p className="text-muted-foreground mt-1">{erro}</p>
        <Button asChild variant="secondary" className="mt-4">
          <Link to={`/orcamentos/${orcId}`}>← Voltar ao orçamento</Link>
        </Button>
      </div>
    )
  }

  const { orcamento: orc } = data
  const readonly = !EDITAVEL.includes(orc.status)

  // Salva um campo do orçamento (PUT /orcamentos/:id) e atualiza o estado local.
  async function salvarOrc(campo: string, valor: string | number | null) {
    try {
      await orcamentoApi.update(orcId, { [campo]: valor })
      setData((d: any) => ({ ...d, orcamento: { ...d.orcamento, [campo]: valor } }))
    } catch (e: any) {
      toast.error(`Erro ao salvar: ${e.message}`)
    }
  }

  const { cliente, config, itens, resolvidos, garantia_texto } = data
  const FATURAVEIS = ["servicos", "produtos"]
  const itensFat = (itens ?? []).filter((i: any) => FATURAVEIS.includes(i.bloco))
  const temPrecos = itensFat.some((i: any) => parseFloat(i.preco_venda_total) > 0)

  const INDICE = [
    "1. Cabeçalho", "2. Destinatário", "3. Objeto", "4. Declarações",
    "5. Escopo", "6. Modalidade", "7. Preço", "8. Prazo + Tributária",
    "9. Faturamento", "10. Medição", "11. Bancários", "12. Representante",
    "13. Testemunha", "14. Reajustamento", "15. Garantia", "16. As Built",
    "17. Validade", "18. Observação", "19. Contato",
  ]

  async function salvarDescricaoItem(iid: number, valor: string) {
    try {
      const upd = await orcamentoApi.patchDescricaoItem(orcId, iid, valor)
      setData((d: any) => ({
        ...d,
        itens: d.itens.map((i: any) => (i.id === iid ? { ...i, ...upd } : i)),
      }))
    } catch (e: any) {
      toast.error(`Erro: ${e.message}`)
    }
  }

  // Texto de garantia recalculado localmente p/ feedback imediato.
  const garTexto =
    orc.garantia_retencao_pct != null && orc.garantia_devolucao_dias != null
      ? `Retenção de ${Number(orc.garantia_retencao_pct)}%, com devolução em ${orc.garantia_devolucao_dias} dias após o termo de encerramento.`
      : garantia_texto || "—"

  return (
    <>
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Button asChild variant="ghost" size="icon">
            <Link to={`/orcamentos/${orcId}`} aria-label="Voltar">
              <ArrowLeftIcon className="size-4" />
            </Link>
          </Button>
          <h2 className="text-xl font-semibold">Proposta {orc.numero}</h2>
          <StatusBadge status={orc.status} />
        </div>
        <Button asChild size="sm" variant="ghost">
          <Link to={`/orcamentos/${orcId}/proposta`}>
            <FileTextIcon className="size-4" /> Ver documento
          </Link>
        </Button>
      </div>

      {readonly && (
        <p className="text-warning bg-warning/10 mb-4 rounded p-2.5 text-center text-xs">
          Orçamento com status "{orc.status}" — somente leitura.
        </p>
      )}

      <div className="grid grid-cols-1 items-start gap-5 lg:grid-cols-[1fr_180px]">
        <div className="space-y-4">
          {/* 1. Cabeçalho — sistema, read-only */}
          <SecaoCard id="sec-1" titulo="1. Cabeçalho" badge="sistema">
            <div className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
              <div><div className="text-muted-foreground text-xs uppercase">Nº</div>{orc.numero}</div>
              <div><div className="text-muted-foreground text-xs uppercase">Versão</div>{orc.versao}</div>
              <div><div className="text-muted-foreground text-xs uppercase">Data</div>{fmtData(orc.created_at)}</div>
              <div><div className="text-muted-foreground text-xs uppercase">UF</div>{orc.uf_execucao}</div>
            </div>
          </SecaoCard>

          {/* 2. Destinatário — cliente, read-only */}
          <SecaoCard id="sec-2" titulo="2. Destinatário" badge="existente">
            <div className="text-sm">
              <div className="font-medium">{cliente?.nome ?? `#${orc.cliente_id}`}</div>
              {cliente?.cnpj_cpf && <div className="text-muted-foreground text-xs">{cliente.cnpj_cpf}</div>}
              {cliente?.contato_nome && <div className="text-muted-foreground text-xs">{cliente.contato_nome}</div>}
            </div>
          </SecaoCard>

          {/* 3. Objeto */}
          <SecaoCard id="sec-3" titulo="3. Objeto" badge="existente">
            <CampoTextarea label="Obra" value={orc.obra ?? ""} readonly={readonly} rows={2}
              onSave={(v) => salvarOrc("obra", v)} placeholder="Descrição da obra/objeto" />
          </SecaoCard>

          {/* 4. Declarações — fallback declaracoes_padrao */}
          <SecaoCard id="sec-4" titulo="4. Declarações" badge="existente">
            <CampoTextarea label="Texto topo (declarações)" value={orc.texto_topo_proposta ?? ""}
              readonly={readonly} rows={5}
              placeholderFallback={resolvidos?.texto_topo_proposta}
              onSave={(v) => salvarOrc("texto_topo_proposta", v)} />
          </SecaoCard>

          {/* 5. Escopo */}
          <SecaoCard id="sec-5" titulo="5. Escopo" badge="novo">
            <CampoTextarea label="Escopo detalhado" value={orc.escopo ?? ""} readonly={readonly} rows={4}
              onSave={(v) => salvarOrc("escopo", v)} placeholder="Descrição detalhada do escopo" />
          </SecaoCard>

          {/* 6. Modalidade */}
          <SecaoCard id="sec-6" titulo="6. Modalidade" badge="novo">
            <CampoTexto label="Modalidade" value={orc.modalidade ?? ""} readonly={readonly}
              placeholderFallback={resolvidos?.modalidade}
              onSave={(v) => salvarOrc("modalidade", v)} />
          </SecaoCard>

          {/* 7. Preço — só descrição editável; qtd/preços read-only */}
          <SecaoCard id="sec-7" titulo="7. Preço" badge="sistema">
            {!temPrecos && (
              <p className="text-warning bg-warning/10 rounded p-2 text-center text-xs">
                Calcule o orçamento para ver os preços.
              </p>
            )}
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-muted-foreground text-[0.625rem] uppercase">
                    <th className="px-2 py-1 text-left">Descrição (cliente)</th>
                    <th className="px-2 py-1 text-center">Un</th>
                    <th className="px-2 py-1 text-right">Qtd</th>
                    <th className="px-2 py-1 text-right">Preço Unit</th>
                    <th className="px-2 py-1 text-right">Preço Total</th>
                  </tr>
                </thead>
                <tbody>
                  {itensFat.length === 0 ? (
                    <tr><td colSpan={5} className="text-muted-foreground py-3 text-center">Nenhum item faturável.</td></tr>
                  ) : itensFat.map((it: any) => (
                    <tr key={it.id} className="border-t">
                      <td className="px-2 py-1">
                        {readonly ? (
                          <span>{it.descricao_cliente || it.descricao}</span>
                        ) : (
                          <input
                            defaultValue={it.descricao_cliente ?? it.descricao}
                            onBlur={(e) => {
                              const nv = e.target.value
                              if (nv !== (it.descricao_cliente ?? it.descricao)) salvarDescricaoItem(it.id, nv)
                            }}
                            className="border-primary w-full rounded border bg-transparent px-1.5 py-0.5"
                          />
                        )}
                      </td>
                      <td className="text-muted-foreground px-2 py-1 text-center">{it.unidade}</td>
                      <td className="text-muted-foreground px-2 py-1 text-right">
                        {Number(it.quantidade).toLocaleString("pt-BR", { maximumFractionDigits: 2 })}
                      </td>
                      <td className="text-muted-foreground px-2 py-1 text-right">
                        {parseFloat(it.preco_venda_total) > 0 ? fmtBRL(it.preco_venda_unitario_final || it.preco_venda_unitario) : "—"}
                      </td>
                      <td className="px-2 py-1 text-right font-medium">
                        {parseFloat(it.preco_venda_total) > 0 ? fmtBRL(it.preco_venda_total) : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="text-right text-sm">
              Total: <span className="text-primary text-base font-bold">
                {orc.total_proposta ? fmtBRL(orc.total_proposta) : "—"}
              </span>
            </div>
          </SecaoCard>

          {/* 8. Prazo + Tributária */}
          <SecaoCard id="sec-8" titulo="8. Prazo + Tributária" badge="novo">
            <CampoTexto label="Prazo de entrega" value={orc.prazo_entrega ?? ""} readonly={readonly}
              onSave={(v) => salvarOrc("prazo_entrega", v)} placeholder="90 (noventa) dias…" />
            <CampoTextarea label="Cláusula tributária (IBS/CBS)" value={orc.clausula_tributaria ?? ""}
              readonly={readonly} rows={4}
              placeholderFallback={resolvidos?.clausula_tributaria}
              onSave={(v) => salvarOrc("clausula_tributaria", v)} />
          </SecaoCard>

          {/* 9. Faturamento */}
          <SecaoCard id="sec-9" titulo="9. Faturamento Direto" badge="novo">
            <CampoTexto label="Faturamento direto" value={orc.faturamento_direto ?? ""} readonly={readonly}
              placeholderFallback={resolvidos?.faturamento_direto}
              onSave={(v) => salvarOrc("faturamento_direto", v)} />
          </SecaoCard>

          {/* 10. Medição */}
          <SecaoCard id="sec-10" titulo="10. Medição e Pagamento" badge="novo">
            <CampoTextarea label="Medição e pagamento" value={orc.medicao_pagamento ?? ""}
              readonly={readonly} rows={3}
              onSave={(v) => salvarOrc("medicao_pagamento", v)} placeholder="Critérios de medição…" />
          </SecaoCard>

          {/* 11. Dados Bancários — config, read-only */}
          <SecaoCard id="sec-11" titulo="11. Dados Bancários" badge="novo">
            <div className="grid grid-cols-3 gap-3 text-sm">
              <div><div className="text-muted-foreground text-xs uppercase">Banco</div>{config?.banco ?? "—"}</div>
              <div><div className="text-muted-foreground text-xs uppercase">Agência</div>{config?.agencia ?? "—"}</div>
              <div><div className="text-muted-foreground text-xs uppercase">Conta</div>{config?.conta_corrente ?? "—"}</div>
            </div>
            <Link to="/parametros" className="text-primary text-xs hover:underline">→ editar em Parâmetros</Link>
          </SecaoCard>

          {/* 12. Representante — config, read-only */}
          <SecaoCard id="sec-12" titulo="12. Representante Legal" badge="existente">
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div><div className="text-muted-foreground text-xs uppercase">Nome</div>{config?.diretor_nome ?? "—"}</div>
              <div><div className="text-muted-foreground text-xs uppercase">Função</div>{config?.diretor_funcao ?? "—"}</div>
              <div><div className="text-muted-foreground text-xs uppercase">CPF</div>{config?.diretor_cpf ?? "—"}</div>
              <div><div className="text-muted-foreground text-xs uppercase">CNPJ</div>{config?.cnpj ?? "—"}</div>
            </div>
            <Link to="/parametros" className="text-primary text-xs hover:underline">→ editar em Parâmetros</Link>
          </SecaoCard>

          {/* 13. Testemunha */}
          <SecaoCard id="sec-13" titulo="13. Testemunha" badge="novo">
            <CampoTexto label="Nome" value={orc.testemunha_nome ?? ""} readonly={readonly}
              onSave={(v) => salvarOrc("testemunha_nome", v)} />
            <CampoTexto label="E-mail" value={orc.testemunha_email ?? ""} readonly={readonly}
              onSave={(v) => salvarOrc("testemunha_email", v)} />
            <CampoTexto label="CPF" value={orc.testemunha_cpf ?? ""} readonly={readonly}
              onSave={(v) => salvarOrc("testemunha_cpf", v)} />
          </SecaoCard>

          {/* 14. Reajustamento — fallback */}
          <SecaoCard id="sec-14" titulo="14. Reajustamento" badge="novo">
            <CampoTextarea label="Reajustamento (IPCA/IGPM)" value={orc.reajustamento ?? ""}
              readonly={readonly} rows={4}
              placeholderFallback={resolvidos?.reajustamento}
              onSave={(v) => salvarOrc("reajustamento", v)} />
          </SecaoCard>

          {/* 15. Garantia — pct/dias + texto auto */}
          <SecaoCard id="sec-15" titulo="15. Garantia Contratual" badge="novo">
            <div className="grid grid-cols-2 gap-3">
              <CampoTexto label="Retenção (%)" value={orc.garantia_retencao_pct != null ? String(orc.garantia_retencao_pct) : ""}
                readonly={readonly} placeholderFallback={resolvidos?.garantia_retencao_pct != null ? String(resolvidos.garantia_retencao_pct) : undefined}
                onSave={(v) => salvarOrc("garantia_retencao_pct", v === "" ? null : v)} />
              <CampoTexto label="Devolução (dias)" value={orc.garantia_devolucao_dias != null ? String(orc.garantia_devolucao_dias) : ""}
                readonly={readonly} placeholderFallback={resolvidos?.garantia_devolucao_dias != null ? String(resolvidos.garantia_devolucao_dias) : undefined}
                onSave={(v) => salvarOrc("garantia_devolucao_dias", v === "" ? null : Number(v))} />
            </div>
            <p className="text-muted-foreground text-xs">{garTexto}</p>
          </SecaoCard>

          {/* 16. As Built */}
          <SecaoCard id="sec-16" titulo="16. Entrega de As Built" badge="novo">
            <CampoTexto label="Entrega de as built" value={orc.entrega_as_built ?? ""} readonly={readonly}
              placeholderFallback={resolvidos?.entrega_as_built}
              onSave={(v) => salvarOrc("entrega_as_built", v)} />
          </SecaoCard>

          {/* 17. Validade */}
          <SecaoCard id="sec-17" titulo="17. Validade da Proposta" badge="existente">
            <CampoTexto label="Validade" value={orc.validade_proposta ?? ""} readonly={readonly}
              onSave={(v) => salvarOrc("validade_proposta", v)} placeholder="90 (noventa) dias…" />
          </SecaoCard>

          {/* 18. Observação */}
          <SecaoCard id="sec-18" titulo="18. Observação" badge="existente">
            <CampoTextarea label="Texto livre / observações" value={orc.texto_livre_proposta ?? ""}
              readonly={readonly} rows={3}
              onSave={(v) => salvarOrc("texto_livre_proposta", v)} placeholder="Observações finais…" />
          </SecaoCard>

          {/* 19. Contato Comercial — config, read-only */}
          <SecaoCard id="sec-19" titulo="19. Contato Comercial" badge="novo">
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div><div className="text-muted-foreground text-xs uppercase">Nome</div>{config?.contato_comercial_nome ?? "—"}</div>
              <div><div className="text-muted-foreground text-xs uppercase">Função</div>{config?.contato_comercial_funcao ?? "—"}</div>
              <div><div className="text-muted-foreground text-xs uppercase">Fone</div>{config?.contato_comercial_fone ?? "—"}</div>
              <div><div className="text-muted-foreground text-xs uppercase">E-mail</div>{config?.contato_comercial_email ?? "—"}</div>
            </div>
            <Link to="/parametros" className="text-primary text-xs hover:underline">→ editar em Parâmetros</Link>
          </SecaoCard>
        </div>
        <nav className="sticky top-4 hidden lg:block">
          <div className="text-muted-foreground mb-2 text-[0.625rem] font-semibold uppercase">Seções</div>
          <ul className="space-y-0.5 text-xs">
            {INDICE.map((label, i) => (
              <li key={i}>
                <a href={`#sec-${i + 1}`} className="text-muted-foreground hover:text-foreground block rounded px-2 py-1 hover:bg-secondary">
                  {label}
                </a>
              </li>
            ))}
          </ul>
        </nav>
      </div>
    </>
  )
}
