import { NavLink } from "react-router"
import {
  HouseIcon,
  UsersThreeIcon,
  ShieldCheckIcon,
  TruckIcon,
  PackageIcon,
  BuildingsIcon,
  ReceiptIcon,
  UsersIcon,
  StackIcon,
  WrenchIcon,
  FileTextIcon,
  PercentIcon,
  CubeIcon,
  SlidersHorizontalIcon,
  ChartBarIcon,
  type Icon,
} from "@phosphor-icons/react"

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "~/components/ui/sidebar"
import { podeVer } from "~/lib/rbac"
import { auth } from "~/lib/api"

interface NavItem {
  to: string
  label: string
  icon: Icon
}

interface NavSection {
  label: string
  show: boolean
  items: NavItem[]
}

function buildSections(): NavSection[] {
  return [
    {
      label: "Principal",
      show: true,
      items: [{ to: "/dashboard", label: "Dashboard", icon: HouseIcon }],
    },
    {
      label: "Bancos de Dados",
      show: podeVer("bds"),
      items: [
        { to: "/bds/bdi", label: "BDI", icon: PercentIcon },
        { to: "/bds/rh", label: "Recursos Humanos", icon: UsersThreeIcon },
        { to: "/bds/epi", label: "EPIs", icon: ShieldCheckIcon },
        { to: "/bds/ferramental", label: "Ferramental", icon: WrenchIcon },
        { to: "/bds/frotas", label: "Frotas", icon: TruckIcon },
        { to: "/bds/materiais", label: "Materiais", icon: PackageIcon },
        { to: "/bds/estrutura", label: "Estrutura Op.", icon: BuildingsIcon },
        { to: "/bds/despesas", label: "Despesas", icon: ReceiptIcon },
      ],
    },
    {
      label: "Fichas Técnicas",
      show: podeVer("fichas"),
      items: [
        { to: "/fichas/equipes", label: "Equipes", icon: UsersIcon },
        { to: "/fichas/produtos", label: "Ficha Técnica", icon: StackIcon },
        { to: "/fichas/servicos", label: "Serviços", icon: WrenchIcon },
        { to: "/produtos-componentes", label: "Produtos/Componentes", icon: CubeIcon },
        { to: "/parametros", label: "Parâmetros", icon: SlidersHorizontalIcon },
      ],
    },
    {
      label: "Orçamentação",
      show: podeVer("orcamentos") || podeVer("clientes"),
      items: [
        ...(podeVer("orcamentos")
          ? [{ to: "/orcamentos", label: "Orçamentos", icon: FileTextIcon }]
          : []),
        ...(podeVer("clientes")
          ? [{ to: "/clientes", label: "Clientes", icon: UsersThreeIcon }]
          : []),
        { to: "/bi-precos", label: "BI — Preços", icon: ChartBarIcon },
      ],
    },
  ]
}

function LogoMark() {
  return (
    <svg viewBox="0 0 24 24" className="size-5 fill-current">
      <path d="M12 3 A9 9 0 1 1 4 8 L12 12 Z" />
      <path d="M12 12 L4 8 A9 9 0 0 1 12 3 Z" transform="translate(1.5, -1.5)" />
    </svg>
  )
}

export function AppSidebar() {
  const sections = buildSections().filter((s) => s.show && s.items.length > 0)
  const user = auth.getUser()
  const inicial = (user?.nome ?? user?.email ?? "U")[0]?.toUpperCase() ?? "U"

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader>
        <div className="flex items-center gap-2 px-1 py-1.5">
          <div className="bg-sidebar-primary text-sidebar-primary-foreground flex size-8 shrink-0 items-center justify-center">
            <LogoMark />
          </div>
          <div className="flex flex-col leading-none group-data-[collapsible=icon]:hidden">
            <span className="text-base font-semibold tracking-tight">orcOS</span>
            <span className="text-muted-foreground text-[0.625rem] font-medium tracking-[0.1em] uppercase">
              ALTA NOROESTE
            </span>
          </div>
        </div>
      </SidebarHeader>

      <SidebarContent>
        {sections.map((section) => (
          <SidebarGroup key={section.label}>
            <SidebarGroupLabel>{section.label}</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {section.items.map((item) => (
                  <SidebarMenuItem key={item.to}>
                    <NavLink to={item.to}>
                      {({ isActive }) => (
                        <SidebarMenuButton isActive={isActive} tooltip={item.label}>
                          <item.icon weight={isActive ? "fill" : "regular"} />
                          <span>{item.label}</span>
                        </SidebarMenuButton>
                      )}
                    </NavLink>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        ))}
      </SidebarContent>

      <SidebarFooter>
        <div className="flex items-center gap-2 px-1 py-1.5">
          <div className="bg-muted text-foreground flex size-8 shrink-0 items-center justify-center text-sm font-semibold">
            {inicial}
          </div>
          <div className="min-w-0 group-data-[collapsible=icon]:hidden">
            <div className="truncate text-sm font-medium">
              {user?.nome ?? user?.email ?? "Usuário"}
            </div>
            <div className="text-muted-foreground truncate text-xs capitalize">
              {user?.papel ?? "Operador"}
            </div>
          </div>
        </div>
      </SidebarFooter>
    </Sidebar>
  )
}
