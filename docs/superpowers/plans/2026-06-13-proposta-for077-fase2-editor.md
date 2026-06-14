# Proposta FOR-077 — Fase 2 (Editor + aba Empresa) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir o editor de proposta comercial FOR-077 (19 seções, layout de cards + índice interno, auto-save onBlur) em rota própria por orçamento, e expandir a aba Empresa dos Parâmetros para os 17 campos globais do ConfigSistema.

**Architecture:** Frontend React Router 7 + Tailwind v4 + shadcn/Radix, tema Discord Dark. Editor é uma rota nova `/orcamentos/:id/proposta/editar` que consome o endpoint F1 `GET /orcamentos/:id/proposta` (fonte única) e salva campo-a-campo via `PUT /orcamentos/:id` (campos do orçamento) e `PATCH /orcamentos/:id/itens/:iid` (descrição-cliente). A aba Empresa em `parametros.tsx` ganha os campos do ConfigSistema com um único botão Salvar.

**Tech Stack:** React 19, React Router 7.15, TypeScript, Tailwind v4, shadcn UI (Card, Input, Textarea, Label, Button, Badge), sonner (toast), `~/lib/api`, `~/lib/format`.

---

## Convenções verificadas (leia antes de começar)

- **NÃO há suíte de testes no frontend** (só `tests/` do backend, pytest). Cada task é verificada com `npm run typecheck` (= `react-router typegen && tsc`) e, onde indicado, `npm run build` + um check manual no browser. NÃO introduza Jest/Vitest/Testing Library — está fora de escopo (YAGNI).
- **Rodar typecheck (PowerShell, a partir da raiz):** `cd frontend; npm run typecheck` — ou via Bash: `cd "g:/Meu Drive/ansvorc/frontend" && npm run typecheck`. Esperado: sem erros de tipo.
- **Componentes UI disponíveis** (`~/components/ui/`): `Card`, `Input`, `Textarea`, `Label`, `Button`, `Badge`, `Select`, `Table*`, `Tabs*`. Todos já existem. Importe de `~/components/ui/<nome>`.
- **Helpers de formato** (`~/lib/format`): `fmtBRL(v)`, `fmtData(iso)`. Use-os.
- **API client** (`~/lib/api`): `orcamentoApi` (get, update, listItens, updateItem…), `configApi` (get, update, uploadLogo). Tipos são `any` no projeto — siga o padrão (`useState<any>`).
- **Padrões de tela existentes a imitar:**
  - `frontend/app/routes/orcamentos.$id.tsx` — auto-save onBlur (`salvarCampo`), read-only por status (`readonly = orc && !["rascunho","reprovado"].includes(orc.status)`), tela de erro com "Voltar".
  - `frontend/app/routes/proposta.tsx` — já edita `descricao_cliente`/`texto_topo_proposta` onBlur; padrão de carregamento.
  - `frontend/app/routes/parametros.tsx` — componente `EmpresaConfig` atual (4 campos), `Tabs`, `configApi`.
