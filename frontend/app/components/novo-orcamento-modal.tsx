import { useEffect, useState } from "react"
import { toast } from "sonner"

import { Button } from "~/components/ui/button"
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "~/components/ui/select"
import { clienteApi, orcamentoApi, parametroApi } from "~/lib/api"

const UFS = [
  { v: "PR", l: "Paraná (PR)" },
  { v: "SP", l: "São Paulo (SP)" },
  { v: "SC", l: "Santa Catarina (SC)" },
  { v: "RS", l: "Rio Grande do Sul (RS)" },
  { v: "MG", l: "Minas Gerais (MG)" },
]

export function NovoOrcamentoModal({
  open,
  onOpenChange,
  onCreated,
}: {
  open: boolean
  onOpenChange: (v: boolean) => void
  onCreated: (novo: any) => void
}) {
  const [clientes, setClientes] = useState<any[]>([])
  const [numero, setNumero] = useState("")
  const [clienteId, setClienteId] = useState("")
  const [obra, setObra] = useState("")
  const [uf, setUf] = useState("PR")
  const [reidi, setReidi] = useState(false)
  const [dataLimite, setDataLimite] = useState("")
  const [seguimentosDisp, setSeguimentosDisp] = useState<any[]>([])
  const [segmentos, setSegmentos] = useState<string[]>([])
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (open) {
      setNumero("")
      setClienteId("")
      setObra("")
      setUf("PR")
      setReidi(false)
      setDataLimite("")
      setSegmentos([])
      clienteApi.list().then(setClientes).catch(() => setClientes([]))
      parametroApi.listSeguimentos().then(setSeguimentosDisp).catch(() => setSeguimentosDisp([]))
    }
  }, [open])

  function toggleSegmento(nome: string) {
    setSegmentos((prev) =>
      prev.includes(nome) ? prev.filter((s) => s !== nome) : [...prev, nome]
    )
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    if (!clienteId) {
      toast.error("Selecione um cliente.")
      return
    }
    setSaving(true)
    try {
      const novo = await orcamentoApi.create({
        numero: numero,
        cliente_id: Number(clienteId),
        obra: obra || null,
        uf_execucao: uf,
        beneficio_reidi: reidi,
        data_limite: dataLimite || null,
        segmentos,
      })
      toast.success("Orçamento criado!")
      onOpenChange(false)
      onCreated(novo)
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
          <DialogTitle>Novo Orçamento</DialogTitle>
        </DialogHeader>
        <form onSubmit={submit} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="flex flex-col gap-2 sm:col-span-2">
            <Label>Nº Proposta *</Label>
            <Input required placeholder="PROP-2025-001" value={numero} onChange={(e) => setNumero(e.target.value)} />
          </div>
          <div className="flex flex-col gap-2 sm:col-span-2">
            <Label>Cliente *</Label>
            <Select value={clienteId} onValueChange={setClienteId}>
              <SelectTrigger><SelectValue placeholder="Selecione…" /></SelectTrigger>
              <SelectContent>
                {clientes.map((c) => (
                  <SelectItem key={c.id} value={String(c.id)}>{c.nome}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            {clientes.length === 0 && (
              <p className="text-warning text-xs">Nenhum cliente cadastrado. Crie um cliente primeiro.</p>
            )}
          </div>
          <div className="flex flex-col gap-2 sm:col-span-2">
            <Label>Descrição da Obra</Label>
            <Input placeholder="Ex: Rodovia PR-444 — Lote 3" value={obra} onChange={(e) => setObra(e.target.value)} />
          </div>
          <div className="flex flex-col gap-2 sm:col-span-2">
            <Label>Data-limite de envio</Label>
            <Input type="date" value={dataLimite} onChange={(e) => setDataLimite(e.target.value)} />
          </div>
          <div className="flex flex-col gap-2 sm:col-span-2">
            <Label>Segmentos</Label>
            <div className="flex flex-wrap gap-3">
              {seguimentosDisp.map((s) => (
                <label key={s.id ?? s.nome} className="flex cursor-pointer items-center gap-2">
                  <Checkbox
                    checked={segmentos.includes(s.nome)}
                    onCheckedChange={() => toggleSegmento(s.nome)}
                  />
                  <span className="text-sm">{s.nome}</span>
                </label>
              ))}
              {seguimentosDisp.length === 0 && (
                <span className="text-muted-foreground text-xs">Nenhum segmento cadastrado.</span>
              )}
            </div>
          </div>
          <div className="flex flex-col gap-2">
            <Label>UF de Execução *</Label>
            <Select value={uf} onValueChange={setUf}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                {UFS.map((u) => <SelectItem key={u.v} value={u.v}>{u.l}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <label className="flex cursor-pointer items-center gap-2 self-end">
            <Checkbox checked={reidi} onCheckedChange={(c) => setReidi(!!c)} />
            <span className="text-sm">Benefício REIDI (PIS/COFINS)</span>
          </label>
          <DialogFooter className="sm:col-span-2">
            <Button type="button" variant="secondary" onClick={() => onOpenChange(false)}>Cancelar</Button>
            <Button type="submit" disabled={saving}>{saving ? "Criando…" : "Criar e Abrir"}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
