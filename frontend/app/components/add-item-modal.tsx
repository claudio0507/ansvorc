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
import { bdApi, fichaApi, orcamentoApi, produtoApi } from "~/lib/api"

const LABELS: Record<string, string> = {
  servicos: "Serviço",
  produtos: "Produto",
  operacional: "Custo Operacional",
  excepcionais: "Custo Excepcional / Manual",
}
const MOD_FAT_OPTS = ["BDI-MAT+MO", "BDI-MO", "BDI+ICMS", "FAT DIR SIMP"]
const SEGUIMENTOS = ["EPS", "HORIZONTAL", "VERTICAL", "APOIO"]

export function AddItemModal({
  bloco,
  orcId,
  onOpenChange,
  onAdded,
}: {
  bloco: string | null
  orcId: number
  onOpenChange: (v: boolean) => void
  onAdded: (novo: any) => void
}) {
  const isServico = bloco === "servicos"
  const isProduto = bloco === "produtos"
  const isOperacional = bloco === "operacional"
  const isManual = bloco === "excepcionais"
  const isFaturavel = isServico || isProduto

  const [seguimento, setSeguimento] = useState("EPS")
  const [catalogo, setCatalogo] = useState<any[]>([]) // fichas serviço/produto OU estrutura
  const [refId, setRefId] = useState("")
  const [descricao, setDescricao] = useState("")
  const [unidade, setUnidade] = useState("un")
  const [quantidade, setQuantidade] = useState("1")
  const [custo, setCusto] = useState("0")
  const [modFat, setModFat] = useState(MOD_FAT_OPTS[0])
  const [margem, setMargem] = useState("10")
  const [saving, setSaving] = useState(false)

  // Carrega catálogo conforme o bloco
  async function carregar() {
    if (isServico) setCatalogo(await fichaApi.listServicos(seguimento))
    // BLOCO 1.5 — produtos do orçamento vêm do cadastro `produtos` (não da ficha)
    else if (isProduto) setCatalogo(await produtoApi.list())
    else if (isOperacional) setCatalogo((await bdApi.listEst()) as any[])
    else setCatalogo([])
  }

  useEffect(() => {
    if (bloco) {
      setRefId("")
      setDescricao("")
      setUnidade("un")
      setQuantidade("1")
      setCusto("0")
      setModFat(MOD_FAT_OPTS[0])
      setMargem("10")
      carregar()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [bloco])

  // Recarrega serviços ao trocar seguimento
  useEffect(() => {
    if (isServico && bloco) carregar()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [seguimento])

  // Ao escolher um item do catálogo, pré-preenche descrição/unidade (readonly p/ ficha)
  function onSelectRef(v: string) {
    setRefId(v)
    const item = catalogo.find((x) => String(x.id) === v)
    if (!item) return
    if (isServico || isProduto) {
      setDescricao(item.nome ?? "")
      setUnidade(item.unidade ?? "un")
    } else if (isOperacional) {
      setDescricao(item.item ?? "")
      setUnidade(item.unidade ?? "un")
      setCusto(String(item.valor_unitario ?? "0"))
    }
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    if (!bloco) return
    if (isFaturavel && !refId) {
      toast.error(isServico ? "Selecione uma ficha de serviço" : "Selecione um produto")
      return
    }
    setSaving(true)
    const payload: Record<string, unknown> = {
      bloco,
      descricao,
      unidade,
      quantidade,
      mod_fat: isFaturavel ? modFat : "-",
      margem_lucro: isFaturavel ? margem : "0",
    }
    if (isServico) payload.ficha_servico_id = Number(refId)
    if (isProduto) payload.produto_id = Number(refId)
    if (isOperacional || isManual) payload.custo_direto_unitario = custo

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
          {isServico && (
            <div className="flex flex-col gap-2">
              <Label>Seguimento</Label>
              <Select value={seguimento} onValueChange={setSeguimento}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {SEGUIMENTOS.map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
          )}

          {isFaturavel && (
            <div className="flex flex-col gap-2 sm:col-span-2">
              <Label>{isServico ? "Ficha de Serviço" : "Produto"} *</Label>
              <Select value={refId} onValueChange={onSelectRef}>
                <SelectTrigger><SelectValue placeholder="Selecione…" /></SelectTrigger>
                <SelectContent>
                  {catalogo.map((x) => (
                    <SelectItem key={x.id} value={String(x.id)}>
                      {x.codigo} — {x.nome}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          {isOperacional && (
            <div className="flex flex-col gap-2 sm:col-span-2">
              <Label>Item de Estrutura</Label>
              <Select value={refId} onValueChange={onSelectRef}>
                <SelectTrigger><SelectValue placeholder="Selecione (preenche custo)…" /></SelectTrigger>
                <SelectContent>
                  {catalogo.map((x) => (
                    <SelectItem key={x.id} value={String(x.id)}>{x.item}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          <div className="flex flex-col gap-2 sm:col-span-2">
            <Label>Descrição *</Label>
            <Input
              required
              placeholder="Descrição do item…"
              value={descricao}
              onChange={(e) => setDescricao(e.target.value)}
              readOnly={isFaturavel}
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label>Unidade {isFaturavel && "(da ficha)"}</Label>
            <Input
              required
              value={unidade}
              onChange={(e) => setUnidade(e.target.value)}
              readOnly={isFaturavel}
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label>Quantidade *</Label>
            <Input type="number" required min="0" step="any" value={quantidade} onChange={(e) => setQuantidade(e.target.value)} />
          </div>

          {(isOperacional || isManual) && (
            <div className="flex flex-col gap-2">
              <Label>Custo Direto Unit. (R$) *</Label>
              <Input type="number" required min="0" step="0.01" value={custo} onChange={(e) => setCusto(e.target.value)} />
            </div>
          )}

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
