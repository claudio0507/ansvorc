import { useEffect, useMemo, useState } from "react"
import { useParams } from "react-router"
import { toast } from "sonner"
import { MagnifyingGlassIcon, PencilSimpleIcon, PlusIcon, TrashIcon } from "@phosphor-icons/react"

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
import { bdApi } from "~/lib/api"
import { fmtBRL, fmtData } from "~/lib/format"

const SEGUIMENTOS = ["EPS", "HORIZONTAL", "VERTICAL", "APOIO"]
const UFS = ["PR", "SP", "SC", "RS", "MG", "RJ", "GO", "DF", "BA", "PE", "CE"]
const MODALIDADES = ["BDI-MAT+MO", "BDI-MO", "BDI+ICMS", "FAT DIR SIMP"]
const SEG_FERR = ["EPS", "HORIZONTAL", "VERTICAL", "OBRA CIVIL"]
const SEG_FROTA = ["APOIO", "EPS", "HORIZONTAL", "VERTICAL"]
const TIPOS_EST = ["Base_de_Apoio", "Moradia", "Administrativo", "Operacional", "Logística"]

type FieldType = "text" | "number" | "select"
interface Field {
  name: string
  label: string
  type: FieldType
  required?: boolean
  placeholder?: string
  options?: string[]
  step?: string
  value?: string
}
interface BdConfig {
  title: string
  subtitle: string
  cols: string[]
  row: (r: any) => React.ReactNode[]
  list: (filtro?: string) => Promise<any[]>
  delete: (id: number) => Promise<any>
  create: (d: any) => Promise<any>
  update: (id: number, d: any) => Promise<any>
  formFields: Field[]
  filter?: { kind: "uf" | "seguimento"; options: string[] }
}

const num = (v: any) => parseFloat(v) || 0
const brl = (v: any) => fmtBRL(num(v))
const pct = (v: any) => `${(num(v) * 100).toFixed(2)}%`
const seg = (s: string) => <Badge variant="secondary">{String(s).toUpperCase()}</Badge>
const ativoBadge = (a: boolean) =>
  a ? <Badge variant="success">ATIVO</Badge> : <Badge variant="secondary">INATIVO</Badge>

