import { useEffect, useMemo, useState } from "react"
import { Link } from "react-router"
import { toast } from "sonner"
import {
  MagnifyingGlassIcon,
  PlusIcon,
  PencilSimpleIcon,
  PowerIcon,
} from "@phosphor-icons/react"

import { PageHeader } from "~/components/page-header"
import { StatusBadge } from "~/components/status-badge"
import { Badge } from "~/components/ui/badge"
import { Button } from "~/components/ui/button"
import { Card } from "~/components/ui/card"
import { Checkbox } from "~/components/ui/checkbox"
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "~/components/ui/dialog"
import { Input } from "~/components/ui/input"
import { Label } from "~/components/ui/label"
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

interface Cliente {
  id: number
  nome: string
  tipo?: string
  cnpj_cpf?: string
  contato_nome?: string
  contato_email?: string
  contato_telefone?: string
  ativo: boolean
}

function ClienteModal({
  cliente,
  open,
  onOpenChange,
  onSaved,
}: {
  cliente: Cliente | null
  open: boolean
  onOpenChange: (v: boolean) => void
  onSaved: () => void
}) {
  const editando = !!cliente
  const [v, setV] = useState<Record<string, string>>({})
  const [ativo, setAtivo] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (open) {
      setV({
        nome: cliente?.nome ?? "",
        tipo: cliente?.tipo ?? "",
        cnpj_cpf: cliente?.cnpj_cpf ?? "",
        contato_nome: cliente?.contato_nome ?? "",
        contato_email: cliente?.contato_email ?? "",
        contato_telefone: cliente?.contato_telefone ?? "",
      })
      setAtivo(cliente?.ativo ?? true)
    }
  }, [open, cliente])

  const set = (k: string, val: string) => setV((s) => ({ ...s, [k]: val }))

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    const payload: Record<string, unknown> = {
      nome: v.nome,
      tipo: v.tipo || null,
      cnpj_cpf: v.cnpj_cpf || null,
      contato_nome: v.contato_nome || null,
      contato_email: v.contato_email || null,
      contato_telefone: v.contato_telefone || null,
    }
    if (editando) payload.ativo = ativo
    try {
      if (editando) {
        await clienteApi.update(cliente!.id, payload)
        toast.success("Cliente atualizado")
      } else {
        await clienteApi.create(payload)
        toast.success("Cliente criado")
      }
      onOpenChange(false)
      onSaved()
    } catch (err: any) {
      toast.error(`Erro: ${err.message}`)
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>{editando ? "Editar Cliente" : "Novo Cliente"}</DialogTitle>
        </DialogHeader>
        <form onSubmit={submit} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="flex flex-col gap-2 sm:col-span-2">
            <Label>Razão Social / Nome *</Label>
            <Input required placeholder="Ex: Motiva Rodovias S.A." value={v.nome ?? ""} onChange={(e) => set("nome", e.target.value)} />
          </div>
          <div className="flex flex-col gap-2">
            <Label>CNPJ / CPF</Label>
            <Input placeholder="00.000.000/0001-00" value={v.cnpj_cpf ?? ""} onChange={(e) => set("cnpj_cpf", e.target.value)} />
          </div>
          <div className="flex flex-col gap-2">
            <Label>Tipo</Label>
            <Input placeholder="Público, Privado…" value={v.tipo ?? ""} onChange={(e) => set("tipo", e.target.value)} />
          </div>
          <div className="flex flex-col gap-2 sm:col-span-2">
            <Label>Nome do Contato</Label>
            <Input placeholder="Ex: João Silva" value={v.contato_nome ?? ""} onChange={(e) => set("contato_nome", e.target.value)} />
          </div>
          <div className="flex flex-col gap-2">
            <Label>E-mail do Contato</Label>
            <Input type="email" placeholder="joao@empresa.com" value={v.contato_email ?? ""} onChange={(e) => set("contato_email", e.target.value)} />
          </div>
          <div className="flex flex-col gap-2">
            <Label>Telefone</Label>
            <Input type="tel" placeholder="(41) 9 9999-9999" value={v.contato_telefone ?? ""} onChange={(e) => set("contato_telefone", e.target.value)} />
          </div>
          {editando && (
            <label className="flex cursor-pointer items-center gap-2 self-end sm:col-span-2">
              <Checkbox checked={ativo} onCheckedChange={(c) => setAtivo(!!c)} />
              <span className="text-sm">Cliente ativo</span>
            </label>
          )}
          <DialogFooter className="sm:col-span-2">
            <Button type="button" variant="secondary" onClick={() => onOpenChange(false)}>Cancelar</Button>
            <Button type="submit" disabled={saving}>
              {saving ? "Salvando…" : editando ? "Salvar Alterações" : "Criar Cliente"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

function OrcamentosClienteModal({
  cliente,
  onOpenChange,
}: {
  cliente: Cliente | null
  onOpenChange: (v: boolean) => void
}) {
  const [orcs, setOrcs] = useState<any[] | null>(null)
  const [erro, setErro] = useState("")

  useEffect(() => {
    if (!cliente) return
    setOrcs(null)
    orcamentoApi
      .list()
      .then((all) => setOrcs(all.filter((o) => o.cliente_id === cliente.id)))
      .catch((e) => setErro(e.message))
  }, [cliente])

  return (
    <Dialog open={!!cliente} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Orçamentos — {cliente?.nome}</DialogTitle>
        </DialogHeader>
        {erro ? (
          <p className="text-destructive">{erro}</p>
        ) : orcs === null ? (
          <p className="text-muted-foreground py-4 text-center text-sm">Carregando…</p>
        ) : orcs.length === 0 ? (
          <p className="text-muted-foreground py-4 text-center text-sm">Nenhum orçamento vinculado.</p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Nº</TableHead>
                <TableHead>Obra</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Total</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {orcs.map((o) => (
                <TableRow key={o.id}>
                  <TableCell className="text-primary font-mono text-xs">{o.numero}</TableCell>
                  <TableCell className="text-muted-foreground text-xs">{o.obra ?? "—"}</TableCell>
                  <TableCell><StatusBadge status={o.status} /></TableCell>
                  <TableCell className="text-right font-semibold">{fmtBRL(o.total_proposta)}</TableCell>
                  <TableCell>
                    <Button asChild variant="ghost" size="sm" onClick={() => onOpenChange(false)}>
                      <Link to={`/orcamentos/${o.id}`}>Abrir →</Link>
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </DialogContent>
    </Dialog>
  )
}

export default function Clientes() {
  const [todos, setTodos] = useState<Cliente[] | null>(null)
  const [erro, setErro] = useState("")
  const [busca, setBusca] = useState("")
  const [soAtivos, setSoAtivos] = useState(true)
  const [editar, setEditar] = useState<Cliente | null>(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [verOrcs, setVerOrcs] = useState<Cliente | null>(null)

  async function refresh() {
    setErro("")
    try {
      setTodos(await clienteApi.list())
    } catch (err: any) {
      setErro(err.message)
    }
  }

  useEffect(() => {
    refresh()
  }, [])

  const filtrados = useMemo(() => {
    if (!todos) return []
    let f = todos
    if (soAtivos) f = f.filter((c) => c.ativo)
    if (busca) {
      const q = busca.toLowerCase()
      f = f.filter((c) => c.nome.toLowerCase().includes(q) || (c.cnpj_cpf ?? "").toLowerCase().includes(q))
    }
    return f
  }, [todos, busca, soAtivos])

  function abrirNovo() {
    setEditar(null)
    setModalOpen(true)
  }
  function abrirEditar(c: Cliente) {
    setEditar(c)
    setModalOpen(true)
  }

  async function toggleAtivo(c: Cliente) {
    try {
      await clienteApi.update(c.id, { ativo: !c.ativo })
      toast.success(!c.ativo ? "Cliente ativado" : "Cliente desativado")
      refresh()
    } catch (err: any) {
      toast.error(`Erro: ${err.message}`)
    }
  }

  return (
    <>
      <PageHeader
        title="Clientes"
        subtitle="Cadastro de contratantes e histórico de propostas"
        actions={
          <>
            <div className="relative">
              <MagnifyingGlassIcon className="text-muted-foreground absolute top-1/2 left-2.5 size-4 -translate-y-1/2" />
              <Input className="w-56 pl-8" placeholder="Buscar por nome ou CNPJ…" value={busca} onChange={(e) => setBusca(e.target.value)} />
            </div>
            <label className="flex cursor-pointer items-center gap-2 text-sm">
              <Checkbox checked={soAtivos} onCheckedChange={(c) => setSoAtivos(!!c)} />
              Somente ativos
            </label>
            <Button size="sm" onClick={abrirNovo}>
              <PlusIcon className="size-4" /> Novo Cliente
            </Button>
          </>
        }
      />

      <Card className="overflow-x-auto py-0">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Razão Social</TableHead>
              <TableHead>CNPJ/CPF</TableHead>
              <TableHead>Contato</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Orçamentos</TableHead>
              <TableHead className="w-20"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {todos === null ? (
              <TableRow><TableCell colSpan={6} className="text-muted-foreground py-8 text-center">Carregando…</TableCell></TableRow>
            ) : erro ? (
              <TableRow><TableCell colSpan={6} className="text-destructive py-8 text-center">{erro}</TableCell></TableRow>
            ) : filtrados.length === 0 ? (
              <TableRow><TableCell colSpan={6} className="text-muted-foreground py-8 text-center">Nenhum cliente encontrado.</TableCell></TableRow>
            ) : (
              filtrados.map((c) => (
                <TableRow key={c.id}>
                  <TableCell>
                    <div className="font-medium">{c.nome}</div>
                    {c.contato_email && <div className="text-muted-foreground text-xs">{c.contato_email}</div>}
                  </TableCell>
                  <TableCell className="text-xs">{c.cnpj_cpf ?? "—"}</TableCell>
                  <TableCell className="text-xs">
                    {c.contato_nome ?? "—"}
                    {c.contato_telefone && <div className="text-muted-foreground">{c.contato_telefone}</div>}
                  </TableCell>
                  <TableCell>
                    {c.ativo ? <Badge variant="success">ATIVO</Badge> : <Badge variant="destructive">INATIVO</Badge>}
                  </TableCell>
                  <TableCell>
                    <Button variant="ghost" size="sm" onClick={() => setVerOrcs(c)}>Ver →</Button>
                  </TableCell>
                  <TableCell>
                    <div className="flex justify-end gap-1">
                      <Button variant="ghost" size="icon" title="Editar" onClick={() => abrirEditar(c)}>
                        <PencilSimpleIcon className="size-4" />
                      </Button>
                      <Button variant="ghost" size="icon" title={c.ativo ? "Desativar" : "Ativar"} onClick={() => toggleAtivo(c)}>
                        <PowerIcon className={c.ativo ? "text-warning size-4" : "text-success size-4"} />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </Card>

      <ClienteModal cliente={editar} open={modalOpen} onOpenChange={setModalOpen} onSaved={refresh} />
      <OrcamentosClienteModal cliente={verOrcs} onOpenChange={(v) => !v && setVerOrcs(null)} />
    </>
  )
}
