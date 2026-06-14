import { useEffect, useState } from "react"
import { toast } from "sonner"
import { PencilSimpleIcon, PlusIcon, TrashIcon } from "@phosphor-icons/react"

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
import { Textarea } from "~/components/ui/textarea"
import { configApi, orcamentistaApi, parametroApi, unidadeApi } from "~/lib/api"

interface ListaSimplesProps {
  load: () => Promise<any[]>
  create: (b: any) => Promise<any>
  update: (id: number, b: any) => Promise<any>
  del: (id: number) => Promise<any>
  campos: { key: string; label: string; placeholder?: string }[]
  colunas: { key: string; label: string }[]
}

function CrudSimples({ load, create, update, del, campos, colunas }: ListaSimplesProps) {
  const [rows, setRows] = useState<any[] | null>(null)
  const [form, setForm] = useState<Record<string, string>>({})
  const [editId, setEditId] = useState<number | null>(null)
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
      if (editId !== null) {
        await update(editId, form)
        setEditId(null)
        toast.success("Registro atualizado")
      } else {
        await create(form)
        toast.success("Registro adicionado")
      }
      setForm({})
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
          <PlusIcon className="size-4" /> {editId !== null ? "Atualizar" : "Adicionar"}
        </Button>
        {editId !== null && (
          <Button type="button" size="sm" variant="ghost" onClick={() => { setEditId(null); setForm({}) }}>
            Cancelar
          </Button>
        )}
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
                    <Button variant="ghost" size="icon" onClick={() => { setEditId(r.id); setForm(campos.reduce((acc: any, c: any) => ({ ...acc, [c.key]: r[c.key] ?? "" }), {})) }}>
                      <PencilSimpleIcon className="text-muted-foreground size-4" />
                    </Button>
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

// Campos do ConfigSistema editáveis na aba Empresa (espelham ConfigSistemaUpdate).
const CAMPOS_EMPRESA = [
  "nome_empresa", "cnpj",
  "diretor_nome", "diretor_funcao", "diretor_cpf", "diretor_telefone", "diretor_email",
  "contato_comercial_nome", "contato_comercial_funcao", "contato_comercial_fone", "contato_comercial_email",
  "banco", "agencia", "conta_corrente",
  "declaracoes_padrao", "clausula_tributaria_padrao", "reajustamento_padrao",
  "garantia_retencao_padrao_pct", "garantia_devolucao_padrao_dias",
]

// Monta o estado do formulário a partir da config (campos null viram "").
function formDaConfig(c: any): Record<string, string> {
  const init: Record<string, string> = {}
  for (const k of CAMPOS_EMPRESA) init[k] = c[k] != null ? String(c[k]) : ""
  return init
}

function EmpresaConfig() {
  const [cfg, setCfg] = useState<any>(null)
  const [f, setF] = useState<Record<string, string>>({})
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    configApi
      .get()
      .then((c) => {
        setCfg(c)
        setF(formDaConfig(c))
      })
      .catch((e: any) => toast.error(e.message))
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
      for (const k of CAMPOS_EMPRESA) {
        const v = f[k]?.trim() ?? ""
        if (k === "nome_empresa") payload[k] = v
        else if (k === "garantia_retencao_padrao_pct") payload[k] = v === "" ? null : v
        else if (k === "garantia_devolucao_padrao_dias") payload[k] = v === "" ? null : Number(v)
        else payload[k] = v === "" ? null : v
      }
      const c = await configApi.update(payload)
      setCfg(c)
      setF(formDaConfig(c)) // re-sincroniza com o que o backend gravou (normalizações)
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
            update={(id, b) => parametroApi.updateSeguimento(id, b)}
            del={parametroApi.deleteSeguimento}
            campos={[{ key: "nome", label: "Nome", placeholder: "EPS" }]}
            colunas={[{ key: "nome", label: "Nome" }]}
          />
        </TabsContent>

        <TabsContent value="tipos" className="mt-4">
          <CrudSimples
            load={parametroApi.listTipos}
            create={(b) => parametroApi.createTipo(b)}
            update={(id, b) => parametroApi.updateTipo(id, b)}
            del={parametroApi.deleteTipo}
            campos={[{ key: "nome", label: "Nome", placeholder: "Base_de_Apoio" }]}
            colunas={[{ key: "nome", label: "Nome" }]}
          />
        </TabsContent>

        <TabsContent value="unidades" className="mt-4">
          <CrudSimples
            load={unidadeApi.list}
            create={(b) => unidadeApi.create(b)}
            update={(id, b) => unidadeApi.update(id, b)}
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
            update={(id, b) => orcamentistaApi.update(id, b)}
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
