/** RBAC da sidebar — port de _SIDEBAR_PAPEIS / _podeVer (app.js). */
import { auth } from "./api"

export type Secao = "bds" | "fichas" | "orcamentos" | "clientes"

const SIDEBAR_PAPEIS: Record<Secao, Set<string>> = {
  bds: new Set(["gestor_bd", "sponsor"]),
  fichas: new Set(["parametrizador", "sponsor"]),
  orcamentos: new Set(["orcamentista", "parametrizador", "sponsor"]),
  clientes: new Set(["orcamentista", "parametrizador", "gestor_bd", "sponsor"]),
}

export function podeVer(secao: Secao): boolean {
  const papel = auth.getUser()?.papel ?? ""
  return SIDEBAR_PAPEIS[secao]?.has(papel) ?? true
}
