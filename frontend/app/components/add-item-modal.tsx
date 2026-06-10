import { useEffect, useState } from "react"
import { toast } from "sonner"

import { Button } from "~/components/ui/button"
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
import { orcamentoApi } from "~/lib/api"

const LABELS: Record<string, string> = {
  servicos: "Serviço",
  produtos: "Produto",
  operacional: "Custo Operacional",
  excepcionais: "Custo Excepcional / Manual",
}
const MOD_FAT_OPTS = ["BDI-MAT+MO", "BDI-MO", "BDI+ICMS", "FAT DIR SIMP"]

export function AddItemModal({
  bloco,
  orcId,
  fichasServico,
  fichasProduto,
  onOpenChange,
  onAdded,
}: {
  bloco: string | null
  orcId: number
  fichasServico: any[]
  fichasProduto: any[]
  onOpenChange: (v: boolean) => void
  onAdded: (novo: any) => void
}) {
  const isFaturavel = bloco === "servicos" || bloco === "produtos"
  const isServico = bloco === "servicos"
  const fichas = isServico ? fichasServico : fichasProduto

  const [fichaId, setFichaId] = useState("")
  const [descricao, setDescricao] = useState("")
  const [unidade, setUnidade] = useState("un")
  const [quantidade, setQuantidade] = useState("1")
  const [custo, setCusto] = useState("0")
  const [modFat, setModFat] = useState(MOD_FAT_OPTS[0])
  const [margem, setMargem] = useState("10")
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (bloco) {
      setFichaId("")
      setDescricao("")
      setUnidade("un")
      setQuantidade("1")
      setCusto("0")
      setModFat(MOD_FAT_OPTS[0])
      setMargem("10")
    }
  }, [bloco])

  function onSelectFicha(v: string) {
    setFichaId(v)
    const f = fichas.find((x) => String(x.id) === v)
    if (f) {
      setDescricao(f.nome ?? "")
      setUnidade(f.unidade_medida ?? "un")
    }
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    if (!bloco) return
    setSaving(true)
    const payload: Record<string, unknown> = {
      bloco,
      descricao,
      unidade_medida: unidade,
      quantidade,
      custo_direto_unitario: custo,
      mod_fat: isFaturavel ? modFat : "-",
      margem_percentual: isFaturavel ? String(parseFloat(margem || "0") / 100) : "0",
      item_excepcional: bloco === "excepcionais",
    }
    if (fichaId) {
      if (bloco === "servicos") payload.ficha_servico_id = Number(fichaId)
      else if (bloco === "produtos") payload.ficha_produto_id = Number(fichaId)
    }
    try {
      const novo = await orcamentoApi.addItem(orcId, payload)
      toast.success("Item adicionado")
      onAdded(novo)
    } catch (err: any) {
      toast.error(`Erro: ${err.message}`)
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open={!!bloco} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>Adicionar {bloco ? LABELS[bloco] : ""}</DialogTitle>
        </DialogHeader>
        <form onSubmit={submit} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {isFaturavel && (
            <div className="flex flex-col gap-2 sm:col-span-2">
              <Label>Ficha Técnica</Label>
              <Select value={fichaId} onValueChange={onSelectFicha}>
                <SelectTrigger><SelectValue placeholder="Selecione para pré-preencher (opcional)…" /></SelectTrigger>
                <SelectContent>
                  {fichas.map((f) => (
                    <SelectItem key={f.id} value={String(f.id)}>
                      {f.codigo} — {f.nome}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
          <div className="flex flex-col gap-2 sm:col-span-2">
            <Label>Descrição *</Label>
            <Input required placeholder="Descrição do item…" value={descricao} onChange={(e) => setDescricao(e.target.value)} />
          </div>
          <div className="flex flex-col gap-2">
            <Label>Unidade *</Label>
            <Input required value={unidade} onChange={(e) => setUnidade(e.target.value)} />
          </div>
          <div className="flex flex-col gap-2">
            <Label>Quantidade *</Label>
            <Input type="number" required min="0.0001" step="0.01" value={quantidade} onChange={(e) => setQuantidade(e.target.value)} />
          </div>
          <div className="flex flex-col gap-2">
            <Label>Custo Direto Unit. (R$) *</Label>
            <Input type="number" required min="0" step="0.01" value={custo} onChange={(e) => setCusto(e.target.value)} />
          </div>
          {isFaturavel && (
            <>
              <div className="flex flex-col gap-2">
                <Label>MOD FAT</Label>
                <Select value={modFat} onValueChange={setModFat}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {MOD_FAT_OPTS.map((m) => <SelectItem key={m} value={m}>{m}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex flex-col gap-2">
                <Label>Margem (%)</Label>
                <Input type="number" min="0" max="99.9" step="0.1" value={margem} onChange={(e) => setMargem(e.target.value)} />
              </div>
            </>
          )}
          <DialogFooter className="sm:col-span-2">
            <Button type="button" variant="secondary" onClick={() => onOpenChange(false)}>Cancelar</Button>
            <Button type="submit" disabled={saving}>{saving ? "Adicionando…" : "Adicionar Item"}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