- **Tema:** use tokens Tailwind do projeto (`bg-card`, `bg-secondary`, `text-primary`, `text-muted-foreground`, `border`, `text-success`), NÃO hex direto. O acento vermelho é `text-primary`/`bg-primary` (mapeado para #c32a30 no tema).
- **Branch:** `feat/melhorias-v2`. NÃO criar branch nova.

---

## File Structure

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `frontend/app/lib/api.ts` | Modificar | + `orcamentoApi.getProposta(id)` e `orcamentoApi.patchDescricaoItem(id, iid, descricao)` |
| `frontend/app/routes.ts` | Modificar | registra `orcamentos/:id/proposta/editar` |
| `frontend/app/routes/orcamentos.$id.tsx` | Modificar | botão "Editar Proposta" no header |
| `frontend/app/components/secao-card.tsx` | Criar | `SecaoCard` (card de seção: título acento + badge) — reutilizável |
| `frontend/app/components/campo-proposta.tsx` | Criar | `CampoTexto` + `CampoTextarea` (auto-save onBlur, read-only aware) |
| `frontend/app/routes/proposta.editar.$id.tsx` | Criar | o editor das 19 seções (layout A) |
| `frontend/app/routes/parametros.tsx` | Modificar | `EmpresaConfig` 4 → 17 campos, save único |

Decompondo `SecaoCard`/`CampoTexto`/`CampoTextarea` em arquivos próprios (não inline) porque são usados pelo editor e mantêm `proposta.editar.$id.tsx` focado na composição das 19 seções.

---

## Task 1: Camada de API — getProposta + patchDescricaoItem

**Files:**
- Modify: `frontend/app/lib/api.ts` (objeto `orcamentoApi`, ~linha 200-221)

- [ ] **Step 1: Adicionar os dois métodos ao `orcamentoApi`**

Em `frontend/app/lib/api.ts`, dentro do objeto `orcamentoApi`, logo após a linha `calcular: (id: number) => api.post<any>(\`/orcamentos/${id}/calcular\`),` adicione:

```ts
  getProposta: (id: number) => api.get<any>(`/orcamentos/${id}/proposta`),
  patchDescricaoItem: (id: number, iid: number, descricao: string) =>
    api.patch<any>(`/orcamentos/${id}/itens/${iid}`, { descricao }),
```

- [ ] **Step 2: Verificar typecheck**

Run: `cd "g:/Meu Drive/ansvorc/frontend" && npm run typecheck`
Expected: sem erros.

- [ ] **Step 3: Commit**

```bash
git add frontend/app/lib/api.ts
git commit -m "feat(proposta): api getProposta + patchDescricaoItem (FOR-077 F2)"
```

---

## Task 2: Componente SecaoCard

**Files:**
- Create: `frontend/app/components/secao-card.tsx`

- [ ] **Step 1: Criar o componente**

`SecaoCard` é o card de uma seção da proposta: título em acento + borda inferior + badge opcional (NOVO/EXISTENTE/SISTEMA) + `id` para o scroll do índice. Crie `frontend/app/components/secao-card.tsx`:

```tsx
import type { ReactNode } from "react"

import { Card } from "~/components/ui/card"

type Badge = "novo" | "existente" | "sistema"

const BADGE_STYLE: Record<Badge, string> = {
  novo: "bg-primary text-primary-foreground",
  existente: "bg-secondary text-secondary-foreground",
  sistema: "bg-success/15 text-success",
}
const BADGE_LABEL: Record<Badge, string> = {
  novo: "NOVO",
  existente: "EXISTENTE",
  sistema: "SISTEMA",
}

export function SecaoCard({
  id,
  titulo,
  badge,
  children,
}: {
  id: string
  titulo: string
  badge?: Badge
  children: ReactNode
}) {
  return (
    <Card id={id} className="scroll-mt-20 p-5">
      <div className="text-primary mb-3 flex items-center gap-2 border-b pb-2 text-xs font-bold tracking-wide uppercase">
        {titulo}
        {badge && (
          <span
            className={`rounded px-1.5 py-0.5 text-[0.625rem] font-bold ${BADGE_STYLE[badge]}`}
          >
            {BADGE_LABEL[badge]}
          </span>
        )}
      </div>
      <div className="space-y-3">{children}</div>
    </Card>
  )
}
```

- [ ] **Step 2: Verificar typecheck**

Run: `cd "g:/Meu Drive/ansvorc/frontend" && npm run typecheck`
Expected: sem erros.

- [ ] **Step 3: Commit**

```bash
git add frontend/app/components/secao-card.tsx
git commit -m "feat(proposta): componente SecaoCard (FOR-077 F2)"
```

---

## Task 3: Componentes CampoTexto + CampoTextarea (auto-save onBlur)

**Files:**
- Create: `frontend/app/components/campo-proposta.tsx`

- [ ] **Step 1: Criar os componentes**

Inputs com auto-save onBlur. Quando `readonly`, renderiza o valor como texto (não input). Quando vazio e há `placeholderFallback`, mostra esse texto em cinza/itálico no placeholder (indica "usando padrão da empresa"). Crie `frontend/app/components/campo-proposta.tsx`:

```tsx
import { useState } from "react"

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
  return (
    <div className="flex flex-col gap-1.5">
      <Label className="text-muted-foreground text-xs font-medium uppercase">{label}</Label>
      {readonly ? (
        <div className="bg-secondary/40 min-h-9 rounded border px-3 py-2 text-sm">
          {value || <span className="text-muted-foreground italic">—</span>}
        </div>
      ) : (
        <>
          <Input
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
  return (
    <div className="flex flex-col gap-1.5">
      <Label className="text-muted-foreground text-xs font-medium uppercase">{label}</Label>
      {readonly ? (
        <div className="bg-secondary/40 min-h-9 rounded border px-3 py-2 text-sm whitespace-pre-wrap">
          {value || <span className="text-muted-foreground italic">—</span>}
        </div>
      ) : (
        <>
          <Textarea
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
```

- [ ] **Step 2: Verificar typecheck**

Run: `cd "g:/Meu Drive/ansvorc/frontend" && npm run typecheck`
Expected: sem erros. (Se `Textarea` não exportar `rows`/`placeholder`, são props nativas do `<textarea>` — o componente shadcn repassa via `...props`; sem erro esperado.)

- [ ] **Step 3: Commit**

```bash
git add frontend/app/components/campo-proposta.tsx
git commit -m "feat(proposta): campos com auto-save onBlur + fallback (FOR-077 F2)"
```

---

## Task 4: Rota do editor + esqueleto (carregamento, erro, header, read-only)

**Files:**
- Create: `frontend/app/routes/proposta.editar.$id.tsx`
- Modify: `frontend/app/routes.ts`

- [ ] **Step 1: Registrar a rota**

Em `frontend/app/routes.ts`, dentro do bloco `layout("routes/_app.tsx", [...])`, logo após a linha `route("orcamentos/:id/proposta", "routes/proposta.tsx"),` adicione:

```ts
    route("orcamentos/:id/proposta/editar", "routes/proposta.editar.$id.tsx"),
```

- [ ] **Step 2: Criar o esqueleto do editor**

Cria `frontend/app/routes/proposta.editar.$id.tsx` com carregamento via `getProposta`, estados, tela de erro e o header. As 19 seções entram na Task 5 (por enquanto um placeholder na coluna de cards):

```tsx
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
```

Nota: `StatusBadge` existe em `~/components/status-badge` (usado em `orcamentos.$id.tsx`). `salvarOrc` será consumido pelas seções na Task 5. O `tsconfig.json` do projeto **NÃO** tem `noUnusedLocals` (verificado), então a função temporariamente não-usada NÃO quebra o typecheck — não adicione `void salvarOrc` nem workaround.

- [ ] **Step 3: Verificar typecheck**

Run: `cd "g:/Meu Drive/ansvorc/frontend" && npm run typecheck`
Expected: sem erros. (`salvarOrc` ainda não é chamado, mas o projeto não usa `noUnusedLocals` — não quebra.)

- [ ] **Step 4: Commit**

```bash
git add frontend/app/routes.ts frontend/app/routes/proposta.editar.$id.tsx
git commit -m "feat(proposta): rota + esqueleto do editor de proposta (FOR-077 F2)"
```

---

## Task 5: As 19 seções + índice interno

**Files:**
- Modify: `frontend/app/routes/proposta.editar.$id.tsx`

- [ ] **Step 1: Importar componentes e dados auxiliares**

No topo de `proposta.editar.$id.tsx`, adicione aos imports existentes:

```tsx
import { SecaoCard } from "~/components/secao-card"
import { CampoTexto, CampoTextarea } from "~/components/campo-proposta"
import { fmtBRL, fmtData } from "~/lib/format"
```

- [ ] **Step 2: Definir o índice e helpers dentro do componente**

Logo antes do `return (`, adicione o array do índice e o helper de salvar descrição de item. Também derive `cliente`, `config`, `itens`, `resolvidos`:

```tsx
  const { cliente, config, itens, resolvidos, garantia_texto } = data
  const FATURAVEIS = ["servicos", "produtos"]
  const itensFat = (itens ?? []).filter((i: any) => FATURAVEIS.includes(i.bloco))
  const temPrecos = itensFat.some((i: any) => parseFloat(i.preco_venda_total) > 0)

  const INDICE = [
    "1. Cabeçalho", "2. Destinatário", "3. Objeto", "4. Declarações",
    "5. Escopo", "6. Modalidade", "7. Preço", "8. Prazo + Tributária",
    "9. Faturamento", "10. Medição", "11. Bancários", "12. Representante",
    "13. Testemunha", "14. Reajustamento", "15. Garantia", "16. As Built",
    "17. Validade", "18. Observação", "19. Contato",
  ]

  async function salvarDescricaoItem(iid: number, valor: string) {
    try {
      const upd = await orcamentoApi.patchDescricaoItem(orcId, iid, valor)
      setData((d: any) => ({
        ...d,
        itens: d.itens.map((i: any) => (i.id === iid ? { ...i, ...upd } : i)),
      }))
    } catch (e: any) {
      toast.error(`Erro: ${e.message}`)
    }
  }

  // Texto de garantia recalculado localmente p/ feedback imediato.
  const garTexto =
    orc.garantia_retencao_pct != null && orc.garantia_devolucao_dias != null
      ? `Retenção de ${Number(orc.garantia_retencao_pct)}%, com devolução em ${orc.garantia_devolucao_dias} dias após o termo de encerramento.`
      : garantia_texto || "—"
```

- [ ] **Step 3: Substituir o placeholder das seções pelo conteúdo das 19 seções**

Substitua o bloco `<div className="space-y-4">{/* SEÇÕES entram na Task 5 */}</div>` por:

```tsx
        <div className="space-y-4">
          {/* 1. Cabeçalho — sistema, read-only */}
          <SecaoCard id="sec-1" titulo="1. Cabeçalho" badge="sistema">
            <div className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
              <div><div className="text-muted-foreground text-xs uppercase">Nº</div>{orc.numero}</div>
              <div><div className="text-muted-foreground text-xs uppercase">Versão</div>{orc.versao}</div>
              <div><div className="text-muted-foreground text-xs uppercase">Data</div>{fmtData(orc.created_at)}</div>
              <div><div className="text-muted-foreground text-xs uppercase">UF</div>{orc.uf_execucao}</div>
            </div>
          </SecaoCard>

          {/* 2. Destinatário — cliente, read-only */}
          <SecaoCard id="sec-2" titulo="2. Destinatário" badge="existente">
            <div className="text-sm">
              <div className="font-medium">{cliente?.nome ?? `#${orc.cliente_id}`}</div>
              {cliente?.cnpj_cpf && <div className="text-muted-foreground text-xs">{cliente.cnpj_cpf}</div>}
              {cliente?.contato_nome && <div className="text-muted-foreground text-xs">{cliente.contato_nome}</div>}
            </div>
          </SecaoCard>

          {/* 3. Objeto */}
          <SecaoCard id="sec-3" titulo="3. Objeto" badge="existente">
            <CampoTextarea label="Obra" value={orc.obra ?? ""} readonly={readonly} rows={2}
              onSave={(v) => salvarOrc("obra", v)} placeholder="Descrição da obra/objeto" />
          </SecaoCard>

          {/* 4. Declarações — fallback declaracoes_padrao */}
          <SecaoCard id="sec-4" titulo="4. Declarações" badge="existente">
            <CampoTextarea label="Texto topo (declarações)" value={orc.texto_topo_proposta ?? ""}
              readonly={readonly} rows={5}
              placeholderFallback={resolvidos?.texto_topo_proposta}
              onSave={(v) => salvarOrc("texto_topo_proposta", v)} />
          </SecaoCard>

          {/* 5. Escopo */}
          <SecaoCard id="sec-5" titulo="5. Escopo" badge="novo">
            <CampoTextarea label="Escopo detalhado" value={orc.escopo ?? ""} readonly={readonly} rows={4}
              onSave={(v) => salvarOrc("escopo", v)} placeholder="Descrição detalhada do escopo" />
          </SecaoCard>

          {/* 6. Modalidade */}
          <SecaoCard id="sec-6" titulo="6. Modalidade" badge="novo">
            <CampoTexto label="Modalidade" value={orc.modalidade ?? ""} readonly={readonly}
              placeholderFallback={resolvidos?.modalidade}
              onSave={(v) => salvarOrc("modalidade", v)} />
          </SecaoCard>

          {/* 7. Preço — só descrição editável; qtd/preços read-only */}
          <SecaoCard id="sec-7" titulo="7. Preço" badge="sistema">
            {!temPrecos && (
              <p className="text-warning bg-warning/10 rounded p-2 text-center text-xs">
                Calcule o orçamento para ver os preços.
              </p>
            )}
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-muted-foreground text-[0.625rem] uppercase">
                    <th className="px-2 py-1 text-left">Descrição (cliente)</th>
                    <th className="px-2 py-1 text-center">Un</th>
                    <th className="px-2 py-1 text-right">Qtd</th>
                    <th className="px-2 py-1 text-right">Preço Unit</th>
                    <th className="px-2 py-1 text-right">Preço Total</th>
                  </tr>
                </thead>
                <tbody>
                  {itensFat.length === 0 ? (
                    <tr><td colSpan={5} className="text-muted-foreground py-3 text-center">Nenhum item faturável.</td></tr>
                  ) : itensFat.map((it: any) => (
                    <tr key={it.id} className="border-t">
                      <td className="px-2 py-1">
                        {readonly ? (
                          <span>{it.descricao_cliente || it.descricao}</span>
                        ) : (
                          <input
                            defaultValue={it.descricao_cliente ?? it.descricao}
                            onBlur={(e) => {
                              const nv = e.target.value
                              if (nv !== (it.descricao_cliente ?? it.descricao)) salvarDescricaoItem(it.id, nv)
                            }}
                            className="border-primary w-full rounded border bg-transparent px-1.5 py-0.5"
                          />
                        )}
                      </td>
                      <td className="text-muted-foreground px-2 py-1 text-center">{it.unidade}</td>
                      <td className="text-muted-foreground px-2 py-1 text-right">
                        {Number(it.quantidade).toLocaleString("pt-BR", { maximumFractionDigits: 2 })}
                      </td>
                      <td className="text-muted-foreground px-2 py-1 text-right">
                        {parseFloat(it.preco_venda_total) > 0 ? fmtBRL(it.preco_venda_unitario_final || it.preco_venda_unitario) : "—"}
                      </td>
                      <td className="px-2 py-1 text-right font-medium">
                        {parseFloat(it.preco_venda_total) > 0 ? fmtBRL(it.preco_venda_total) : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="text-right text-sm">
              Total: <span className="text-primary text-base font-bold">
                {orc.total_proposta ? fmtBRL(orc.total_proposta) : "—"}
              </span>
            </div>
          </SecaoCard>

          {/* 8. Prazo + Tributária */}
          <SecaoCard id="sec-8" titulo="8. Prazo + Tributária" badge="novo">
            <CampoTexto label="Prazo de entrega" value={orc.prazo_entrega ?? ""} readonly={readonly}
              onSave={(v) => salvarOrc("prazo_entrega", v)} placeholder="90 (noventa) dias…" />
            <CampoTextarea label="Cláusula tributária (IBS/CBS)" value={orc.clausula_tributaria ?? ""}
              readonly={readonly} rows={4}
              placeholderFallback={resolvidos?.clausula_tributaria}
              onSave={(v) => salvarOrc("clausula_tributaria", v)} />
          </SecaoCard>

          {/* 9. Faturamento */}
          <SecaoCard id="sec-9" titulo="9. Faturamento Direto" badge="novo">
            <CampoTexto label="Faturamento direto" value={orc.faturamento_direto ?? ""} readonly={readonly}
              placeholderFallback={resolvidos?.faturamento_direto}
              onSave={(v) => salvarOrc("faturamento_direto", v)} />
          </SecaoCard>

          {/* 10. Medição */}
          <SecaoCard id="sec-10" titulo="10. Medição e Pagamento" badge="novo">
            <CampoTextarea label="Medição e pagamento" value={orc.medicao_pagamento ?? ""}
              readonly={readonly} rows={3}
              onSave={(v) => salvarOrc("medicao_pagamento", v)} placeholder="Critérios de medição…" />
          </SecaoCard>

          {/* 11. Dados Bancários — config, read-only */}
          <SecaoCard id="sec-11" titulo="11. Dados Bancários" badge="novo">
            <div className="grid grid-cols-3 gap-3 text-sm">
              <div><div className="text-muted-foreground text-xs uppercase">Banco</div>{config?.banco ?? "—"}</div>
              <div><div className="text-muted-foreground text-xs uppercase">Agência</div>{config?.agencia ?? "—"}</div>
              <div><div className="text-muted-foreground text-xs uppercase">Conta</div>{config?.conta_corrente ?? "—"}</div>
            </div>
            <Link to="/parametros" className="text-primary text-xs hover:underline">→ editar em Parâmetros</Link>
          </SecaoCard>

          {/* 12. Representante — config, read-only */}
          <SecaoCard id="sec-12" titulo="12. Representante Legal" badge="existente">
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div><div className="text-muted-foreground text-xs uppercase">Nome</div>{config?.diretor_nome ?? "—"}</div>
              <div><div className="text-muted-foreground text-xs uppercase">Função</div>{config?.diretor_funcao ?? "—"}</div>
              <div><div className="text-muted-foreground text-xs uppercase">CPF</div>{config?.diretor_cpf ?? "—"}</div>
              <div><div className="text-muted-foreground text-xs uppercase">CNPJ</div>{config?.cnpj ?? "—"}</div>
            </div>
            <Link to="/parametros" className="text-primary text-xs hover:underline">→ editar em Parâmetros</Link>
          </SecaoCard>

          {/* 13. Testemunha */}
          <SecaoCard id="sec-13" titulo="13. Testemunha" badge="novo">
            <CampoTexto label="Nome" value={orc.testemunha_nome ?? ""} readonly={readonly}
              onSave={(v) => salvarOrc("testemunha_nome", v)} />
            <CampoTexto label="E-mail" value={orc.testemunha_email ?? ""} readonly={readonly}
              onSave={(v) => salvarOrc("testemunha_email", v)} />
            <CampoTexto label="CPF" value={orc.testemunha_cpf ?? ""} readonly={readonly}
              onSave={(v) => salvarOrc("testemunha_cpf", v)} />
          </SecaoCard>

          {/* 14. Reajustamento — fallback */}
          <SecaoCard id="sec-14" titulo="14. Reajustamento" badge="novo">
            <CampoTextarea label="Reajustamento (IPCA/IGPM)" value={orc.reajustamento ?? ""}
              readonly={readonly} rows={4}
              placeholderFallback={resolvidos?.reajustamento}
              onSave={(v) => salvarOrc("reajustamento", v)} />
          </SecaoCard>

          {/* 15. Garantia — pct/dias + texto auto */}
          <SecaoCard id="sec-15" titulo="15. Garantia Contratual" badge="novo">
            <div className="grid grid-cols-2 gap-3">
              <CampoTexto label="Retenção (%)" value={orc.garantia_retencao_pct != null ? String(orc.garantia_retencao_pct) : ""}
                readonly={readonly} placeholderFallback={resolvidos?.garantia_retencao_pct != null ? String(resolvidos.garantia_retencao_pct) : undefined}
                onSave={(v) => salvarOrc("garantia_retencao_pct", v === "" ? null : v)} />
              <CampoTexto label="Devolução (dias)" value={orc.garantia_devolucao_dias != null ? String(orc.garantia_devolucao_dias) : ""}
                readonly={readonly} placeholderFallback={resolvidos?.garantia_devolucao_dias != null ? String(resolvidos.garantia_devolucao_dias) : undefined}
                onSave={(v) => salvarOrc("garantia_devolucao_dias", v === "" ? null : Number(v))} />
            </div>
            <p className="text-muted-foreground text-xs">{garTexto}</p>
          </SecaoCard>

          {/* 16. As Built */}
          <SecaoCard id="sec-16" titulo="16. Entrega de As Built" badge="novo">
            <CampoTexto label="Entrega de as built" value={orc.entrega_as_built ?? ""} readonly={readonly}
              placeholderFallback={resolvidos?.entrega_as_built}
              onSave={(v) => salvarOrc("entrega_as_built", v)} />
          </SecaoCard>

          {/* 17. Validade */}
          <SecaoCard id="sec-17" titulo="17. Validade da Proposta" badge="existente">
            <CampoTexto label="Validade" value={orc.validade_proposta ?? ""} readonly={readonly}
              onSave={(v) => salvarOrc("validade_proposta", v)} placeholder="90 (noventa) dias…" />
          </SecaoCard>

          {/* 18. Observação */}
          <SecaoCard id="sec-18" titulo="18. Observação" badge="existente">
            <CampoTextarea label="Texto livre / observações" value={orc.texto_livre_proposta ?? ""}
              readonly={readonly} rows={3}
              onSave={(v) => salvarOrc("texto_livre_proposta", v)} placeholder="Observações finais…" />
          </SecaoCard>

          {/* 19. Contato Comercial — config, read-only */}
          <SecaoCard id="sec-19" titulo="19. Contato Comercial" badge="novo">
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div><div className="text-muted-foreground text-xs uppercase">Nome</div>{config?.contato_comercial_nome ?? "—"}</div>
              <div><div className="text-muted-foreground text-xs uppercase">Função</div>{config?.contato_comercial_funcao ?? "—"}</div>
              <div><div className="text-muted-foreground text-xs uppercase">Fone</div>{config?.contato_comercial_fone ?? "—"}</div>
              <div><div className="text-muted-foreground text-xs uppercase">E-mail</div>{config?.contato_comercial_email ?? "—"}</div>
            </div>
            <Link to="/parametros" className="text-primary text-xs hover:underline">→ editar em Parâmetros</Link>
          </SecaoCard>
        </div>
```

- [ ] **Step 4: Preencher o índice interno**

Substitua o bloco `<nav className="sticky top-4 hidden lg:block">{/* ÍNDICE entra na Task 5 */}</nav>` por:

```tsx
        <nav className="sticky top-4 hidden lg:block">
          <div className="text-muted-foreground mb-2 text-[0.625rem] font-semibold uppercase">Seções</div>
          <ul className="space-y-0.5 text-xs">
            {INDICE.map((label, i) => (
              <li key={i}>
                <a href={`#sec-${i + 1}`} className="text-muted-foreground hover:text-foreground block rounded px-2 py-1 hover:bg-secondary">
                  {label}
                </a>
              </li>
            ))}
          </ul>
        </nav>
```

- [ ] **Step 5: Verificar typecheck + build**

Run: `cd "g:/Meu Drive/ansvorc/frontend" && npm run typecheck`
Expected: sem erros.
Run: `cd "g:/Meu Drive/ansvorc/frontend" && npm run build`
Expected: build conclui sem erro.

- [ ] **Step 6: Check manual no browser**

Suba o backend + frontend (ver README do projeto; tipicamente `py -m uvicorn backend.main:app` + `npm run dev`). Abra um orçamento existente, navegue para `/orcamentos/<id>/proposta/editar`. Verifique:
- As 19 seções renderizam; índice à direita salta para a seção ao clicar.
- Editar "Escopo" e sair do campo → toast só se erro; recarregar a página mantém o valor (salvou).
- Seção 7: descrição com borda de acento editável; qtd/preços cinza; sem item calculado mostra o aviso.
- Seções 11/12/19 mostram dados da config + link "→ editar em Parâmetros".
- Garantia: digitar 5 e 60 → texto "Retenção de 5%, com devolução em 60 dias…".

- [ ] **Step 7: Commit**

```bash
git add frontend/app/routes/proposta.editar.$id.tsx
git commit -m "feat(proposta): editor com as 19 seções FOR-077 + índice (F2)"
```

---

## Task 6: Botão "Editar Proposta" no orçamento

**Files:**
- Modify: `frontend/app/routes/orcamentos.$id.tsx` (header de ações, ~linha 246-251)

- [ ] **Step 1: Adicionar o botão**

Em `frontend/app/routes/orcamentos.$id.tsx`, no header de ações, logo após o botão existente que linka para `/orcamentos/${orcId}/proposta` (o `<Button asChild size="sm" variant="ghost">` com `<FileTextIcon /> Proposta`), adicione um segundo botão:

```tsx
          <Button asChild size="sm" variant="ghost">
            <Link to={`/orcamentos/${orcId}/proposta/editar`}>
              <PencilSimpleIcon className="size-4" /> Editar Proposta
            </Link>
          </Button>
```

E adicione `PencilSimpleIcon` ao import de `@phosphor-icons/react` no topo do arquivo (junto de `FileTextIcon`, etc.):

```tsx
import {
  ArrowLeftIcon,
  CalculatorIcon,
  ArrowsClockwiseIcon,
  TrashIcon,
  PlusIcon,
  FileTextIcon,
  PencilSimpleIcon,
} from "@phosphor-icons/react"
```

- [ ] **Step 2: Verificar typecheck**

Run: `cd "g:/Meu Drive/ansvorc/frontend" && npm run typecheck`
Expected: sem erros.

- [ ] **Step 3: Commit**

```bash
git add frontend/app/routes/orcamentos.$id.tsx
git commit -m "feat(proposta): botão Editar Proposta no orçamento (F2)"
```

---

## Task 7: Aba Empresa — expandir para 17 campos

**Files:**
- Modify: `frontend/app/routes/parametros.tsx` (componente `EmpresaConfig`, ~linha 149-243)

- [ ] **Step 1: Reescrever o componente `EmpresaConfig`**

Substitua TODO o componente `EmpresaConfig` (de `function EmpresaConfig() {` até o seu `}` de fechamento, antes de `export default function Parametros()`) por uma versão com os 17 campos + save único. Mantém o upload de logo. Converte string vazia → `null` ao salvar (exceto `nome_empresa`, obrigatório). `Textarea`/`Card`/`Label`/`Input`/`Button` já importados no arquivo? `Textarea` NÃO está — adicione ao topo: `import { Textarea } from "~/components/ui/textarea"`.

```tsx
function EmpresaConfig() {
  const [cfg, setCfg] = useState<any>(null)
  const [f, setF] = useState<Record<string, string>>({})
  const [saving, setSaving] = useState(false)

  const CAMPOS_TEXTO = [
    "nome_empresa", "cnpj",
    "diretor_nome", "diretor_funcao", "diretor_cpf", "diretor_telefone", "diretor_email",
    "contato_comercial_nome", "contato_comercial_funcao", "contato_comercial_fone", "contato_comercial_email",
    "banco", "agencia", "conta_corrente",
    "declaracoes_padrao", "clausula_tributaria_padrao", "reajustamento_padrao",
    "garantia_retencao_padrao_pct", "garantia_devolucao_padrao_dias",
  ]

  async function load() {
    try {
      const c = await configApi.get()
      setCfg(c)
      const init: Record<string, string> = {}
      for (const k of CAMPOS_TEXTO) init[k] = c[k] != null ? String(c[k]) : ""
      setF(init)
    } catch (e: any) {
      toast.error(e.message)
    }
  }
  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    setF((s) => ({ ...s, [k]: e.target.value }))

  async function salvar() {
    if (!f.nome_empresa?.trim()) {
      toast.error("Nome da empresa é obrigatório.")
      return
    }
    setSaving(true)
    try {
      const payload: Record<string, any> = {}
      for (const k of CAMPOS_TEXTO) {
        const v = f[k]?.trim() ?? ""
        if (k === "nome_empresa") payload[k] = v
        else if (k === "garantia_retencao_padrao_pct") payload[k] = v === "" ? null : v
        else if (k === "garantia_devolucao_padrao_dias") payload[k] = v === "" ? null : Number(v)
        else payload[k] = v === "" ? null : v
      }
      const c = await configApi.update(payload)
      setCfg(c)
      toast.success("Configurações da empresa atualizadas")
    } catch (e: any) {
      toast.error(`Erro: ${e.message}`)
    } finally {
      setSaving(false)
    }
  }

  async function enviarLogo(file: File) {
    try {
      const c = await configApi.uploadLogo(file)
      setCfg(c)
      toast.success("Logo atualizado")
    } catch (e: any) {
      toast.error(`Erro: ${e.message}`)
    }
  }

  const campoT = (k: string, label: string, ph?: string) => (
    <div className="flex flex-col gap-1.5">
      <Label className="text-muted-foreground text-xs uppercase">{label}</Label>
      <Input value={f[k] ?? ""} onChange={set(k)} placeholder={ph} />
    </div>
  )
  const campoArea = (k: string, label: string) => (
    <div className="flex flex-col gap-1.5">
      <Label className="text-muted-foreground text-xs uppercase">{label}</Label>
      <Textarea value={f[k] ?? ""} onChange={set(k)} rows={4} />
    </div>
  )

  return (
    <div className="max-w-3xl space-y-4">
      <div className="flex justify-end">
        <Button size="sm" onClick={salvar} disabled={saving}>
          {saving ? "Salvando…" : "Salvar"}
        </Button>
      </div>

      <Card className="space-y-4 p-6">
        <Label className="text-primary text-xs font-bold uppercase">Dados da Empresa</Label>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {campoT("nome_empresa", "Nome da Empresa", "ALTA NOROESTE")}
          {campoT("cnpj", "CNPJ", "20.945.724/0001-15")}
        </div>
        <div className="flex flex-col gap-2 border-t pt-4">
          <Label className="text-muted-foreground text-xs uppercase">Logotipo (PNG, máx 500KB)</Label>
          {cfg?.logo_path && <img src={cfg.logo_path} alt="logo" className="h-12 max-w-[200px] object-contain" />}
          <Input type="file" accept="image/png" onChange={(e) => { const x = e.target.files?.[0]; if (x) enviarLogo(x) }} />
        </div>
      </Card>

      <Card className="space-y-4 p-6">
        <Label className="text-primary text-xs font-bold uppercase">Representante Legal</Label>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {campoT("diretor_nome", "Nome")}
          {campoT("diretor_funcao", "Função", "Diretor Comercial")}
          {campoT("diretor_cpf", "CPF")}
          {campoT("diretor_telefone", "Telefone")}
          {campoT("diretor_email", "E-mail")}
        </div>
      </Card>

      <Card className="space-y-4 p-6">
        <Label className="text-primary text-xs font-bold uppercase">Contato Comercial</Label>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {campoT("contato_comercial_nome", "Nome")}
          {campoT("contato_comercial_funcao", "Função", "Comercial")}
          {campoT("contato_comercial_fone", "Fone")}
          {campoT("contato_comercial_email", "E-mail")}
        </div>
      </Card>

      <Card className="space-y-4 p-6">
        <Label className="text-primary text-xs font-bold uppercase">Dados Bancários</Label>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          {campoT("banco", "Banco", "Bradesco")}
          {campoT("agencia", "Agência", "0110")}
          {campoT("conta_corrente", "Conta Corrente", "0287852-6")}
        </div>
      </Card>

      <Card className="space-y-4 p-6">
        <Label className="text-primary text-xs font-bold uppercase">Textos Padrão</Label>
        {campoArea("declaracoes_padrao", "Declarações padrão (bullets legais)")}
        {campoArea("clausula_tributaria_padrao", "Cláusula tributária padrão (IBS/CBS)")}
        {campoArea("reajustamento_padrao", "Reajustamento padrão (IPCA/IGPM)")}
        <div className="grid grid-cols-2 gap-3">
          {campoT("garantia_retencao_padrao_pct", "Retenção padrão (%)", "5")}
          {campoT("garantia_devolucao_padrao_dias", "Devolução padrão (dias)", "60")}
        </div>
      </Card>
    </div>
  )
}
```

- [ ] **Step 2: Verificar typecheck + build**

Run: `cd "g:/Meu Drive/ansvorc/frontend" && npm run typecheck`
Expected: sem erros.
Run: `cd "g:/Meu Drive/ansvorc/frontend" && npm run build`
Expected: build conclui.

- [ ] **Step 3: Check manual no browser**

Abra `/parametros` → aba Empresa. Verifique: 5 cards (Dados / Representante / Contato / Bancários / Textos Padrão), upload de logo funciona, botão Salvar persiste (recarregar mantém), limpar um campo (não nome_empresa) salva como vazio, limpar nome_empresa → toast de erro e não salva.

- [ ] **Step 4: Commit**

```bash
git add frontend/app/routes/parametros.tsx
git commit -m "feat(config): aba Empresa com 17 campos do ConfigSistema (F2)"
```

---

## Task 8: Verificação final + handoff

- [ ] **Step 1: Typecheck + build limpos**

Run: `cd "g:/Meu Drive/ansvorc/frontend" && npm run typecheck && npm run build`
Expected: ambos sem erro.

- [ ] **Step 2: Atualizar handoff**

Em `docs/superpowers/HANDOFF-proposta-for077.md`, marque F2 como concluída e aponte F3 (documento + PDF) como próxima. Atualize a linha de fases e a seção "Próximo passo concreto".

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/HANDOFF-proposta-for077.md
git commit -m "docs: handoff FOR-077 — F2 editor concluída, próxima F3 documento+PDF"
```

---

## Self-Review (cobertura do spec)

| Requisito do spec | Task |
|---|---|
| API getProposta + patchDescricaoItem | Task 1 |
| Editor rota separada `/orcamentos/:id/proposta/editar` | Task 4 |
| Layout A (cards + índice interno) | Task 4 (esqueleto) + Task 5 (índice) |
| Auto-save onBlur (orçamento + item) | Task 3 (componentes) + Task 5 (wiring) |
| 19 seções com mapeamento campo→fonte→editável | Task 5 |
| Seção 7: só descrição editável, preços read-only, aviso sem cálculo | Task 5 |
| Fallback `*_padrao` como placeholder | Task 3 (`placeholderFallback`) + Task 5 (seções 4/8/14/15/6/9/16) |
| Garantia: texto auto + normalização pct | Task 5 (`garTexto`) |
| Seções config 11/12/19 read-only + link Parâmetros | Task 5 |
| Read-only por status | Task 4 (`readonly`) + Task 5 |
| Botão "Editar Proposta" no orçamento | Task 6 |
| Aba Empresa 17 campos, save único, "" → null exceto nome_empresa | Task 7 |
| Upload de logo preservado | Task 7 |
| Sem testes de front → typecheck+build+manual | todas as tasks |

**Desvios/notas:**
- `SecaoCard`/`CampoTexto`/`CampoTextarea` em arquivos próprios (`components/`) em vez de inline no editor — melhora foco do arquivo e segue o padrão de `components/` do projeto. (Spec dizia "dentro do arquivo"; este desvio é uma melhoria de organização, mesma funcionalidade.)
- Verificação manual é obrigatória (Tasks 5 e 7) porque não há testes automatizados de front — é a única forma de validar comportamento de runtime.