const BD_CONFIG: Record<string, BdConfig> = {
  bdi: {
    title: "Parâmetros de BDI",
    subtitle: "Alíquotas tributárias por modalidade e UF",
    cols: [
      "Modalidade",
      "UF",
      "ICMS",
      "COFINS",
      "PIS",
      "ISSQN",
      "Cst Finan",
      "IRPJ",
      "CSLL",
      "Desp Adm",
    ],
    row: (r) => [
      <span className="font-medium">{r.modalidade}</span>,
      seg(r.uf),
      pct(r.icms),
      pct(r.cofins),
      pct(r.pis),
      pct(r.issqn),
      pct(r.custo_financeiro),
      pct(r.irpj),
      pct(r.csll),
      pct(r.despesas_adm),
    ],
    list: (uf) => bdApi.listBDI(uf),
    delete: (id) => bdApi.deleteBDI(id),
    create: (d) => bdApi.createBDI(d),
    update: (id, d) => bdApi.updateBDI(id, d),
    filter: { kind: "uf", options: UFS },
    formFields: [
      { name: "modalidade", label: "Modalidade", type: "select", required: true, options: MODALIDADES },
      { name: "uf", label: "UF", type: "select", required: true, options: UFS },
      { name: "icms", label: "ICMS (decimal)", type: "number", step: "0.0001", value: "0" },
      { name: "cofins", label: "COFINS (decimal)", type: "number", step: "0.0001", value: "0.03" },
      { name: "pis", label: "PIS (decimal)", type: "number", step: "0.0001", value: "0.0065" },
      { name: "issqn", label: "ISSQN (decimal)", type: "number", step: "0.0001", value: "0.035" },
      { name: "custo_financeiro", label: "Custo Financeiro", type: "number", step: "0.0001", value: "0.015" },
      { name: "irpj", label: "IRPJ (decimal)", type: "number", step: "0.0001", value: "0.02" },
      { name: "csll", label: "CSLL (decimal)", type: "number", step: "0.0001", value: "0.0108" },
      { name: "despesas_adm", label: "Despesas Adm", type: "number", step: "0.0001", value: "0.13" },
    ],
  },
  rh: {
    title: "Recursos Humanos",
    subtitle: "Cargos e custo diário de mão de obra",
    cols: ["Cargo", "Custo Diário", "Status"],
    row: (r) => [<strong>{r.cargo}</strong>, brl(r.custo_diario), ativoBadge(r.ativo)],
    list: () => bdApi.listRH() as Promise<any[]>,
    delete: (id) => bdApi.deleteRH(id),
    create: (d) => bdApi.createRH(d),
    update: (id, d) => bdApi.updateRH(id, d),
    formFields: [
      { name: "cargo", label: "Cargo", type: "text", required: true, placeholder: "Encarregado" },
      { name: "custo_diario", label: "Custo Diário (R$)", type: "number", required: true, step: "0.01" },
    ],
  },
  epi: {
    title: "EPIs",
    subtitle: "Equipamentos de proteção individual (custo diário)",
    cols: ["Item", "Custo Diário", "Status"],
    row: (r) => [<strong>{r.item}</strong>, brl(r.custo_diario), ativoBadge(r.ativo)],
    list: () => bdApi.listEPI() as Promise<any[]>,
    delete: (id) => bdApi.deleteEPI(id),
    create: (d) => bdApi.createEPI(d),
    update: (id, d) => bdApi.updateEPI(id, d),
    formFields: [
      { name: "item", label: "Item", type: "text", required: true, placeholder: "Kit EPI Encarregado" },
      { name: "custo_diario", label: "Custo Diário (R$)", type: "number", required: true, step: "0.01" },
    ],
  },
  ferramental: {
    title: "Ferramental",
    subtitle: "Ferramentas por seguimento",
    cols: ["Seguimento", "Custo Diário", "Status"],
    row: (r) => [seg(r.seguimento), brl(r.custo_diario), ativoBadge(r.ativo)],
    list: (s) => bdApi.listFerr(s),
    delete: (id) => bdApi.deleteFerr(id),
    create: (d) => bdApi.createFerr(d),
    update: (id, d) => bdApi.updateFerr(id, d),
    filter: { kind: "seguimento", options: SEG_FERR },
    formFields: [
      { name: "seguimento", label: "Seguimento", type: "select", required: true, options: SEG_FERR },
      { name: "custo_diario", label: "Custo Diário (R$)", type: "number", required: true, step: "0.01" },
    ],
  },
  frotas: {
    title: "Frotas",
    subtitle: "Veículos e equipamentos por seguimento",
    cols: ["Seguimento", "Custo Diário", "Status"],
    row: (r) => [seg(r.seguimento), brl(r.custo_diario), ativoBadge(r.ativo)],
    list: (s) => bdApi.listFrotas(s),
    delete: (id) => bdApi.deleteFrota(id),
    create: (d) => bdApi.createFrota(d),
    update: (id, d) => bdApi.updateFrota(id, d),
    filter: { kind: "seguimento", options: SEG_FROTA },
    formFields: [
      { name: "seguimento", label: "Seguimento", type: "select", required: true, options: SEG_FROTA },
      { name: "custo_diario", label: "Custo Diário (R$)", type: "number", required: true, step: "0.01" },
    ],
  },
  materiais: {
    title: "Materiais",
    subtitle: "Materiais e insumos físicos",
    cols: ["Material", "Und", "Destinação", "Valor Unit.", "Status"],
    row: (r) => [
      <strong>{r.material}</strong>,
      r.unidade,
      r.destinacao ? seg(r.destinacao) : "—",
      brl(r.valor_unitario),
      ativoBadge(r.ativo),
    ],
    list: () => bdApi.listMat() as Promise<any[]>,
    delete: (id) => bdApi.deleteMat(id),
    create: (d) => bdApi.createMat(d),
    update: (id, d) => bdApi.updateMat(id, d),
    formFields: [
      { name: "material", label: "Material", type: "text", required: true, placeholder: "Chapa de Aço 1,00" },
      { name: "unidade", label: "Unidade", type: "text", required: true, placeholder: "und, kg, L…" },
      { name: "destinacao", label: "Destinação (opcional)", type: "text", placeholder: "FABRICA, HORIZONTAL" },
      { name: "valor_unitario", label: "Valor Unit. (R$)", type: "number", required: true, step: "0.0001" },
    ],
  },
  estrutura: {
    title: "Estrutura Operacional",
    subtitle: "Custos operacionais (BDI Sombra)",
    cols: ["Item", "Und", "Tipo", "Valor Unit.", "Status"],
    row: (r) => [
      <strong>{r.item}</strong>,
      r.unidade,
      seg(r.tipo),
      brl(r.valor_unitario),
      ativoBadge(r.ativo),
    ],
    list: () => bdApi.listEst() as Promise<any[]>,
    delete: (id) => bdApi.deleteEst(id),
    create: (d) => bdApi.createEst(d),
    update: (id, d) => bdApi.updateEst(id, d),
    formFields: [
      { name: "item", label: "Item", type: "text", required: true },
      { name: "unidade", label: "Unidade", type: "text", required: true },
      { name: "tipo", label: "Tipo", type: "select", required: true, options: TIPOS_EST },
      { name: "valor_unitario", label: "Valor Unit. (R$)", type: "number", required: true, step: "0.0001" },
    ],
  },
  despesas: {
    title: "Despesas",
    subtitle: "EPC, refeição e hospedagem por seguimento",
    cols: ["Seguimento", "EPC", "Refeição", "Hospedagem", "Status"],
    row: (r) => [
      seg(r.seguimento),
      brl(r.epc),
      brl(r.refeicao),
      brl(r.hospedagem),
      ativoBadge(r.ativo),
    ],
    list: (s) => bdApi.listDesp(s),
    delete: (id) => bdApi.deleteDesp(id),
    create: (d) => bdApi.createDesp(d),
    update: (id, d) => bdApi.updateDesp(id, d),
    filter: { kind: "seguimento", options: SEGUIMENTOS },
    formFields: [
      { name: "seguimento", label: "Seguimento", type: "select", required: true, options: SEGUIMENTOS },
      { name: "epc", label: "EPC (R$)", type: "number", step: "0.01", value: "0" },
      { name: "refeicao", label: "Refeição (R$)", type: "number", step: "0.01", value: "0" },
      { name: "hospedagem", label: "Hospedagem (R$)", type: "number", step: "0.01", value: "0" },
    ],
  },
}

