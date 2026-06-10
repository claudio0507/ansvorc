/**
 * api.ts — Wrapper fetch() para o backend Sinalys em /api/v1
 * Port de frontend_legacy/js/api.js (comportamento 1:1).
 *
 * Access token: apenas em memória. Refresh token: localStorage.
 */

const BASE_URL = "/api/v1"
const REFRESH_KEY = "sinalys_refresh"
const USER_KEY = "sinalys_user"

let _accessToken: string | null = null

export interface SessionUser {
  id?: number
  email?: string
  nome?: string
  papel?: string
}

export const auth = {
  setTokens(accessToken: string, refreshToken: string) {
    _accessToken = accessToken
    localStorage.setItem(REFRESH_KEY, refreshToken)
  },
  getAccessToken() {
    return _accessToken
  },
  clearAccessToken() {
    _accessToken = null
  },
  hasSession() {
    return !!localStorage.getItem(REFRESH_KEY)
  },
  setUser(user: SessionUser) {
    localStorage.setItem(USER_KEY, JSON.stringify(user))
  },
  getUser(): SessionUser | null {
    const raw = localStorage.getItem(USER_KEY)
    try {
      return raw ? (JSON.parse(raw) as SessionUser) : null
    } catch {
      return null
    }
  },
  clearUser() {
    localStorage.removeItem(USER_KEY)
  },
  isLoggedIn() {
    return !!_accessToken || !!localStorage.getItem(REFRESH_KEY)
  },
  logout() {
    _accessToken = null
    localStorage.removeItem(REFRESH_KEY)
    localStorage.removeItem(USER_KEY)
    window.location.assign("/login")
  },
}

