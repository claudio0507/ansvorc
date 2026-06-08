/**
 * api.js — Wrapper fetch() para o backend Sinalys em /api/v1
 *
 * Uso:
 *   import { api } from './api.js';
 *   const rhs = await api.get('/bd-rh');
 *   const novo = await api.post('/bd-rh', { ...payload });
 */

const BASE_URL = '/api/v1';

// ── Token helpers ─────────────────────────────────────────────────────────────

export const auth = {
  /** Salva o JWT no localStorage (fase dev: apenas simula login). */
  setToken(token) { localStorage.setItem('sinalys_token', token); },
  getToken()      { return localStorage.getItem('sinalys_token'); },
  clearToken()    { localStorage.removeItem('sinalys_token'); },

  /** Dados do usuário logado (gravados no login). */
  setUser(user)   { localStorage.setItem('sinalys_user', JSON.stringify(user)); },
  getUser()       {
    const raw = localStorage.getItem('sinalys_user');
    try { return raw ? JSON.parse(raw) : null; } catch { return null; }
  },
  clearUser()     { localStorage.removeItem('sinalys_user'); },

  isLoggedIn()    { return !!auth.getToken(); },

  logout() {
    auth.clearToken();
    auth.clearUser();
    window.location.hash = '#/login';
  },
};

// ── Core fetch ────────────────────────────────────────────────────────────────

async function request(method, path, body = null) {
  const headers = { 'Content-Type': 'application/json' };

  const token = auth.getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const init = { method, headers };
  if (body !== null) init.body = JSON.stringify(body);

  const response = await fetch(`${BASE_URL}${path}`, init);

  // 204 No Content — sem body
  if (response.status === 204) return null;

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const message = data?.detail ?? `Erro ${response.status}`;
    const err = new Error(typeof message === 'string' ? message : JSON.stringify(message));
    err.status = response.status;
    err.data   = data;
    throw err;
  }

  return data;
}

// ── API pública ───────────────────────────────────────────────────────────────

export const api = {
  get:    (path)          => request('GET',    path),
  post:   (path, body)    => request('POST',   path, body),
  put:    (path, body)    => request('PUT',    path, body),
  delete: (path)          => request('DELETE', path),
  patch:  (path, body)    => request('PATCH',  path, body),
};

// ── Endpoints nomeados ────────────────────────────────────────────────────────

export const bdApi = {
  // BDI
  listBDI:    ()        => api.get('/bd-bdi'),
  getBDI:     (id)      => api.get(`/bd-bdi/${id}`),
  createBDI:  (body)    => api.post('/bd-bdi', body),
  updateBDI:  (id, b)   => api.put(`/bd-bdi/${id}`, b),
  deleteBDI:  (id)      => api.delete(`/bd-bdi/${id}`),

  // RH
  listRH:     ()        => api.get('/bd-rh'),
  getRH:      (id)      => api.get(`/bd-rh/${id}`),
  createRH:   (body)    => api.post('/bd-rh', body),
  updateRH:   (id, b)   => api.put(`/bd-rh/${id}`, b),
  deleteRH:   (id)      => api.delete(`/bd-rh/${id}`),

  // EPI
  listEPI:    ()        => api.get('/bd-epi'),
  getEPI:     (id)      => api.get(`/bd-epi/${id}`),
  createEPI:  (body)    => api.post('/bd-epi', body),
  updateEPI:  (id, b)   => api.put(`/bd-epi/${id}`, b),
  deleteEPI:  (id)      => api.delete(`/bd-epi/${id}`),

  // Ferramental
  listFerr:   ()        => api.get('/bd-ferramental'),
  createFerr: (body)    => api.post('/bd-ferramental', body),
  updateFerr: (id, b)   => api.put(`/bd-ferramental/${id}`, b),
  deleteFerr: (id)      => api.delete(`/bd-ferramental/${id}`),

  // Frotas
  listFrotas: ()        => api.get('/bd-frotas'),
  createFrota:(body)    => api.post('/bd-frotas', body),
  updateFrota:(id, b)   => api.put(`/bd-frotas/${id}`, b),
  deleteFrota:(id)      => api.delete(`/bd-frotas/${id}`),

  // Materiais
  listMat:    ()        => api.get('/bd-materiais'),
  createMat:  (body)    => api.post('/bd-materiais', body),
  updateMat:  (id, b)   => api.put(`/bd-materiais/${id}`, b),
  deleteMat:  (id)      => api.delete(`/bd-materiais/${id}`),

  // Estrutura Operacional
  listEst:    ()        => api.get('/bd-estrutura'),
  createEst:  (body)    => api.post('/bd-estrutura', body),
  updateEst:  (id, b)   => api.put(`/bd-estrutura/${id}`, b),
  deleteEst:  (id)      => api.delete(`/bd-estrutura/${id}`),

  // Despesas
  listDesp:   ()        => api.get('/bd-despesas'),
  createDesp: (body)    => api.post('/bd-despesas', body),
  updateDesp: (id, b)   => api.put(`/bd-despesas/${id}`, b),
  deleteDesp: (id)      => api.delete(`/bd-despesas/${id}`),
};

