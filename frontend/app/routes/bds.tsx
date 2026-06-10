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
import { bdApi } from "~/lib/api"
import { fmtBRL } from "~/lib/format"

type FieldType = "text" | "number" | "select"
interface Field {
  name: string
  label: string
  type: FieldType
  required?: boolean
  placeholder?: string
  options?: string[]
  step?: string
  min?: string
  value?: string
}

interface BdConfig {
  title: string
  cols: string[]
  row: (r: any) => React.ReactNode[]
  list: () => Promise<any>
  delete: (id: number) => Promise<any>
  create: (d: any) => Promise<any>
  formFields: Field[]
}

const num = (v: any) => parseFloat(v) || 0
const brl = (v: any) => fmtBRL(num(v))
const ativoBadge = (ativo: boolean) =>
  ativo ? <Badge variant="success">Ativo</Badge> : <Badge variant="secondary">Inativo</Badge>
const cat = (text: string) => <Badge variant="secondary">{text}</Badge>

const BD_CONFIG: Record<string, BdConfig> = {
  rh: {
    title: "Recursos Humanos",
    cols: ["Código", "Cargo", "Categoria", "Salário Base", "Custo/hora", "Status"],
    row: (r) => {
      const custoHora = ((num(r.salario_base) * (1 + num(r.encargos_percentual))) / num(r.horas_mes)).toFixed(2)
      return [r.codigo, <strong>{r.cargo}</strong>, cat(r.categoria), brl(r.salario_base), `R$ ${custoHora}`, ativoBadge(r.ativo)]
    },
    list: () => bdApi.listRH(),
    delete: (id) => bdApi.deleteRH(id),
    create: (d) => bdApi.createRH(d),
    formFields: [
      { name: "codigo", label: "Código", type: "text", required: true, placeholder: "RH-001" },
      { name: "cargo", label: "Cargo", type: "text", required: true, placeholder: "Encarregado Geral" },
      { name: "categoria", label: "Categoria", type: "select", required: true, options: ["OPERACIONAL", "TECNICO", "ADMINISTRATIVO"] },
      { name: "salario_base", label: "Salário Base (R$)", type: "number", required: true, step: "0.01", min: "0" },
      { name: "encargos_percentual", label: "Encargos (decimal)", type: "number", required: true, step: "0.0001", value: "0.72" },
      { name: "horas_mes", label: "Horas/Mês", type: "number", required: true, step: "0.01", value: "220" },
    ],
  },
  epi: {
    title: "EPIs",
    cols: ["Código", "Descrição", "Und", "Custo Unit.", "Vida Útil", "Status"],
    row: (r) => [r.codigo, r.descricao, r.unidade_medida, brl(r.custo_unitario), r.vida_util_dias ? `${r.vida_util_dias} dias` : "—", ativoBadge(r.ativo)],
    list: () => bdApi.listEPI(),
    delete: (id) => bdApi.deleteEPI(id),
    create: (d) => bdApi.createEPI(d),
    formFields: [
      { name: "codigo", label: "Código", type: "text", required: true },
      { name: "descricao", label: "Descrição", type: "text", required: true },
      { name: "unidade_medida", label: "Unidade", type: "text", required: true, placeholder: "un, par…" },
      { name: "custo_unitario", label: "Custo Unit. (R$)", type: "number", required: true, step: "0.01", min: "0" },
      { name: "vida_util_dias", label: "Vida Útil (dias)", type: "number", step: "1", min: "1" },
    ],
  },
  frotas: {
    title: "Frotas",
    cols: ["Código", "Descrição", "Tipo", "Diária", "R$/km", "Status"],
    row: (r) => [r.codigo, r.descricao, cat(r.tipo), brl(r.custo_diaria), r.custo_km ? `R$ ${num(r.custo_km).toFixed(2)}` : "—", ativoBadge(r.ativo)],
    list: () => bdApi.listFrotas(),
    delete: (id) => bdApi.deleteFrota(id),
    create: (d) => bdApi.createFrota(d),
    formFields: [
      { name: "codigo", label: "Código", type: "text", required: true },
      { name: "descricao", label: "Descrição", type: "text", required: true },
      { name: "tipo", label: "Tipo", type: "select", required: true, options: ["VEICULO_LEVE", "VEICULO_PESADO", "EQUIPAMENTO", "PRANCHA"] },
      { name: "custo_diaria", label: "Diária (R$)", type: "number", required: true, step: "0.01", min: "0" },
      { name: "custo_km", label: "R$/km (opcional)", type: "number", step: "0.01", min: "0" },
    ],
  },
  materiais: {
    title: "Materiais",
    cols: ["Código", "Descrição", "Categoria", "Und", "Custo Unit.", "ICMS", "Status"],
    row: (r) => [
      r.codigo, r.descricao, cat(r.categoria), r.unidade_medida, brl(r.custo_unitario),
      r.icms_incide ? <Badge variant="warning">Sim</Badge> : <Badge variant="secondary">Não</Badge>,
      ativoBadge(r.ativo),
    ],
    list: () => bdApi.listMat(),
    delete: (id) => bdApi.deleteMat(id),
    create: (d) => bdApi.createMat(d),
    formFields: [
      { name: "codigo", label: "Código", type: "text", required: true },
      { name: "descricao", label: "Descrição", type: "text", required: true },
      { name: "categoria", label: "Categoria", type: "select", required: true, options: ["PLACA", "PELICULA", "TINTA", "PERFIL", "PARAFUSO", "OUTROS"] },
      { name: "unidade_medida", label: "Unidade", type: "text", required: true },
      { name: "custo_unitario", label: "Custo Unit. (R$)", type: "number", required: true, step: "0.01", min: "0" },
      { name: "fornecedor", label: "Fornecedor (opcional)", type: "text" },
    ],
  },
  estrutura: {
    title: "Estrutura Operacional",
    cols: ["Código", "Descrição", "Tipo", "Und", "Custo Unit.", "Status"],
    row: (r) => [r.codigo, r.descricao, cat(r.tipo), r.unidade_medida, brl(r.custo_unitario), ativoBadge(r.ativo)],
    list: () => bdApi.listEst(),
    delete: (id) => bdApi.deleteEst(id),
    create: (d) => bdApi.createEst(d),
    formFields: [
      { name: "codigo", label: "Código", type: "text", required: true },
      { name: "descricao", label: "Descrição", type: "text", required: true },
      { name: "tipo", label: "Tipo", type: "select", required: true, options: ["ALOJAMENTO", "LOGISTICA", "MOBILIZACAO", "COMUNICACAO", "OUTROS"] },
      { name: "unidade_medida", label: "Unidade", type: "text", required: true },
      { name: "custo_unitario", label: "Custo Unit. (R$)", type: "number", required: true, step: "0.01", min: "0" },
    ],
  },
  despesas: {
    title: "Despesas",
    cols: ["Código", "Descrição", "Tipo", "Percentual", "Valor Fixo", "Status"],
    row: (r) => [
      r.codigo, r.descricao, cat(r.tipo),
      r.percentual ? `${(num(r.percentual) * 100).toFixed(2)}%` : "—",
      r.valor_fixo ? brl(r.valor_fixo) : "—",
      ativoBadge(r.ativo),
    ],
    list: () => bdApi.listDesp(),
    delete: (id) => bdApi.deleteDesp(id),
    create: (d) => bdApi.createDesp(d),
    formFields: [
      { name: "codigo", label: "Código", type: "text", required: true },
      { name: "descricao", label: "Descrição", type: "text", required: true },
      { name: "tipo", label: "Tipo", type: "select", required: true, options: ["ADMINISTRATIVA", "FINANCEIRA", "SEGURO", "OUTROS"] },
      { name: "percentual", label: "Percentual (decimal, ex: 0.13)", type: "number", step: "0.0001" },
      { name: "valor_fixo", label: "Valor Fixo (R$, ex: 1500)", type: "number", step: "0.01" },
    ],
  },
}

