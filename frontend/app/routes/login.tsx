import { useEffect, useState } from "react"
import { useNavigate } from "react-router"
import { toast } from "sonner"

import { Button } from "~/components/ui/button"
import { Input } from "~/components/ui/input"
import { Label } from "~/components/ui/label"
import { api, auth, type ApiError } from "~/lib/api"

function LogoMark() {
  return (
    <svg viewBox="0 0 24 24" className="size-7 fill-current">
      <path d="M12 2L2 7l10 5 10-5-10-5zm0 10L2 7v10l10 5 10-5V7l-10 5z" />
    </svg>
  )
}

export default function Login() {
  const navigate = useNavigate()
  const [email, setEmail] = useState("")
  const [senha, setSenha] = useState("")
  const [erro, setErro] = useState("")
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (auth.isLoggedIn()) navigate("/dashboard", { replace: true })
  }, [navigate])

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setErro("")
    if (!email.trim() || !senha) {
      setErro("Preencha e-mail e senha.")
      return
    }
    setLoading(true)
    try {
      const data = await api.post<{
        access_token: string
        refresh_token: string
        nome?: string
        papel?: string
        usuario_id?: number
      }>("/auth/login", { email: email.trim(), senha })
      auth.setTokens(data.access_token, data.refresh_token)
      auth.setUser({
        email: email.trim(),
        nome: data.nome,
        papel: data.papel,
        id: data.usuario_id,
      })
      toast.success("Bem-vindo ao orcOS!")
      navigate("/dashboard", { replace: true })
    } catch (err) {
      const e = err as ApiError
      setErro(e.status === 401 ? "E-mail ou senha incorretos." : e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-muted flex min-h-svh items-center justify-center p-4">
      <div className="bg-card w-full max-w-sm border p-8 shadow-sm">
        <div className="mb-8 flex flex-col items-center text-center">
          <div className="bg-primary text-primary-foreground mb-4 flex size-14 items-center justify-center">
            <LogoMark />
          </div>
          <h1 className="text-2xl font-bold tracking-tight">orcOS</h1>
          <p className="text-muted-foreground mt-0.5 text-xs font-medium tracking-[0.12em] uppercase">
            ALTA NOROESTE
          </p>
          <p className="text-muted-foreground mt-1 text-sm">ERP de Orçamentação Viária</p>
        </div>

        <form onSubmit={onSubmit} noValidate className="flex flex-col gap-4">
          <div className="flex flex-col gap-2">
            <Label htmlFor="login-email">E-mail</Label>
            <Input
              id="login-email"
              type="email"
              autoComplete="username"
              placeholder="seuemail@altanoroeste.com.br"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="flex flex-col gap-2">
            <Label htmlFor="login-password">Senha</Label>
            <Input
              id="login-password"
              type="password"
              autoComplete="current-password"
              placeholder="••••••••"
              value={senha}
              onChange={(e) => setSenha(e.target.value)}
              required
            />
          </div>

          {erro && (
            <p className="text-destructive bg-destructive/10 px-3 py-2 text-sm" role="alert">
              {erro}
            </p>
          )}

          <Button type="submit" className="mt-2 w-full" disabled={loading}>
            {loading ? "Entrando…" : "Entrar"}
          </Button>
        </form>

        <p className="text-muted-foreground/70 mt-6 text-center text-[0.625rem] tracking-wide">
          Desenvolvido por Viaxis Tech HUB
        </p>
      </div>
    </div>
  )
}
