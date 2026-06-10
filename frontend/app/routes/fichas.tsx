import { useEffect, useMemo, useState } from "react"
import { useParams } from "react-router"
import { toast } from "sonner"
import { MagnifyingGlassIcon, PlusIcon, TrashIcon } from "@phosphor-icons/react"

import { PageHeader } from "~/components/page-header"
import { Badge } from "~/components/ui/badge"
import { Button } from "~/components/ui/button"
import { Card } from "~/components/ui/card"
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
import { fichaApi } from "~/lib/api"

type Section = "equipes" | "produtos" | "servicos"

const SECTIONS: Record<Section, { title: string; list: () => Promise<any[]>; create: (b: any) => Promise<any>; del: (id: number) => Promise<any> }> = {
  equipes: { title: "Fichas de Equipe", list: fichaApi.listEquipes, create: fichaApi.createEquipe, del: fichaApi.deleteEquipe },
  produtos: { title: "Fichas de Produto", list: fichaApi.listProdutos, create: fichaApi.createProduto, del: fichaApi.deleteProduto },
  servicos: { title: "Fichas de Serviço", list: fichaApi.listServicos, create: fichaApi.createServico, del: fichaApi.deleteServico },
}

function detalhe(section: Section, f: any): string {
  if (section === "equipes") return `Produção: ${f.producao_diaria} ${f.unidade_producao}`
  if (section === "servicos") return `${f.tipo_servico} | Prod: ${f.producao_diaria} ${f.unidade_medida}`
  return `Und: ${f.unidade_medida}`
}

