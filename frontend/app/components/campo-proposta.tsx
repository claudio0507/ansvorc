import { useEffect, useId, useState } from "react"

import { Input } from "~/components/ui/input"
import { Label } from "~/components/ui/label"
import { Textarea } from "~/components/ui/textarea"

type BaseProps = {
  label: string
  value: string
  onSave: (valor: string) => void
  placeholder?: string
  /** Texto do padrão da empresa exibido quando vazio (fallback). */
  placeholderFallback?: string
  readonly?: boolean
}

function notaFallback(placeholderFallback?: string) {
  if (!placeholderFallback) return null
  return (
    <p className="text-muted-foreground/70 text-[0.625rem] italic">
      Vazio usa o padrão da empresa — edite para sobrescrever.
    </p>
  )
}

export function CampoTexto({
  label,
  value,
  onSave,
  placeholder,
  placeholderFallback,
  readonly,
}: BaseProps) {
  const [v, setV] = useState(value ?? "")
  useEffect(() => {
    setV(value ?? "")
  }, [value])
  const fieldId = useId()
  return (
    <div className="flex flex-col gap-1.5">
      <Label htmlFor={fieldId} className="text-muted-foreground text-xs font-medium uppercase">{label}</Label>
      {readonly ? (
        <div className="bg-secondary/40 min-h-9 rounded border px-3 py-2 text-sm">
          {value || <span className="text-muted-foreground italic">—</span>}
        </div>
      ) : (
        <>
          <Input
            id={fieldId}
            value={v}
            placeholder={placeholderFallback || placeholder}
            onChange={(e) => setV(e.target.value)}
            onBlur={() => {
              if (v !== (value ?? "")) onSave(v)
            }}
          />
          {!v && notaFallback(placeholderFallback)}
        </>
      )}
    </div>
  )
}

export function CampoTextarea({
  label,
  value,
  onSave,
  placeholder,
  placeholderFallback,
  readonly,
  rows = 3,
}: BaseProps & { rows?: number }) {
  const [v, setV] = useState(value ?? "")
  useEffect(() => {
    setV(value ?? "")
  }, [value])
  const fieldId = useId()
  return (
    <div className="flex flex-col gap-1.5">
      <Label htmlFor={fieldId} className="text-muted-foreground text-xs font-medium uppercase">{label}</Label>
      {readonly ? (
        <div className="bg-secondary/40 min-h-9 rounded border px-3 py-2 text-sm whitespace-pre-wrap">
          {value || <span className="text-muted-foreground italic">—</span>}
        </div>
      ) : (
        <>
          <Textarea
            id={fieldId}
            value={v}
            rows={rows}
            placeholder={placeholderFallback || placeholder}
            onChange={(e) => setV(e.target.value)}
            onBlur={() => {
              if (v !== (value ?? "")) onSave(v)
            }}
          />
          {!v && notaFallback(placeholderFallback)}
        </>
      )}
    </div>
  )
}
