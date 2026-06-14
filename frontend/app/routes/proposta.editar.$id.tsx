import { useCallback, useEffect, useState } from "react"
import { Link, useParams } from "react-router"
import { toast } from "sonner"
import { ArrowLeftIcon, FileTextIcon } from "@phosphor-icons/react"

import { StatusBadge } from "~/components/status-badge"
import { Button } from "~/components/ui/button"
import { orcamentoApi } from "~/lib/api"

const EDITAVEL = ["rascunho", "reprovado"]

export default function PropostaEditor() {
  const { id } = useParams()
  const orcId = Number(id)

  const [data, setData] = useState<any>(null)
  const [erro, setErro] = useState("")
  const [carregando, setCarregando] = useState(true)

  const carregar = useCallback(async () => {
    setCarregando(true)
    setErro("")
    try {
      setData(await orcamentoApi.getProposta(orcId))
    } catch (e: any) {
      setErro(e.message)
    } finally {
      setCarregando(false)
    }
  }, [orcId])

  useEffect(() => {
    carregar()
  }, [carregar])

  if (carregando) {
    return <div className="text-muted-foreground py-12 text-center">Carregando proposta…</div>
  }
  if (erro || !data?.orcamento) {
    return (
      <div className="py-12 text-center">
        <h3 className="text-lg font-semibold">Erro ao carregar proposta</h3>
        <p className="text-muted-foreground mt-1">{erro}</p>
        <Button asChild variant="secondary" className="mt-4">
          <Link to={`/orcamentos/${orcId}`}>← Voltar ao orçamento</Link>
        </Button>
      </div>
    )
  }

  const { orcamento: orc } = data
  const readonly = !EDITAVEL.includes(orc.status)

  // Salva um campo do orçamento (PUT /orcamentos/:id) e atualiza o estado local.
  async function salvarOrc(campo: string, valor: string | number | null) {
    try {
      await orcamentoApi.update(orcId, { [campo]: valor })
      setData((d: any) => ({ ...d, orcamento: { ...d.orcamento, [campo]: valor } }))
    } catch (e: any) {
      toast.error(`Erro ao salvar: ${e.message}`)
    }
  }

  return (
    <>
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Button asChild variant="ghost" size="icon">
            <Link to={`/orcamentos/${orcId}`} aria-label="Voltar">
              <ArrowLeftIcon className="size-4" />
            </Link>
          </Button>
          <h2 className="text-xl font-semibold">Proposta {orc.numero}</h2>
          <StatusBadge status={orc.status} />
        </div>
        <Button asChild size="sm" variant="ghost">
          <Link to={`/orcamentos/${orcId}/proposta`}>
            <FileTextIcon className="size-4" /> Ver documento
          </Link>
        </Button>
      </div>

      {readonly && (
        <p className="text-warning bg-warning/10 mb-4 rounded p-2.5 text-center text-xs">
          Orçamento com status "{orc.status}" — somente leitura.
        </p>
      )}

      <div className="grid grid-cols-1 items-start gap-5 lg:grid-cols-[1fr_180px]">
        <div className="space-y-4">
          {/* SEÇÕES entram na Task 5 */}
        </div>
        <nav className="sticky top-4 hidden lg:block">
          {/* ÍNDICE entra na Task 5 */}
        </nav>
      </div>
    </>
  )
}
