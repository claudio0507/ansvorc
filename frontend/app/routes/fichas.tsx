import { useEffect, useMemo, useState } from "react"
import { useParams } from "react-router"
import { toast } from "sonner"
import { MagnifyingGlassIcon, PlusIcon, TrashIcon, PencilSimpleIcon } from "@phosphor-icons/react"

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
import { bdApi, fichaApi } from "~/lib/api"
import { fmtBRL } from "~/lib/format"

type Section = "equipes" | "produtos" | "servicos"
const SEGUIMENTOS = ["EPS", "HORIZONTAL", "VERTICAL", "APOIO"]

const SECTIONS: Record<
  Section,
  { title: string; list: () => Promise<any[]>; create: (b: any) => Promise<any>; del: (id: number) => Promise<any> }
> = {
  equipes: { title: "Fichas de Equipe", list: fichaApi.listEquipes, create: fichaApi.createEquipe, del: fichaApi.deleteEquipe },
  produtos: { title: "Fichas de Produto", list: fichaApi.listProdutos, create: fichaApi.createProduto, del: fichaApi.deleteProduto },
  servicos: { title: "Fichas de Serviço", list: fichaApi.listServicos, create: fichaApi.createServico, del: fichaApi.deleteServico },
}

// ── Modal: criar cabeçalho da ficha ──────────────────────────────────────────

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
      if (section === "equipes") setV({ codigo: "", seguimento: "EPS" })
      else if (section === "produtos") setV({ codigo: "", nome: "", unidade: "und" })
      else setV({ codigo: "", nome: "", seguimento: "EPS", produtividade_dia: "1", unidade: "m²" })
    }
  }, [open, section])

  const set = (k: string, val: string) => setV((s) => ({ ...s, [k]: val }))

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    try {
      await SECTIONS[section].create(v)
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
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Nova Ficha de {titles[section]}</DialogTitle>
        </DialogHeader>
        <form onSubmit={submit} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="flex flex-col gap-2">
            <Label>Código *</Label>
            <Input required placeholder="EQ-001" value={v.codigo ?? ""} onChange={(e) => set("codigo", e.target.value)} />
          </div>
          {section !== "equipes" && (
            <div className="flex flex-col gap-2">
              <Label>Nome *</Label>
              <Input required value={v.nome ?? ""} onChange={(e) => set("nome", e.target.value)} />
            </div>
          )}
          {section !== "produtos" && (
            <div className="flex flex-col gap-2">
              <Label>Seguimento *</Label>
              <Select value={v.seguimento ?? ""} onValueChange={(val) => set("seguimento", val)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {SEGUIMENTOS.map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
          )}
          {section === "produtos" && (
            <div className="flex flex-col gap-2">
              <Label>Unidade *</Label>
              <Input required value={v.unidade ?? ""} onChange={(e) => set("unidade", e.target.value)} />
            </div>
          )}
          {section === "servicos" && (
            <>
              <div className="flex flex-col gap-2">
                <Label>Produtividade/dia *</Label>
                <Input type="number" required step="0.01" min="0.01" value={v.produtividade_dia ?? ""} onChange={(e) => set("produtividade_dia", e.target.value)} />
              </div>
              <div className="flex flex-col gap-2">
                <Label>Unidade *</Label>
                <Input required value={v.unidade ?? ""} onChange={(e) => set("unidade", e.target.value)} />
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

// ── Editor: itens da Ficha de Equipe ─────────────────────────────────────────

function EquipeEditor({ fichaId, onClose }: { fichaId: number; onClose: () => void }) {
  const [ficha, setFicha] = useState<any>(null)
  const [rhs, setRhs] = useState<any[]>([])
  const [epis, setEpis] = useState<any[]>([])
  const [rhId, setRhId] = useState("")
  const [epiId, setEpiId] = useState("__none__")
  const [qtd, setQtd] = useState("1")
  const [saving, setSaving] = useState(false)

  async function load() {
    const [f, r, e] = await Promise.all([
      fichaApi.getEquipe(fichaId),
      bdApi.listRH() as Promise<any[]>,
      bdApi.listEPI() as Promise<any[]>,
    ])
    setFicha(f)
    setRhs(r)
    setEpis(e)
  }
  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fichaId])

  async function addItem(e: React.FormEvent) {
    e.preventDefault()
    if (!rhId) return toast.error("Selecione um cargo")
    setSaving(true)
    try {
      await fichaApi.addItemEquipe(fichaId, {
        rh_id: Number(rhId),
        epi_id: epiId === "__none__" ? null : Number(epiId),
        quantidade: Number(qtd),
      })
      setRhId("")
      setEpiId("__none__")
      setQtd("1")
      await load()
    } catch (err: any) {
      toast.error(`Erro: ${err.message}`)
    } finally {
      setSaving(false)
    }
  }

  async function removeItem(id: number) {
    try {
      await fichaApi.removeItemEquipe(fichaId, id)
      await load()
    } catch (err: any) {
      toast.error(`Erro: ${err.message}`)
    }
  }

  const rhNome = (id: number) => rhs.find((r) => r.id === id)?.cargo ?? `#${id}`

  return (
    <Dialog open onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle>
            Editar Equipe {ficha?.codigo} <Badge variant="secondary">{ficha?.seguimento}</Badge>
          </DialogTitle>
        </DialogHeader>

        <form onSubmit={addItem} className="grid grid-cols-1 items-end gap-3 sm:grid-cols-4">
          <div className="flex flex-col gap-2">
            <Label>Cargo (bd_RH)</Label>
            <Select value={rhId} onValueChange={setRhId}>
              <SelectTrigger><SelectValue placeholder="Selecione…" /></SelectTrigger>
              <SelectContent>
                {rhs.map((r) => <SelectItem key={r.id} value={String(r.id)}>{r.cargo}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div className="flex flex-col gap-2">
            <Label>EPI (opcional)</Label>
            <Select value={epiId} onValueChange={setEpiId}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="__none__">—</SelectItem>
                {epis.map((e) => <SelectItem key={e.id} value={String(e.id)}>{e.item}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div className="flex flex-col gap-2">
            <Label>QTD (pessoas)</Label>
            <Input type="number" min="1" step="1" value={qtd} onChange={(e) => setQtd(e.target.value)} />
          </div>
          <Button type="submit" disabled={saving}>
            <PlusIcon className="size-4" /> Adicionar
          </Button>
        </form>

        <Card className="overflow-x-auto py-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Cargo</TableHead>
                <TableHead className="text-right">QTD</TableHead>
                <TableHead className="text-right">Custo MO</TableHead>
                <TableHead className="text-right">Custo EPI</TableHead>
                <TableHead className="text-right">Refeição</TableHead>
                <TableHead className="text-right">Hospedagem</TableHead>
                <TableHead className="text-right">Custo-Dia</TableHead>
                <TableHead className="w-10"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {!ficha?.itens?.length ? (
                <TableRow><TableCell colSpan={8} className="text-muted-foreground py-6 text-center">Nenhum item.</TableCell></TableRow>
              ) : (
                ficha.itens.map((it: any) => (
                  <TableRow key={it.id}>
                    <TableCell>{rhNome(it.rh_id)}</TableCell>
                    <TableCell className="text-right">{it.quantidade}</TableCell>
                    <TableCell className="text-right">{fmtBRL(it.custo_mo)}</TableCell>
                    <TableCell className="text-right">{fmtBRL(it.custo_epi)}</TableCell>
                    <TableCell className="text-right">{fmtBRL(it.refeicao)}</TableCell>
                    <TableCell className="text-right">{fmtBRL(it.hospedagem)}</TableCell>
                    <TableCell className="text-right font-semibold">{fmtBRL(it.custo_dia_linha)}</TableCell>
                    <TableCell>
                      <Button variant="ghost" size="icon" onClick={() => removeItem(it.id)}>
                        <TrashIcon className="text-destructive size-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </Card>

        <div className="flex items-center justify-end gap-2 border-t pt-3">
          <span className="text-muted-foreground text-sm">Custo-Dia Total</span>
          <span className="text-primary text-lg font-bold">{fmtBRL(ficha?.custo_dia_total)}</span>
        </div>
      </DialogContent>
    </Dialog>
  )
}

// ── Editor: BOM da Ficha de Produto ──────────────────────────────────────────

function ProdutoEditor({ fichaId, onClose }: { fichaId: number; onClose: () => void }) {
  const [ficha, setFicha] = useState<any>(null)
  const [materiais, setMateriais] = useState<any[]>([])
  const [produtos, setProdutos] = useState<any[]>([])
  const [tipo, setTipo] = useState<"material" | "produto">("material")
  const [refId, setRefId] = useState("")
  const [qtd, setQtd] = useState("1")
  const [saving, setSaving] = useState(false)

  async function load() {
    const [f, m, p] = await Promise.all([
      fichaApi.getProduto(fichaId),
      bdApi.listMat() as Promise<any[]>,
      fichaApi.listProdutos(),
    ])
    setFicha(f)
    setMateriais(m)
    setProdutos(p.filter((x) => x.id !== fichaId))
  }
  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fichaId])

  async function addItem(e: React.FormEvent) {
    e.preventDefault()
    if (!refId) return toast.error("Selecione um componente")
    setSaving(true)
    try {
      await fichaApi.addItemProduto(fichaId, {
        material_id: tipo === "material" ? Number(refId) : null,
        componente_filho_id: tipo === "produto" ? Number(refId) : null,
        quantidade: Number(qtd),
      })
      setRefId("")
      setQtd("1")
      await load()
    } catch (err: any) {
      toast.error(`Erro: ${err.message}`)
    } finally {
      setSaving(false)
    }
  }

  const lista = tipo === "material" ? materiais : produtos
  const nomeRef = (it: any) =>
    it.material_id
      ? materiais.find((m) => m.id === it.material_id)?.material ?? `Mat #${it.material_id}`
      : produtos.find((p) => p.id === it.componente_filho_id)?.nome ?? `Prod #${it.componente_filho_id}`

  return (
    <Dialog open onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle>Editar Produto {ficha?.codigo} — {ficha?.nome}</DialogTitle>
        </DialogHeader>

        <form onSubmit={addItem} className="grid grid-cols-1 items-end gap-3 sm:grid-cols-4">
          <div className="flex flex-col gap-2">
            <Label>Tipo</Label>
            <Select value={tipo} onValueChange={(v) => { setTipo(v as any); setRefId("") }}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="material">Material</SelectItem>
                <SelectItem value="produto">Sub-produto</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex flex-col gap-2">
            <Label>Componente</Label>
            <Select value={refId} onValueChange={setRefId}>
              <SelectTrigger><SelectValue placeholder="Selecione…" /></SelectTrigger>
              <SelectContent>
                {lista.map((x) => (
                  <SelectItem key={x.id} value={String(x.id)}>
                    {tipo === "material" ? x.material : `${x.codigo} — ${x.nome}`}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex flex-col gap-2">
            <Label>Quantidade</Label>
            <Input type="number" min="0.000001" step="0.01" value={qtd} onChange={(e) => setQtd(e.target.value)} />
          </div>
          <Button type="submit" disabled={saving}>
            <PlusIcon className="size-4" /> Adicionar
          </Button>
        </form>

        <Card className="overflow-x-auto py-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Componente</TableHead>
                <TableHead className="text-right">QTD</TableHead>
                <TableHead>Und</TableHead>
                <TableHead className="text-right">Custo Unit.</TableHead>
                <TableHead className="text-right">Custo Total</TableHead>
                <TableHead className="w-10"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {!ficha?.itens?.length ? (
                <TableRow><TableCell colSpan={6} className="text-muted-foreground py-6 text-center">Nenhum componente.</TableCell></TableRow>
              ) : (
                ficha.itens.map((it: any) => (
                  <TableRow key={it.id}>
                    <TableCell>
                      {nomeRef(it)}
                      {it.componente_filho_id && <Badge variant="secondary" className="ml-2">SUB</Badge>}
                    </TableCell>
                    <TableCell className="text-right">{it.quantidade}</TableCell>
                    <TableCell>{it.unidade}</TableCell>
                    <TableCell className="text-right">{fmtBRL(it.custo_unitario)}</TableCell>
                    <TableCell className="text-right font-semibold">{fmtBRL(it.custo_total_linha)}</TableCell>
                    <TableCell>
                      <Button variant="ghost" size="icon" onClick={async () => {
                        await fichaApi.removeItemProduto(fichaId, it.id)
                        await load()
                      }}>
                        <TrashIcon className="text-destructive size-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </Card>

        <div className="flex items-center justify-end gap-2 border-t pt-3">
          <span className="text-muted-foreground text-sm">Custo Total</span>
          <span className="text-primary text-lg font-bold">{fmtBRL(ficha?.custo_total)}</span>
        </div>
      </DialogContent>
    </Dialog>
  )
}

// ── Editor: recursos da Ficha de Serviço ─────────────────────────────────────

function ServicoEditor({ fichaId, onClose }: { fichaId: number; onClose: () => void }) {
  const [ficha, setFicha] = useState<any>(null)
  const [equipes, setEquipes] = useState<any[]>([])
  const [frotas, setFrotas] = useState<any[]>([])
  const [ferrs, setFerrs] = useState<any[]>([])
  const [produtos, setProdutos] = useState<any[]>([])
  const [eqId, setEqId] = useState("")
  const [frId, setFrId] = useState("")
  const [feId, setFeId] = useState("")
  const [prId, setPrId] = useState("__none__")
  const [saving, setSaving] = useState(false)

  async function load() {
    const f = await fichaApi.getServico(fichaId)
    const seg = f.seguimento
    const [eq, fr, fe, pr] = await Promise.all([
      fichaApi.listEquipes(seg),
      bdApi.listFrotas(seg),
      bdApi.listFerr(seg),
      fichaApi.listProdutos(),
    ])
    setFicha(f)
    setEquipes(eq)
    setFrotas(fr)
    setFerrs(fe)
    setProdutos(pr)
  }
  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fichaId])

  async function addRecurso(e: React.FormEvent) {
    e.preventDefault()
    if (!eqId || !frId || !feId) return toast.error("Equipe, frota e ferramental são obrigatórios")
    setSaving(true)
    try {
      await fichaApi.addRecurso(fichaId, {
        ficha_equipe_id: Number(eqId),
        frota_id: Number(frId),
        ferramental_id: Number(feId),
        ficha_produto_id: prId === "__none__" ? null : Number(prId),
      })
      setEqId("")
      setFrId("")
      setFeId("")
      setPrId("__none__")
      await load()
    } catch (err: any) {
      toast.error(`Erro: ${err.message}`)
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle>
            Editar Serviço {ficha?.codigo} <Badge variant="secondary">{ficha?.seguimento}</Badge>
            <span className="text-muted-foreground ml-2 text-sm font-normal">
              prod/dia: {ficha?.produtividade_dia} {ficha?.unidade}
            </span>
          </DialogTitle>
        </DialogHeader>

        <p className="text-muted-foreground text-xs">
          Recursos filtrados pelo seguimento da ficha. Equipe + Frota + Ferramental são obrigatórios; produto é opcional.
        </p>

        <form onSubmit={addRecurso} className="grid grid-cols-1 items-end gap-3 sm:grid-cols-5">
          <div className="flex flex-col gap-2">
            <Label>Equipe</Label>
            <Select value={eqId} onValueChange={setEqId}>
              <SelectTrigger><SelectValue placeholder="…" /></SelectTrigger>
              <SelectContent>
                {equipes.map((x) => <SelectItem key={x.id} value={String(x.id)}>{x.codigo}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div className="flex flex-col gap-2">
            <Label>Frota</Label>
            <Select value={frId} onValueChange={setFrId}>
              <SelectTrigger><SelectValue placeholder="…" /></SelectTrigger>
              <SelectContent>
                {frotas.map((x) => <SelectItem key={x.id} value={String(x.id)}>{x.seguimento} ({fmtBRL(x.custo_diario)})</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div className="flex flex-col gap-2">
            <Label>Ferramental</Label>
            <Select value={feId} onValueChange={setFeId}>
              <SelectTrigger><SelectValue placeholder="…" /></SelectTrigger>
              <SelectContent>
                {ferrs.map((x) => <SelectItem key={x.id} value={String(x.id)}>{x.seguimento} ({fmtBRL(x.custo_diario)})</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div className="flex flex-col gap-2">
            <Label>Produto (opc)</Label>
            <Select value={prId} onValueChange={setPrId}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="__none__">—</SelectItem>
                {produtos.map((x) => <SelectItem key={x.id} value={String(x.id)}>{x.nome}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <Button type="submit" disabled={saving}>
            <PlusIcon className="size-4" /> Vincular
          </Button>
        </form>

        <Card className="overflow-x-auto py-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Equipe</TableHead>
                <TableHead>Frota</TableHead>
                <TableHead>Ferramental</TableHead>
                <TableHead>Produto</TableHead>
                <TableHead className="w-10"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {!ficha?.recursos?.length ? (
                <TableRow><TableCell colSpan={5} className="text-muted-foreground py-6 text-center">Nenhum recurso vinculado.</TableCell></TableRow>
              ) : (
                ficha.recursos.map((r: any) => (
                  <TableRow key={r.id}>
                    <TableCell>{equipes.find((e) => e.id === r.ficha_equipe_id)?.codigo ?? `#${r.ficha_equipe_id}`}</TableCell>
                    <TableCell>{frotas.find((f) => f.id === r.frota_id)?.seguimento ?? `#${r.frota_id}`}</TableCell>
                    <TableCell>{ferrs.find((f) => f.id === r.ferramental_id)?.seguimento ?? `#${r.ferramental_id}`}</TableCell>
                    <TableCell>{r.ficha_produto_id ? (produtos.find((p) => p.id === r.ficha_produto_id)?.nome ?? `#${r.ficha_produto_id}`) : "—"}</TableCell>
                    <TableCell>
                      <Button variant="ghost" size="icon" onClick={async () => { await fichaApi.removeRecurso(fichaId, r.id); await load() }}>
                        <TrashIcon className="text-destructive size-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </Card>

        <div className="flex items-center justify-end gap-2 border-t pt-3">
          <span className="text-muted-foreground text-sm">Custo Unitário ({ficha?.unidade})</span>
          <span className="text-primary text-lg font-bold">{fmtBRL(ficha?.custo_unitario)}</span>
        </div>
      </DialogContent>
    </Dialog>
  )
}

// ── Página ───────────────────────────────────────────────────────────────────

export default function Fichas() {
  const { tipo } = useParams()
  const section = (tipo as Section) ?? "equipes"
  const cfg = SECTIONS[section]
  const [rows, setRows] = useState<any[] | null>(null)
  const [erro, setErro] = useState("")
  const [busca, setBusca] = useState("")
  const [modalOpen, setModalOpen] = useState(false)
  const [editId, setEditId] = useState<number | null>(null)

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
    return rows.filter((f) => `${f.codigo} ${f.nome ?? ""}`.toLowerCase().includes(q))
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

  const custoLabel = section === "equipes" ? "Custo-Dia" : section === "produtos" ? "Custo Total" : "Custo Unit."
  const custoVal = (f: any) =>
    section === "equipes" ? f.custo_dia_total : section === "produtos" ? f.custo_total : f.custo_unitario

  return (
    <>
      <PageHeader
        title={cfg.title}
        subtitle="Parametrização de fichas técnicas — custos calculados automaticamente"
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

      <Card className="overflow-x-auto py-0">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Código</TableHead>
              {section !== "equipes" && <TableHead>Nome</TableHead>}
              {section !== "produtos" && <TableHead>Seguimento</TableHead>}
              <TableHead className="text-right">{custoLabel}</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="w-24"></TableHead>
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
              filtered.map((f) => (
                <TableRow key={f.id}>
                  <TableCell className="text-primary font-mono text-xs">{f.codigo}</TableCell>
                  {section !== "equipes" && <TableCell><strong>{f.nome}</strong></TableCell>}
                  {section !== "produtos" && <TableCell><Badge variant="secondary">{f.seguimento}</Badge></TableCell>}
                  <TableCell className="text-right font-semibold">{fmtBRL(custoVal(f))}</TableCell>
                  <TableCell>
                    {f.ativo ? <Badge variant="success">ATIVA</Badge> : <Badge variant="secondary">INATIVA</Badge>}
                  </TableCell>
                  <TableCell>
                    <div className="flex justify-end gap-1">
                      <Button variant="ghost" size="icon" title="Editar itens" onClick={() => setEditId(f.id)}>
                        <PencilSimpleIcon className="size-4" />
                      </Button>
                      <Button variant="ghost" size="icon" title="Excluir" onClick={() => del(f.id)}>
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

      <NovaFichaModal section={section} open={modalOpen} onOpenChange={setModalOpen} onSaved={refresh} />

      {editId !== null && section === "equipes" && (
        <EquipeEditor fichaId={editId} onClose={() => { setEditId(null); refresh() }} />
      )}
      {editId !== null && section === "produtos" && (
        <ProdutoEditor fichaId={editId} onClose={() => { setEditId(null); refresh() }} />
      )}
      {editId !== null && section === "servicos" && (
        <ServicoEditor fichaId={editId} onClose={() => { setEditId(null); refresh() }} />
      )}
    </>
  )
}
