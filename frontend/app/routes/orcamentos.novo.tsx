import { useState } from "react"
import { useNavigate } from "react-router"

import { NovoOrcamentoModal } from "~/components/novo-orcamento-modal"

/** Rota /orcamentos/novo — abre o modal sobre um fundo vazio. */
export default function OrcamentoNovo() {
  const navigate = useNavigate()
  const [open, setOpen] = useState(true)

  return (
    <NovoOrcamentoModal
      open={open}
      onOpenChange={(v) => {
        setOpen(v)
        if (!v) navigate("/orcamentos", { replace: true })
      }}
      onCreated={(novo) => navigate(`/orcamentos/${novo.id}`)}
    />
  )
}