function NovoModal({
  cfg,
  open,
  onOpenChange,
  onSaved,
}: {
  cfg: BdConfig
  open: boolean
  onOpenChange: (v: boolean) => void
  onSaved: () => void
}) {
  const [values, setValues] = useState<Record<string, string>>({})
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (open) {
      const init: Record<string, string> = {}
      cfg.formFields.forEach((f) => (init[f.name] = f.value ?? (f.type === "select" ? f.options![0] : "")))
      setValues(init)
    }
  }, [open, cfg])

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    const payload: Record<string, unknown> = {}
    for (const [k, v] of Object.entries(values)) payload[k] = v === "" ? null : v
    try {
      await cfg.create(payload)
      toast.success("Registro salvo com sucesso")
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
          <DialogTitle>Novo — {cfg.title}</DialogTitle>
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
                  min={f.min}
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
              {saving ? "Salvando…" : "Criar"}
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
  }, [tipo])

  const filtered = useMemo(() => {
    if (!rows) return []
    const q = busca.toLowerCase()
    if (!q) return rows
    return rows.filter((r) =>
      Object.values(r).some((v) => String(v ?? "").toLowerCase().includes(q))
    )
  }, [rows, busca])

  if (!cfg) {
    return <PageHeader title="Módulo não encontrado" subtitle={tipo} />
  }

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
        subtitle="Cadastro e atualização de insumos"
        actions={
          <>
            <div className="relative">
              <MagnifyingGlassIcon className="text-muted-foreground absolute top-1/2 left-2.5 size-4 -translate-y-1/2" />
              <Input
                className="w-48 pl-8"
                placeholder="Filtrar…"
                value={busca}
                onChange={(e) => setBusca(e.target.value)}
              />
            </div>
            <Button size="sm" onClick={() => setModalOpen(true)}>
              <PlusIcon className="size-4" /> Novo
            </Button>
          </>
        }
      />

      <Card className="py-0">
        <Table>
          <TableHeader>
            <TableRow>
              {cfg.cols.map((c) => (
                <TableHead key={c}>{c}</TableHead>
              ))}
              <TableHead className="w-10"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows === null ? (
              <TableRow>
                <TableCell colSpan={cfg.cols.length + 1} className="text-muted-foreground py-8 text-center">
                  Carregando…
                </TableCell>
              </TableRow>
            ) : erro ? (
              <TableRow>
                <TableCell colSpan={cfg.cols.length + 1} className="text-destructive py-8 text-center">
                  Erro: {erro}
                </TableCell>
              </TableRow>
            ) : filtered.length === 0 ? (
              <TableRow>
                <TableCell colSpan={cfg.cols.length + 1} className="text-muted-foreground py-8 text-center">
                  Nenhum registro encontrado.
                </TableCell>
              </TableRow>
            ) : (
              filtered.map((r) => (
                <TableRow key={r.id}>
                  {cfg.row(r).map((cell, i) => (
                    <TableCell key={i}>{cell}</TableCell>
                  ))}
                  <TableCell className="text-right">
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

      <NovoModal cfg={cfg} open={modalOpen} onOpenChange={setModalOpen} onSaved={refresh} />
    </>
  )
}
