import { useEffect, useState } from "react"
import { toast } from "sonner"
import { PencilSimpleIcon, PlusIcon, TrashIcon, LinkIcon } from "@phosphor-icons/react"

import { PageHeader } from "~/components/page-header"
import { Badge } from "~/components/ui/badge"
import { Button } from "~/components/ui/button"
import { Card } from "~/components/ui/card"
import { Checkbox } from "~/components/ui/checkbox"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "~/components/ui/select"
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "~/components/ui/dialog"
import { Input } from "~/components/ui/input"
import { Label } from "~/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "~/components/ui/tabs"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "~/components/ui/table"
import { componenteApi, fichaApi, itemFichaApi, produtoApi, unidadeApi } from "~/lib/api"

type Tipo = "produto" | "componente"

function NovoModal({
  tipo,
  editItem,
  open,
  onOpenChange,
  onSaved,
}: {
  tipo: Tipo
  editItem?: any
  open: boolean
  onOpenChange: (v: boolean) => void
  onSaved: () => void
}) {
  const [v, setV] = useState<Record<string, string>>({})
  const [saving, setSaving] = useState(false)
  const [unidades, setUnidades] = useState<any[]>([])
  const api = tipo === "produto" ? produtoApi : componenteApi
  const isEdit = !!editItem

  useEffect(() => {
    unidadeApi.list().then(setUnidades).catch(() => {})
  }, [])

  useEffect(() => {
    if (open) {
      if (editItem) {
        setV({
          nome: editItem.nome || "",
          descricao: editItem.descricao || "",
          caracteristicas: editItem.caracteristicas || "",
          dimensoes: editItem.dimensoes || "",
          setor: editItem.setor || "",
          deposito_produtivo: editItem.deposito_produtivo || "",
          unidade_id: editItem.unidade_id ? String(editItem.unidade_id) : "",
        })
      } else {
        setV({})
      }
    }
  }, [open, editItem])

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    const payload = {
      nome: v.nome,
      descricao: v.descricao || null,
      caracteristicas: v.caracteristicas || null,
      dimensoes: v.dimensoes || null,
      setor: v.setor || null,
      deposito_produtivo: v.deposito_produtivo || null,
      unidade_id: v.unidade_id ? Number(v.unidade_id) : null,
    }
    try {
      if (isEdit) {
        await api.update(editItem.id, payload)
        toast.success("Registro atualizado")
      } else {
        await api.create(payload)
        toast.success("Registro criado")
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
          <DialogTitle>{isEdit ? "Editar" : "Novo"} {tipo === "produto" ? "Produto" : "Componente"}</DialogTitle>
        </DialogHeader>
        <form onSubmit={submit} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="flex flex-col gap-2 sm:col-span-2">
            <Label>Nome *</Label>
            <Input required value={v.nome ?? ""} onChange={(e) => setV((s) => ({ ...s, nome: e.target.value }))} />
          </div>
          <div className="flex flex-col gap-2 sm:col-span-2">
            <Label>Descrição</Label>
            <Input value={v.descricao ?? ""} onChange={(e) => setV((s) => ({ ...s, descricao: e.target.value }))} />
          </div>
          <div className="flex flex-col gap-2">
            <Label>Dimensões</Label>
            <Input placeholder="100x50x30 cm" value={v.dimensoes ?? ""} onChange={(e) => setV((s) => ({ ...s, dimensoes: e.target.value }))} />
          </div>
          <div className="flex flex-col gap-2">
            <Label>Setor</Label>
            <Input value={v.setor ?? ""} onChange={(e) => setV((s) => ({ ...s, setor: e.target.value }))} />
          </div>
          <div className="flex flex-col gap-2">
            <Label>Unidade</Label>
            <Select value={v.unidade_id ?? ""} onValueChange={(val) => setV((s) => ({ ...s, unidade_id: val }))}>
              <SelectTrigger><SelectValue placeholder="Selecione…" /></SelectTrigger>
              <SelectContent>
                {unidades.map((u: any) => (
                  <SelectItem key={u.id} value={String(u.id)}>{u.sigla} — {u.nome}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex flex-col gap-2 sm:col-span-2">
            <Label>Depósito Produtivo</Label>
            <Input value={v.deposito_produtivo ?? ""} onChange={(e) => setV((s) => ({ ...s, deposito_produtivo: e.target.value }))} />
          </div>
          <DialogFooter className="sm:col-span-2">
            <Button type="button" variant="secondary" onClick={() => onOpenChange(false)}>Cancelar</Button>
            <Button type="submit" disabled={saving}>{saving ? "Salvando…" : isEdit ? "Atualizar" : "Criar"}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

function AtribuirFichaModal({
  tipo,
  item,
  onClose,
}: {
  tipo: Tipo
  item: any | null
  onClose: () => void
}) {
  const [fichas, setFichas] = useState<{ id: number; label: string; tipo: string }[]>([])
  const [sel, setSel] = useState<Set<string>>(new Set())
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!item) return
    setSel(new Set())
    Promise.all([
      fichaApi.listServicos(),
      fichaApi.listProdutos(),
      fichaApi.listEquipes(),
    ]).then(([sv, pr, eq]) => {
      setFichas([
        ...sv.map((f) => ({ id: f.id, label: `Serviço ${f.codigo} — ${f.nome}`, tipo: "servico" })),
        ...pr.map((f) => ({ id: f.id, label: `Produto ${f.codigo} — ${f.nome}`, tipo: "produto" })),
        ...eq.map((f) => ({ id: f.id, label: `Equipe ${f.codigo}`, tipo: "equipe" })),
      ])
    })
  }, [item])

  async function salvar() {
    if (!item || sel.size === 0) return
    setSaving(true)
    try {
      for (const key of sel) {
        const [ftipo, fid] = key.split(":")
        const body: Record<string, number> = {}
        body[tipo === "produto" ? "produto_id" : "componente_id"] = item.id
        body[`ficha_${ftipo}_id`] = Number(fid)
        await itemFichaApi.create(body)
      }
      toast.success("Ficha(s) atribuída(s)")
      onClose()
    } catch (err: any) {
      toast.error(`Erro: ${err.message}`)
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open={!!item} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Atribuir Ficha Técnica — {item?.nome}</DialogTitle>
        </DialogHeader>
        <div className="max-h-80 space-y-1 overflow-y-auto">
          {fichas.length === 0 ? (
            <p className="text-muted-foreground py-4 text-center text-sm">Nenhuma ficha cadastrada.</p>
          ) : (
            fichas.map((f) => {
              const key = `${f.tipo}:${f.id}`
              return (
                <label key={key} className="hover:bg-muted/50 flex cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-sm">
                  <Checkbox
                    checked={sel.has(key)}
                    onCheckedChange={(c) =>
                      setSel((s) => {
                        const n = new Set(s)
                        c ? n.add(key) : n.delete(key)
                        return n
                      })
                    }
                  />
                  {f.label}
                </label>
              )
            })
          )}
        </div>
        <DialogFooter>
          <Button variant="secondary" onClick={onClose}>Cancelar</Button>
          <Button onClick={salvar} disabled={saving || sel.size === 0}>
            {saving ? "Salvando…" : `Atribuir (${sel.size})`}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

function Aba({ tipo }: { tipo: Tipo }) {
  const api = tipo === "produto" ? produtoApi : componenteApi
  const [rows, setRows] = useState<any[] | null>(null)
  const [novoOpen, setNovoOpen] = useState(false)
  const [editItem, setEditItem] = useState<any | null>(null)
  const [atribuir, setAtribuir] = useState<any | null>(null)

  async function refresh() {
    setRows(null)
    try {
      setRows(await api.list())
    } catch (e: any) {
      toast.error(e.message)
    }
  }
  useEffect(() => {
    refresh()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tipo])

  async function remover(id: number) {
    if (!confirm("Excluir este registro?")) return
    try {
      await api.delete(id)
      refresh()
    } catch (e: any) {
      toast.error(e.message)
    }
  }

  return (
    <>
      <div className="mb-3 flex justify-end">
        <Button size="sm" onClick={() => setNovoOpen(true)}>
          <PlusIcon className="size-4" /> Novo {tipo === "produto" ? "Produto" : "Componente"}
        </Button>
      </div>
      <Card className="overflow-x-auto py-0">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Código</TableHead>
              <TableHead>Nome</TableHead>
              <TableHead>Und</TableHead>
              <TableHead>Setor</TableHead>
              <TableHead>Dimensões</TableHead>
              <TableHead>Ficha Técnica</TableHead>
              <TableHead className="w-24"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows === null ? (
              <TableRow><TableCell colSpan={6} className="text-muted-foreground py-8 text-center">Carregando…</TableCell></TableRow>
            ) : rows.length === 0 ? (
              <TableRow><TableCell colSpan={6} className="text-muted-foreground py-8 text-center">Nenhum registro.</TableCell></TableRow>
            ) : (
              rows.map((r) => (
                <TableRow key={r.id}>
                  <TableCell className="text-primary font-mono text-xs">{r.codigo}</TableCell>
                  <TableCell><strong>{r.nome}</strong></TableCell>
                  <TableCell className="text-muted-foreground text-xs">{r.unidade_sigla ?? "—"}</TableCell>
                  <TableCell className="text-muted-foreground text-xs">{r.setor ?? "—"}</TableCell>
                  <TableCell className="text-muted-foreground text-xs">{r.dimensoes ?? "—"}</TableCell>
                  <TableCell>
                    {r.possui_ficha_tecnica ? <Badge variant="success">SIM</Badge> : <Badge variant="secondary">NÃO</Badge>}
                  </TableCell>
                  <TableCell>
                    <div className="flex justify-end gap-1">
                      <Button variant="ghost" size="icon" title="Editar" onClick={() => { setEditItem(r); setNovoOpen(true) }}>
                        <PencilSimpleIcon className="text-muted-foreground size-4" />
                      </Button>
                      <Button variant="ghost" size="icon" title="Atribuir ficha técnica" onClick={() => setAtribuir(r)}>
                        <LinkIcon className="size-4" />
                      </Button>
                      <Button variant="ghost" size="icon" title="Excluir" onClick={() => remover(r.id)}>
                        <TrashIcon className="text-destructive size-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </Card>

      <NovoModal tipo={tipo} editItem={editItem} open={novoOpen} onOpenChange={(v) => { setNovoOpen(v); if (!v) setEditItem(null) }} onSaved={refresh} />
      <AtribuirFichaModal tipo={tipo} item={atribuir} onClose={() => { setAtribuir(null); refresh() }} />
    </>
  )
}

export default function ProdutosComponentes() {
  return (
    <>
      <PageHeader title="Produtos e Componentes" subtitle="Cadastro industrial e atribuição de fichas técnicas" />
      <Tabs defaultValue="produtos">
        <TabsList>
          <TabsTrigger value="produtos">Produtos</TabsTrigger>
          <TabsTrigger value="componentes">Componentes</TabsTrigger>
        </TabsList>
        <TabsContent value="produtos" className="mt-4">
          <Aba tipo="produto" />
        </TabsContent>
        <TabsContent value="componentes" className="mt-4">
          <Aba tipo="componente" />
        </TabsContent>
      </Tabs>
    </>
  )
}
