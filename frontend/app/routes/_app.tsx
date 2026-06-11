import { useEffect, useState } from "react"
import { Outlet, useLocation, useNavigate } from "react-router"
import { MoonIcon, SunIcon, SignOutIcon } from "@phosphor-icons/react"

import { AppSidebar } from "~/components/app-sidebar"
import { Button } from "~/components/ui/button"
import { Separator } from "~/components/ui/separator"
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "~/components/ui/sidebar"
import { auth } from "~/lib/api"
import { useDarkMode } from "~/lib/theme"

const TITLES: { prefix: string; title: string }[] = [
  { prefix: "/dashboard", title: "Dashboard" },
  { prefix: "/bds/rh", title: "Recursos Humanos" },
  { prefix: "/bds/bdi", title: "Parâmetros de BDI" },
  { prefix: "/bds/epi", title: "EPIs" },
  { prefix: "/bds/ferramental", title: "Ferramental" },
  { prefix: "/bds/frotas", title: "Frotas" },
  { prefix: "/bds/materiais", title: "Materiais" },
  { prefix: "/bds/estrutura", title: "Estrutura Operacional" },
  { prefix: "/bds/despesas", title: "Despesas" },
  { prefix: "/fichas/equipes", title: "Fichas de Equipe" },
  { prefix: "/fichas/produtos", title: "Ficha Técnica" },
  { prefix: "/fichas/servicos", title: "Fichas de Serviço" },
  { prefix: "/orcamentos", title: "Orçamentos" },
  { prefix: "/clientes", title: "Clientes" },
  { prefix: "/produtos-componentes", title: "Produtos e Componentes" },
  { prefix: "/parametros", title: "Parâmetros" },
]

function pageTitle(path: string): string {
  const match = TITLES.filter((t) => path.startsWith(t.prefix)).sort(
    (a, b) => b.prefix.length - a.prefix.length
  )[0]
  return match?.title ?? "orcOS"
}

export default function AppLayout() {
  const location = useLocation()
  const navigate = useNavigate()
  const [isDark, toggleDark] = useDarkMode()
  const [authed, setAuthed] = useState<boolean | null>(null)

  useEffect(() => {
    if (!auth.isLoggedIn()) {
      navigate("/login", { replace: true })
    } else {
      setAuthed(true)
    }
  }, [navigate])

  if (!authed) return null

  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset>
        <header className="bg-background sticky top-0 z-10 flex h-14 shrink-0 items-center gap-2 border-b px-4">
          <SidebarTrigger className="-ml-1" />
          <Separator orientation="vertical" className="mr-1 data-[orientation=vertical]:h-4" />
          <h1 className="text-sm font-semibold">{pageTitle(location.pathname)}</h1>
          <div className="ml-auto flex items-center gap-1">
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleDark}
              aria-label={isDark ? "Modo claro" : "Modo escuro"}
              title={isDark ? "Modo claro" : "Modo escuro"}
            >
              {isDark ? <SunIcon className="size-4" /> : <MoonIcon className="size-4" />}
            </Button>
            <Button variant="ghost" size="sm" onClick={() => auth.logout()}>
              <SignOutIcon className="size-4" />
              Sair
            </Button>
          </div>
        </header>
        <main className="bg-background flex-1 p-4 md:p-6">
          <Outlet />
        </main>
      </SidebarInset>
    </SidebarProvider>
  )
}
