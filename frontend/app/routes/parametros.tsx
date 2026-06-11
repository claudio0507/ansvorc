import { useEffect, useState } from "react"
import { toast } from "sonner"
import { PlusIcon, TrashIcon } from "@phosphor-icons/react"

import { PageHeader } from "~/components/page-header"
import { Badge } from "~/components/ui/badge"
import { Button } from "~/components/ui/button"
import { Card } from "~/components/ui/card"
import { Input } from "~/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "~/components/ui/tabs"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "~/components/ui/table"
import { Label } from "~/components/ui/label"
import { configApi, orcamentistaApi, parametroApi, unidadeApi } from "~/lib/api"

interface ListaSimplesProps {
  load: () => Promise<any[]>
  create: (b: any) => Promise<any>
  del: (id: number) => Promise<any>
  campos: { key: string; label: string; placeholder?: string }[]
  colunas: { key: string; label: string }[]
}

function CrudSimples({ load, create, del, campos, colunas }: ListaSimplesProps) {
  const [rows, setRows] = useState<any[] | null>(null)
  const [form, setForm] = useState<Record<string, string>>({})
  const [saving, setSaving] = useState(false)

  async function refresh() {
    setRows(null)
    try {
      setRows(await load())
    } catch (e: any) {
      toast.error(e.message)
    }
  }
  useEffect(() => {
    refresh()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function adicionar(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    try {
      await create(form)
      setForm({})
      toast.success("Registro adicionado")
      refresh()
    } catch (err: any) {
      toast.error(`Erro: ${err.message}`)
    } finally {
      setSaving(false)
    }
  }

  async function remover(id: number) {
    if (!confirm("Excluir este registro?")) return
    try {
      await del(id)
      refresh()
    } catch (err: any) {
      toast.error(`Erro: ${err.message}`)
    }
  }

  return (
    <>
      <form onSubmit={adicionar} className="mb-4 flex flex-wrap items-end gap-3">
        {campos.map((c) => (
          <div key={c.key} className="flex flex-col gap-1.5">
            <label className="text-muted-foreground text-xs font-medium uppercase">{c.label}</label>
            <Input
              className="w-40"
              placeholder={c.placeholder}
              value={form[c.key] ?? ""}
              onChange={(e) => setForm((s) => ({ ...s, [c.key]: e.target.value }))}
              required
            />
          </div>
        ))}
        <Button type="submit" size="sm" disabled={saving}>
          <PlusIcon className="size-4" /> Adicionar
        </Button>
      </form>

      <Card className="overflow-x-auto py-0">
        <Table>
          <TableHeader>
            <TableRow>
              {colunas.map((c) => (
                <TableHead key={c.key}>{c.label}</TableHead>
              ))}
              <TableHead>Status</TableHead>
              <TableHead className="w-10"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows === null ? (
              <TableRow><TableCell colSpan={colunas.length + 2} className="text-muted-foreground py-6 text-center">Carregando…</TableCell></TableRow>
            ) : rows.length === 0 ? (
              <TableRow><TableCell colSpan={colunas.length + 2} className="text-muted-foreground py-6 text-center">Nenhum registro.</TableCell></TableRow>
            ) : (
              rows.map((r) => (
                <TableRow key={r.id}>
                  {colunas.map((c) => (
                    <TableCell key={c.key}>{r[c.key]}</TableCell>
                  ))}
                  <TableCell>
                    {r.ativo ? <Badge variant="success">ATIVO</Badge> : <Badge variant="secondary">INATIVO</Badge>}
                  </TableCell>
                  <TableCell className="text-right">
                    <Button variant="ghost" size="icon" onClick={() => remover(r.id)}>
                      <TrashIcon className="text-destructive size-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </Card>
    </>
  )
}

function EmpresaConfig() {
  const [cfg, setCfg] = useState<any>(null)
  const [nome, setNome] = useState("")
  const [saving, setSaving] = useState(false)

  async function load() {
    try {
      const c = await configApi.get()
      setCfg(c)
      setNome(c.nome_empresa ?? "")
    } catch (e: any) {
      toast.error(e.message)
    }
  }
  useEffect(() => {
    load()
  }, [])

  async function salvarNome() {
    setSaving(true)
    try {
      const c = await configApi.update({ nome_empresa: nome })
      setCfg(c)
      toast.success("Nome da empresa atualizado")
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

  return (
    <Card className="max-w-xl space-y-5 p-6">
      <div className="flex flex-col gap-2">
        <Label>Nome da Empresa (subtítulo do orcOS)</Label>
        <div className="flex gap-2">
          <Input value={nome} onChange={(e) => setNome(e.target.value)} placeholder="ALTA NOROESTE" />
          <Button size="sm" onClick={salvarNome} disabled={saving}>
            Salvar
          </Button>
        </div>
      </div>

      <div className="flex flex-col gap-2 border-t pt-5">
        <Label>Logotipo (PNG, máx 500KB, ~400×120)</Label>
        {cfg?.logo_path && (
          <img src={cfg.logo_path} alt="logo" className="h-12 max-w-[200px] object-contain" />
        )}
        <Input
          type="file"
          accept="image/png"
          onChange={(e) => {
            const f = e.target.files?.[0]
            if (f) enviarLogo(f)
          }}
        />
        <p className="text-muted-foreground text-xs">Exibido na proposta, login e sidebar.</p>
      </div>
    </Card>
  )
}

export default function Parametros() {
  return (
    <>
      <PageHeader title="Parâmetros" subtitle="Segmentos, unidades, orçamentistas e identidade visual" />
      <Tabs defaultValue="seguimentos">
        <TabsList>
          <TabsTrigger value="seguimentos">Segmentos</TabsTrigger>
          <TabsTrigger value="tipos">Tipos de Estrutura</TabsTrigger>
          <TabsTrigger value="unidades">Unidades de Medida</TabsTrigger>
          <TabsTrigger value="orcamentistas">Orçamentistas</TabsTrigger>
          <TabsTrigger value="empresa">Empresa</TabsTrigger>
        </TabsList>

        <TabsContent value="seguimentos" className="mt-4">
          <CrudSimples
            load={parametroApi.listSeguimentos}
            create={(b) => parametroApi.createSeguimento(b)}
            del={parametroApi.deleteSeguimento}
            campos={[{ key: "nome", label: "Nome", placeholder: "EPS" }]}
            colunas={[{ key: "nome", label: "Nome" }]}
          />
        </TabsContent>

        <TabsContent value="tipos" className="mt-4">
          <CrudSimples
            load={parametroApi.listTipos}
            create={(b) => parametroApi.createTipo(b)}
            del={parametroApi.deleteTipo}
            campos={[{ key: "nome", label: "Nome", placeholder: "Base_de_Apoio" }]}
            colunas={[{ key: "nome", label: "Nome" }]}
          />
        </TabsContent>

        <TabsContent value="unidades" className="mt-4">
          <CrudSimples
            load={unidadeApi.list}
            create={(b) => unidadeApi.create(b)}
            del={unidadeApi.delete}
            campos={[
              { key: "sigla", label: "Sigla", placeholder: "m²" },
              { key: "nome", label: "Nome", placeholder: "Metro Quadrado" },
            ]}
            colunas={[
              { key: "sigla", label: "Sigla" },
              { key: "nome", label: "Nome" },
            ]}
          />
        </TabsContent>

        <TabsContent value="orcamentistas" className="mt-4">
          <CrudSimples
            load={orcamentistaApi.list}
            create={(b) => orcamentistaApi.create(b)}
            del={orcamentistaApi.delete}
            campos={[
              { key: "nome_completo", label: "Nome Completo", placeholder: "João Silva" },
              { key: "funcao", label: "Função", placeholder: "Orçamentista Sênior" },
              { key: "email", label: "E-mail", placeholder: "joao@empresa.com" },
              { key: "telefone", label: "Telefone", placeholder: "(41) 9 9999-9999" },
            ]}
            colunas={[
              { key: "nome_completo", label: "Nome" },
              { key: "funcao", label: "Função" },
              { key: "email", label: "E-mail" },
              { key: "telefone", label: "Telefone" },
            ]}
          />
        </TabsContent>

        <TabsContent value="empresa" className="mt-4">
          <EmpresaConfig />
        </TabsContent>
      </Tabs>
    </>
  )
}