function NovaFichaModal({
  section,
  open,
  onOpenChange,
  onSaved,
}: {
  section: Section
  open: boolean
  onOpenChange: (v: boolean) => void
  onSaved: () => void
}) {
  const [v, setV] = useState<Record<string, string>>({})
  const [saving, setSaving] = useState(false)
  const titles: Record<Section, string> = { equipes: "Equipe", produtos: "Produto", servicos: "Serviço" }

  useEffect(() => {
    if (open) {
      const base: Record<string, string> = { codigo: "", nome: "", descricao: "" }
      if (section === "equipes") Object.assign(base, { producao_diaria: "1", unidade_producao: "dia" })
      if (section === "produtos") Object.assign(base, { unidade_medida: "un" })
      if (section === "servicos") Object.assign(base, { tipo_servico: "VERTICAL", unidade_medida: "m²", producao_diaria: "1" })
      setV(base)
    }
  }, [open, section])

  const set = (k: string, val: string) => setV((s) => ({ ...s, [k]: val }))

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    const payload: Record<string, unknown> = {}
    for (const [k, val] of Object.entries(v)) payload[k] = val === "" ? null : val
    try {
      await SECTIONS[section].create(payload)
      toast.success("Ficha criada com sucesso")
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
          <DialogTitle>Nova Ficha de {titles[section]}</DialogTitle>
        </DialogHeader>
        <form onSubmit={submit} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="flex flex-col gap-2">
            <Label>Código *</Label>
            <Input required placeholder="EQ-001" value={v.codigo ?? ""} onChange={(e) => set("codigo", e.target.value)} />
          </div>
          <div className="flex flex-col gap-2 sm:col-span-2">
            <Label>Nome *</Label>
            <Input required placeholder="Nome da ficha…" value={v.nome ?? ""} onChange={(e) => set("nome", e.target.value)} />
          </div>
          <div className="flex flex-col gap-2 sm:col-span-2">
            <Label>Descrição</Label>
            <Input placeholder="Opcional…" value={v.descricao ?? ""} onChange={(e) => set("descricao", e.target.value)} />
          </div>

          {section === "equipes" && (
            <>
              <div className="flex flex-col gap-2">
                <Label>Produção Diária *</Label>
                <Input type="number" required step="0.01" min="0" value={v.producao_diaria ?? ""} onChange={(e) => set("producao_diaria", e.target.value)} />
              </div>
              <div className="flex flex-col gap-2">
                <Label>Unidade de Produção *</Label>
                <Input required value={v.unidade_producao ?? ""} onChange={(e) => set("unidade_producao", e.target.value)} />
              </div>
            </>
          )}
          {section === "produtos" && (
            <div className="flex flex-col gap-2">
              <Label>Unidade de Medida *</Label>
              <Input required value={v.unidade_medida ?? ""} onChange={(e) => set("unidade_medida", e.target.value)} />
            </div>
          )}
          {section === "servicos" && (
            <>
              <div className="flex flex-col gap-2">
                <Label>Tipo de Serviço *</Label>
                <Select value={v.tipo_servico ?? ""} onValueChange={(val) => set("tipo_servico", val)}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {["VERTICAL", "HORIZONTAL", "SH", "OUTROS"].map((o) => (
                      <SelectItem key={o} value={o}>{o}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex flex-col gap-2">
                <Label>Unidade de Medida *</Label>
                <Input required value={v.unidade_medida ?? ""} onChange={(e) => set("unidade_medida", e.target.value)} />
              </div>
              <div className="flex flex-col gap-2">
                <Label>Produção Diária *</Label>
                <Input type="number" required step="0.01" min="0" value={v.producao_diaria ?? ""} onChange={(e) => set("producao_diaria", e.target.value)} />
              </div>
            </>
          )}

          <DialogFooter className="sm:col-span-2">
            <Button type="button" variant="secondary" onClick={() => onOpenChange(false)}>Cancelar</Button>
            <Button type="submit" disabled={saving}>{saving ? "Criando…" : "Criar Ficha"}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export default function Fichas() {
  const { tipo } = useParams()
  const section = (tipo as Section) ?? "equipes"
  const cfg = SECTIONS[section]
  const [rows, setRows] = useState<any[] | null>(null)
  const [erro, setErro] = useState("")
  const [busca, setBusca] = useState("")
  const [modalOpen, setModalOpen] = useState(false)

  async function refresh() {
    if (!cfg) return
    setRows(null)
    setErro("")
    try {
      setRows(await cfg.list())
    } catch (err: any) {
      setErro(err.message)
    }
  }

  useEffect(() => {
    refresh()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [section])

  const filtered = useMemo(() => {
    if (!rows) return []
    const q = busca.toLowerCase()
    if (!q) return rows
    return rows.filter((f) => `${f.codigo} ${f.nome}`.toLowerCase().includes(q))
  }, [rows, busca])

  if (!cfg) return <PageHeader title="Seção inválida" subtitle={tipo} />

  async function del(id: number) {
    if (!confirm("Excluir ficha e todos os seus itens?")) return
    try {
      await cfg.del(id)
      toast.success("Ficha excluída")
      refresh()
    } catch (err: any) {
      toast.error(`Erro: ${err.message}`)
    }
  }

  return (
    <>
      <PageHeader
        title={cfg.title}
        subtitle="Parametrização de fichas técnicas"
        actions={
          <>
            <div className="relative">
              <MagnifyingGlassIcon className="text-muted-foreground absolute top-1/2 left-2.5 size-4 -translate-y-1/2" />
              <Input className="w-48 pl-8" placeholder="Filtrar fichas…" value={busca} onChange={(e) => setBusca(e.target.value)} />
            </div>
            <Button size="sm" onClick={() => setModalOpen(true)}>
              <PlusIcon className="size-4" /> Nova Ficha
            </Button>
          </>
        }
      />

      <Card className="py-0">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Código</TableHead>
              <TableHead>Nome</TableHead>
              <TableHead>Detalhes</TableHead>
              <TableHead>Itens</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="w-10"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows === null ? (
              <TableRow><TableCell colSpan={6} className="text-muted-foreground py-8 text-center">Carregando…</TableCell></TableRow>
            ) : erro ? (
              <TableRow><TableCell colSpan={6} className="text-destructive py-8 text-center">Erro: {erro}</TableCell></TableRow>
            ) : filtered.length === 0 ? (
              <TableRow><TableCell colSpan={6} className="text-muted-foreground py-8 text-center">Nenhuma ficha cadastrada.</TableCell></TableRow>
            ) : (
              filtered.map((f) => {
                const flag = section === "servicos" ? f.possui_recursos : f.possui_itens
                const flagLabel = section === "servicos" ? "Recursos" : "Itens"
                return (
                  <TableRow key={f.id}>
                    <TableCell className="text-primary font-mono text-xs">{f.codigo}</TableCell>
                    <TableCell><strong>{f.nome}</strong></TableCell>
                    <TableCell className="text-muted-foreground text-xs">{detalhe(section, f)}</TableCell>
                    <TableCell>
                      {flag ? (
                        <Badge variant="success">{flagLabel} OK</Badge>
                      ) : (
                        <Badge variant="warning">Sem {flagLabel.toLowerCase()}</Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      {f.ativo ? <Badge variant="success">Ativa</Badge> : <Badge variant="secondary">Inativa</Badge>}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="icon" title="Excluir" onClick={() => del(f.id)}>
                        <TrashIcon className="text-destructive size-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                )
              })
            )}
          </TableBody>
        </Table>
      </Card>

      <NovaFichaModal section={section} open={modalOpen} onOpenChange={setModalOpen} onSaved={refresh} />
    </>
  )
}