export const clienteApi = {
  list:   ()        => api.get('/clientes'),
  get:    (id)      => api.get(`/clientes/${id}`),
  create: (body)    => api.post('/clientes', body),
  update: (id, b)   => api.put(`/clientes/${id}`, b),
  delete: (id)      => api.delete(`/clientes/${id}`),
};

export const orcamentoApi = {
  list:        ()        => api.get('/orcamentos'),
  get:         (id)      => api.get(`/orcamentos/${id}`),
  create:      (body)    => api.post('/orcamentos', body),
  update:      (id, b)   => api.put(`/orcamentos/${id}`, b),
  delete:      (id)      => api.delete(`/orcamentos/${id}`),
  // Itens
  listItens:   (id)      => api.get(`/orcamentos/${id}/itens`),
  addItem:     (id, b)   => api.post(`/orcamentos/${id}/itens`, b),
  updateItem:  (id, iid, b) => api.put(`/orcamentos/${id}/itens/${iid}`, b),
  deleteItem:  (id, iid) => api.delete(`/orcamentos/${id}/itens/${iid}`),
  // Cálculo
  calcular:    (id)      => api.post(`/orcamentos/${id}/calcular`),
};

export const fichaApi = {
  // Equipes
  listEquipes:     ()        => api.get('/fichas-equipe'),
  getEquipe:       (id)      => api.get(`/fichas-equipe/${id}`),
  createEquipe:    (body)    => api.post('/fichas-equipe', body),
  updateEquipe:    (id, b)   => api.put(`/fichas-equipe/${id}`, b),
  deleteEquipe:    (id)      => api.delete(`/fichas-equipe/${id}`),
  addItemEquipe:   (id, b)   => api.post(`/fichas-equipe/${id}/itens`, b),
  removeItemEquipe:(fId, iId)=> api.delete(`/fichas-equipe/${fId}/itens/${iId}`),

  // Produtos
  listProdutos:    ()        => api.get('/fichas-produto'),
  getProduto:      (id)      => api.get(`/fichas-produto/${id}`),
  createProduto:   (body)    => api.post('/fichas-produto', body),
  updateProduto:   (id, b)   => api.put(`/fichas-produto/${id}`, b),
  deleteProduto:   (id)      => api.delete(`/fichas-produto/${id}`),
  addItemProduto:  (id, b)   => api.post(`/fichas-produto/${id}/itens`, b),

  // Serviços
  listServicos:    ()        => api.get('/fichas-servico'),
  getServico:      (id)      => api.get(`/fichas-servico/${id}`),
  createServico:   (body)    => api.post('/fichas-servico', body),
  updateServico:   (id, b)   => api.put(`/fichas-servico/${id}`, b),
  deleteServico:   (id)      => api.delete(`/fichas-servico/${id}`),
  addRecurso:      (id, b)   => api.post(`/fichas-servico/${id}/recursos`, b),
  removeRecurso:   (sId, rId)=> api.delete(`/fichas-servico/${sId}/recursos/${rId}`),
};
