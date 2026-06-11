import { type RouteConfig, index, route, layout } from "@react-router/dev/routes"

export default [
  index("routes/index.tsx"),
  route("login", "routes/login.tsx"),
  layout("routes/_app.tsx", [
    route("dashboard", "routes/dashboard.tsx"),
    route("bds/:tipo", "routes/bds.tsx"),
    route("fichas/:tipo", "routes/fichas.tsx"),
    route("orcamentos", "routes/orcamentos._index.tsx"),
    route("orcamentos/novo", "routes/orcamentos.novo.tsx"),
    route("orcamentos/:id", "routes/orcamentos.$id.tsx"),
    route("orcamentos/:id/proposta", "routes/proposta.tsx"),
    route("clientes", "routes/clientes.tsx"),
    route("produtos-componentes", "routes/produtos-componentes.tsx"),
    route("parametros", "routes/parametros.tsx"),
    route("bi-precos", "routes/bi-precos.tsx"),
  ]),
] satisfies RouteConfig
