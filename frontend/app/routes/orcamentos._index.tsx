import { useEffect, useMemo, useState } from "react"
import { Link, useNavigate } from "react-router"
import { toast } from "sonner"
import { PlusIcon, PencilSimpleIcon, TrashIcon, MagnifyingGlassIcon } from "@phosphor-icons/react"

import { NovoOrcamentoModal } from "~/components/novo-orcamento-modal"
import { PageHeader } from "~/components/page-header"
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
import { clienteApi, orcamentoApi } from "~/lib/api"
import { fmtBRL } from "~/lib/format"

const FILTROS = [
  { key: "", label: "Todos" },
  { key: "rascunho", label: "Rascunho" },
  { key: "enviado", label: "Enviado" },
  { key: "aprovado", label: "Aprovado" },
  { key: "rejeitado", label: "Rejeitado" },
]

export default function OrcamentosLista() {
  const navigate = useNavigate()
  const [orcs, setOrcs] = useState<any[] | null>(null)
  const [clientesMap, setClientesMap] = useState<Record<number, string>>({})
  const [erro, setErro] = useState("")
  const [filtro, setFiltro] = useState("")
  const [busca, setBusca] = useState("")
  const [modalOpen, setModalOpen] = useState(false)

  async function refresh() {
    setErro("")
    try {
      const [todos, clientes] = await Promise.all([
        orcamentoApi.list(),
        clienteApi.list().catch(() => [] as any[]),
      ])
      setClientesMap(Object.fromEntries(clientes.map((c: any) => [c.id, c.nome])))
      setOrcs(todos)
    } catch (err: any) {
      setErro(err.message)
    }
  }

  useEffect(() => {
    refresh()
  }, [])

  const filtrados = useMemo(() => {
    if (!orcs) return []
    // BLOCO 5.3: mostrar apenas a versão mais recente de cada grupo.
    // Grupo = número base (sem sufixo -vN). Mantém o de maior versão.
    const baseNum = (n: string) => String(n ?? "").replace(/-v\d+$/i, "")
    const maisRecentePorGrupo = new Map<string, any>()
    for (const o of orcs) {
      const k = baseNum(o.numero)
      const atual = maisRecentePorGrupo.get(k)
      if (!atual || (o.versao ?? 1) > (atual.versao ?? 1)) {
        maisRecentePorGrupo.set(k, o)
      }
    }
    let r = Array.from(maisRecentePorGrupo.values())
    if (filtro) r = r.filter((o) => o.status === filtro)
    const q = busca.trim().toLowerCase()
    if (q) {
      r = r.filter(
        (o) =>
          String(o.numero ?? "").toLowerCase().includes(q) ||
          String(o.obra ?? "").toLowerCase().includes(q) ||
          String(clientesMap[o.cliente_id] ?? "").toLowerCase().includes(q)
      )
    }
    return r
  }, [orcs, filtro, busca, clientesMap])

  async function del(id: number) {
    if (!confirm("Excluir orçamento e todos os seus itens?")) return
    try {
      await orcamentoApi.delete(id)
      toast.success("Orçamento excluído")
      refresh()
    } catch (err: any) {
      toast.error(`Erro: ${err.message}`)
    }
  }

  return (
    <>
      <PageHeader
        title="Orçamentos"
        subtitle="Gestão de propostas comerciais"
        actions={
          <>
            <div className="relative">
              <MagnifyingGlassIcon className="text-muted-foreground absolute top-1/2 left-2.5 size-4 -translate-y-1/2" />
              <Input
                className="w-56 pl-8"
                placeholder="Buscar nº, cliente ou obra…"
                value={busca}
                onChange={(e) => setBusca(e.target.value)}
              />
            </div>
            <Button size="sm" onClick={() => setModalOpen(true)}>
              <PlusIcon className="size-4" /> Novo Orçamento
            </Button>
          </>
        }
      />

      <div className="mb-3 flex flex-wrap gap-2">
        {FILTROS.map((f) => (
          <Button
            key={f.key}
            size="sm"
            variant={filtro === f.key ? "default" : "secondary"}
            onClick={() => setFiltro(f.key)}
          >
            {f.label}
          </Button>
        ))}
      </div>

      <Card className="py-0">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Nº Proposta</TableHead>
              <TableHead>Cliente</TableHead>
              <TableHead>Obra</TableHead>
              <TableHead>UF</TableHead>
              <TableHead>REIDI</TableHead>
              <TableHead className="text-right">Total</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="w-20"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {orcs === null ? (
              <TableRow><TableCell colSpan={8} className="text-muted-foreground py-8 text-center">Carregando…</TableCell></TableRow>
            ) : erro ? (
              <TableRow><TableCell colSpan={8} className="text-destructive py-8 text-center">Erro: {erro}</TableCell></TableRow>
            ) : filtrados.length === 0 ? (
              <TableRow><TableCell colSpan={8} className="text-muted-foreground py-8 text-center">
                Nenhum orçamento{filtro ? ` com status "${filtro}"` : ""}.
              </TableCell></TableRow>
            ) : (
              filtrados.map((o) => (
                <TableRow key={o.id} className="cursor-pointer" onClick={() => navigate(`/orcamentos/${o.id}`)}>
                  <TableCell className="text-primary font-mono text-xs">{o.numero}</TableCell>
                  <TableCell className="text-sm">{clientesMap[o.cliente_id] ?? `#${o.cliente_id}`}</TableCell>
                  <TableCell className="text-muted-foreground text-xs">{o.obra ?? "—"}</TableCell>
                  <TableCell><Badge variant="secondary">{o.uf_execucao}</Badge></TableCell>
                  <TableCell>
                    {o.beneficio_reidi ? <Badge variant="success">SIM</Badge> : <Badge variant="secondary">NÃO</Badge>}
                  </TableCell>
                  <TableCell className="text-right font-semibold">{fmtBRL(o.total_proposta)}</TableCell>
                  <TableCell><StatusBadge status={o.status} /></TableCell>
                  <TableCell onClick={(e) => e.stopPropagation()}>
                    <div className="flex justify-end gap-1">
                      <Button asChild variant="ghost" size="icon" title="Abrir">
                        <Link to={`/orcamentos/${o.id}`}><PencilSimpleIcon className="size-4" /></Link>
                      </Button>
                      {o.status === "rascunho" && (
                        <Button variant="ghost" size="icon" title="Excluir" onClick={() => del(o.id)}>
                          <TrashIcon className="text-destructive size-4" />
                        </Button>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </Card>

      <NovoOrcamentoModal
        open={modalOpen}
        onOpenChange={setModalOpen}
        onCreated={(novo) => navigate(`/orcamentos/${novo.id}`)}
      />
    </>
  )
}