async function _refreshAccessToken(): Promise<string | null> {
  const refresh = localStorage.getItem(REFRESH_KEY)
  if (!refresh) return null

  const res = await fetch(`${BASE_URL}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refresh }),
  })

  if (!res.ok) {
    auth.logout()
    return null
  }

  const data = await res.json()
  _accessToken = data.access_token
  if (data.refresh_token) localStorage.setItem(REFRESH_KEY, data.refresh_token)
  return _accessToken
}

export interface ApiError extends Error {
  status?: number
  data?: unknown
}

async function request<T = unknown>(
  method: string,
  path: string,
  body: unknown = null,
  _retry = true
): Promise<T> {
  if (!_accessToken) {
    await _refreshAccessToken()
  }

  const headers: Record<string, string> = { "Content-Type": "application/json" }
  if (_accessToken) headers["Authorization"] = `Bearer ${_accessToken}`

  const init: RequestInit = { method, headers }
  if (body !== null) init.body = JSON.stringify(body)

  const response = await fetch(`${BASE_URL}${path}`, init)

  if (response.status === 401 && _retry && localStorage.getItem(REFRESH_KEY)) {
    const newToken = await _refreshAccessToken()
    if (newToken) return request<T>(method, path, body, false)
    return null as T
  }

  if (response.status === 204) return null as T

  const data = await response.json().catch(() => null)

  if (!response.ok) {
    const message = data?.detail ?? `Erro ${response.status}`
    const err: ApiError = new Error(
      typeof message === "string" ? message : JSON.stringify(message)
    )
    err.status = response.status
    err.data = data
    throw err
  }

  return data as T
}

export const api = {
  get: <T = any>(path: string) => request<T>("GET", path),
  post: <T = any>(path: string, body?: unknown) => request<T>("POST", path, body ?? null),
  put: <T = any>(path: string, body?: unknown) => request<T>("PUT", path, body ?? null),
  delete: <T = any>(path: string) => request<T>("DELETE", path),
  patch: <T = any>(path: string, body?: unknown) => request<T>("PATCH", path, body ?? null),
}

// ── Endpoints nomeados (espelham js/api.js) ──────────────────────────────

export const bdApi = {
  listBDI: () => api.get("/bd-bdi"),
  getBDI: (id: number) => api.get(`/bd-bdi/${id}`),
  createBDI: (body: unknown) => api.post("/bd-bdi", body),
  updateBDI: (id: number, b: unknown) => api.put(`/bd-bdi/${id}`, b),
  deleteBDI: (id: number) => api.delete(`/bd-bdi/${id}`),

  listRH: () => api.get("/bd-rh"),
  getRH: (id: number) => api.get(`/bd-rh/${id}`),
  createRH: (body: unknown) => api.post("/bd-rh", body),
  updateRH: (id: number, b: unknown) => api.put(`/bd-rh/${id}`, b),
  deleteRH: (id: number) => api.delete(`/bd-rh/${id}`),

  listEPI: () => api.get("/bd-epi"),
  getEPI: (id: number) => api.get(`/bd-epi/${id}`),
  createEPI: (body: unknown) => api.post("/bd-epi", body),
  updateEPI: (id: number, b: unknown) => api.put(`/bd-epi/${id}`, b),
  deleteEPI: (id: number) => api.delete(`/bd-epi/${id}`),

  listFerr: () => api.get("/bd-ferramental"),
  createFerr: (body: unknown) => api.post("/bd-ferramental", body),
  updateFerr: (id: number, b: unknown) => api.put(`/bd-ferramental/${id}`, b),
  deleteFerr: (id: number) => api.delete(`/bd-ferramental/${id}`),

  listFrotas: () => api.get("/bd-frotas"),
  createFrota: (body: unknown) => api.post("/bd-frotas", body),
  updateFrota: (id: number, b: unknown) => api.put(`/bd-frotas/${id}`, b),
  deleteFrota: (id: number) => api.delete(`/bd-frotas/${id}`),

  listMat: () => api.get("/bd-materiais"),
  createMat: (body: unknown) => api.post("/bd-materiais", body),
  updateMat: (id: number, b: unknown) => api.put(`/bd-materiais/${id}`, b),
  deleteMat: (id: number) => api.delete(`/bd-materiais/${id}`),

  listEst: () => api.get("/bd-estrutura"),
  createEst: (body: unknown) => api.post("/bd-estrutura", body),
  updateEst: (id: number, b: unknown) => api.put(`/bd-estrutura/${id}`, b),
  deleteEst: (id: number) => api.delete(`/bd-estrutura/${id}`),

  listDesp: () => api.get("/bd-despesas"),
  createDesp: (body: unknown) => api.post("/bd-despesas", body),
  updateDesp: (id: number, b: unknown) => api.put(`/bd-despesas/${id}`, b),
  deleteDesp: (id: number) => api.delete(`/bd-despesas/${id}`),
}

export const clienteApi = {
  list: () => api.get<any[]>("/clientes"),
  get: (id: number) => api.get(`/clientes/${id}`),
  create: (body: unknown) => api.post("/clientes", body),
  update: (id: number, b: unknown) => api.put(`/clientes/${id}`, b),
  delete: (id: number) => api.delete(`/clientes/${id}`),
}

export const orcamentoApi = {
  list: () => api.get<any[]>("/orcamentos"),
  get: (id: number) => api.get(`/orcamentos/${id}`),
  create: (body: unknown) => api.post<any>("/orcamentos", body),
  update: (id: number, b: unknown) => api.put<any>(`/orcamentos/${id}`, b),
  delete: (id: number) => api.delete(`/orcamentos/${id}`),
  listItens: (id: number) => api.get<any[]>(`/orcamentos/${id}/itens`),
  addItem: (id: number, b: unknown) => api.post<any>(`/orcamentos/${id}/itens`, b),
  updateItem: (id: number, iid: number, b: unknown) =>
    api.put<any>(`/orcamentos/${id}/itens/${iid}`, b),
  deleteItem: (id: number, iid: number) => api.delete(`/orcamentos/${id}/itens/${iid}`),
  calcular: (id: number) => api.post<any>(`/orcamentos/${id}/calcular`),
}

export const fichaApi = {
  listEquipes: () => api.get<any[]>("/fichas-equipe"),
  getEquipe: (id: number) => api.get(`/fichas-equipe/${id}`),
  createEquipe: (body: unknown) => api.post("/fichas-equipe", body),
  updateEquipe: (id: number, b: unknown) => api.put(`/fichas-equipe/${id}`, b),
  deleteEquipe: (id: number) => api.delete(`/fichas-equipe/${id}`),
  addItemEquipe: (id: number, b: unknown) => api.post(`/fichas-equipe/${id}/itens`, b),
  removeItemEquipe: (fId: number, iId: number) =>
    api.delete(`/fichas-equipe/${fId}/itens/${iId}`),

  listProdutos: () => api.get<any[]>("/fichas-produto"),
  getProduto: (id: number) => api.get(`/fichas-produto/${id}`),
  createProduto: (body: unknown) => api.post("/fichas-produto", body),
  updateProduto: (id: number, b: unknown) => api.put(`/fichas-produto/${id}`, b),
  deleteProduto: (id: number) => api.delete(`/fichas-produto/${id}`),
  addItemProduto: (id: number, b: unknown) => api.post(`/fichas-produto/${id}/itens`, b),

  listServicos: () => api.get<any[]>("/fichas-servico"),
  getServico: (id: number) => api.get(`/fichas-servico/${id}`),
  createServico: (body: unknown) => api.post("/fichas-servico", body),
  updateServico: (id: number, b: unknown) => api.put(`/fichas-servico/${id}`, b),
  deleteServico: (id: number) => api.delete(`/fichas-servico/${id}`),
  addRecurso: (id: number, b: unknown) => api.post(`/fichas-servico/${id}/recursos`, b),
  removeRecurso: (sId: number, rId: number) =>
    api.delete(`/fichas-servico/${sId}/recursos/${rId}`),
}