function NovoModal({
  cfg,
  editItem,
  open,
  onOpenChange,
  onSaved,
}: {
  cfg: BdConfig
  editItem?: any
  open: boolean
  onOpenChange: (v: boolean) => void
  onSaved: () => void
}) {
  const [values, setValues] = useState<Record<string, string>>({})
  const [saving, setSaving] = useState(false)
  const isEdit = !!editItem

  useEffect(() => {
    if (open) {
      const init: Record<string, string> = {}
      cfg.formFields.forEach((f) => {
        if (editItem && editItem[f.name] !== undefined) {
          init[f.name] = String(editItem[f.name] ?? "")
        } else {
          init[f.name] = f.value ?? (f.type === "select" ? f.options![0] : "")
        }
      })
      setValues(init)
    }
  }, [open, cfg, editItem])

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    const payload: Record<string, unknown> = {}
    for (const [k, v] of Object.entries(values)) payload[k] = v === "" ? null : v
    try {
      if (isEdit) {
        await cfg.update(editItem.id, payload)
        toast.success("Registro atualizado com sucesso")
      } else {
        await cfg.create(payload)
        toast.success("Registro salvo com sucesso")
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
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>{isEdit ? "Editar" : "Novo"} — {cfg.title}</DialogTitle>
        </DialogHeader>
        <form onSubmit={submit} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {cfg.formFields.map((f) => (
            <div key={f.name} className="flex flex-col gap-2">
              <Label>
                {f.label}
                {f.required && " *"}
              </Label>
              {f.type === "select" ? (
                <Select
                  value={values[f.name] ?? ""}
                  onValueChange={(v) => setValues((s) => ({ ...s, [f.name]: v }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {f.options!.map((o) => (
                      <SelectItem key={o} value={o}>
                        {o}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              ) : (
                <Input
                  type={f.type}
                  required={f.required}
                  placeholder={f.placeholder}
                  step={f.step}
                  value={values[f.name] ?? ""}
                  onChange={(e) => setValues((s) => ({ ...s, [f.name]: e.target.value }))}
                />
              )}
            </div>
          ))}
          <DialogFooter className="sm:col-span-2">
            <Button type="button" variant="secondary" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={saving}>
              {saving ? "Salvando…" : isEdit ? "Atualizar" : "Criar"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export default function Bds() {
  const { tipo = "rh" } = useParams()
  const cfg = BD_CONFIG[tipo]
  const [rows, setRows] = useState<any[] | null>(null)
  const [erro, setErro] = useState("")
  const [busca, setBusca] = useState("")
  const [filtroValor, setFiltroValor] = useState<string>("__all__")
  const [modalOpen, setModalOpen] = useState(false)
  const [editItem, setEditItem] = useState<any>(null)

  async function refresh() {
    if (!cfg) return
    setRows(null)
    setErro("")
    try {
      const f = filtroValor === "__all__" ? undefined : filtroValor
      setRows(await cfg.list(f))
    } catch (err: any) {
      setErro(err.message)
    }
  }

  useEffect(() => {
    setFiltroValor("__all__")
    setBusca("")
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tipo])

  useEffect(() => {
    refresh()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tipo, filtroValor])

  const filtered = useMemo(() => {
    if (!rows) return []
    const q = busca.toLowerCase()
    if (!q) return rows
    return rows.filter((r) =>
      Object.values(r).some((v) => String(v ?? "").toLowerCase().includes(q))
    )
  }, [rows, busca])

  if (!cfg) return <PageHeader title="Módulo não encontrado" subtitle={tipo} />

  async function del(id: number) {
    if (!confirm("Excluir este registro?")) return
    try {
      await cfg.delete(id)
      toast.success("Registro excluído")
      refresh()
    } catch (err: any) {
      toast.error(`Erro: ${err.message}`)
    }
  }

  return (
    <>
      <PageHeader
        title={cfg.title}
        subtitle={cfg.subtitle}
        actions={
          <>
            {cfg.filter && (
              <Select value={filtroValor} onValueChange={setFiltroValor}>
                <SelectTrigger className="w-40">
                  <SelectValue
                    placeholder={cfg.filter.kind === "uf" ? "Todas as UF" : "Todos seguimentos"}
                  />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="__all__">
                    {cfg.filter.kind === "uf" ? "Todas as UF" : "Todos seguimentos"}
                  </SelectItem>
                  {cfg.filter.options.map((o) => (
                    <SelectItem key={o} value={o}>
                      {o}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
            <div className="relative">
              <MagnifyingGlassIcon className="text-muted-foreground absolute top-1/2 left-2.5 size-4 -translate-y-1/2" />
              <Input
                className="w-44 pl-8"
                placeholder="Filtrar…"
                value={busca}
                onChange={(e) => setBusca(e.target.value)}
              />
            </div>
            <Button size="sm" onClick={() => { setEditItem(null); setModalOpen(true) }}>
              <PlusIcon className="size-4" /> Novo
            </Button>
          </>
        }
      />

      <Card className="overflow-x-auto py-0">
        <Table>
          <TableHeader>
            <TableRow>
              {cfg.cols.map((c) => (
                <TableHead key={c}>{c}</TableHead>
              ))}
              <TableHead>Atualizado</TableHead>
              <TableHead className="w-10"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows === null ? (
              <TableRow>
                <TableCell colSpan={cfg.cols.length + 2} className="text-muted-foreground py-8 text-center">
                  Carregando…
                </TableCell>
              </TableRow>
            ) : erro ? (
              <TableRow>
                <TableCell colSpan={cfg.cols.length + 2} className="text-destructive py-8 text-center">
                  Erro: {erro}
                </TableCell>
              </TableRow>
            ) : filtered.length === 0 ? (
              <TableRow>
                <TableCell colSpan={cfg.cols.length + 2} className="text-muted-foreground py-8 text-center">
                  Nenhum registro encontrado.
                </TableCell>
              </TableRow>
            ) : (
              filtered.map((r) => (
                <TableRow key={r.id}>
                  {cfg.row(r).map((cell, i) => (
                    <TableCell key={i}>{cell}</TableCell>
                  ))}
                  <TableCell className="text-muted-foreground text-xs">
                    {r.atualizado_em ? fmtData(r.atualizado_em) : "—"}
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="ghost"
                      size="icon"
                      title="Editar"
                      onClick={() => { setEditItem(r); setModalOpen(true) }}
                    >
                      <PencilSimpleIcon className="text-muted-foreground size-4" />
                    </Button>
                    <Button variant="ghost" size="icon" title="Excluir" onClick={() => del(r.id)}>
                      <TrashIcon className="text-destructive size-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </Card>

      <NovoModal cfg={cfg} editItem={editItem} open={modalOpen} onOpenChange={setModalOpen} onSaved={refresh} />
    </>
  )
}
