/**
 * dashboard.js — Tela inicial após login
 * Exibe cards de acesso rápido e estatísticas dos BDs via API.
 */

import { bdApi, fichaApi } from '../api.js';
import { toast } from '../app.js';

export async function renderDashboard(container) {
  // Renderiza esqueleto imediatamente
  container.innerHTML = `
  <div class="page-title">
    <h2>Dashboard</h2>
    <p>Visão geral do sistema de orçamentação</p>
  </div>

  <div class="stats-grid" id="stats-grid">
    ${statSkeleton(4)}
  </div>

  <div class="page-title">
    <h3>Acesso Rápido</h3>
  </div>
  <div class="quick-grid">
    ${quickCard('#/bds/rh',       'red',    iconPeople(),  'Recursos Humanos',     'Cargos e custos de MO')}
    ${quickCard('#/bds/epi',      'amber',  iconShield(),  'EPIs',                 'Equipamentos de proteção')}
    ${quickCard('#/bds/frotas',   'blue',   iconTruck(),   'Frotas',               'Veículos e equipamentos')}
    ${quickCard('#/bds/materiais','green',  iconBox(),     'Materiais',            'Insumos e componentes')}
    ${quickCard('#/fichas/equipes','red',   iconUsers(),   'Fichas de Equipe',     'Composição de equipes')}
    ${quickCard('#/fichas/produtos','blue', iconLayers(),  'Fichas de Produto',    'BOM de placas e kits')}
    ${quickCard('#/fichas/servicos','green',iconWrench(),  'Fichas de Serviço',    'Serviços parametrizados')}
    ${quickCard('#/orcamentos',   'purple', iconDoc(),     'Orçamentos',           'Propostas comerciais')}
  </div>
  `;

  // Carrega stats em paralelo, sem bloquear UI
  loadStats().catch(() => {});
}

async function loadStats() {
  const grid = document.getElementById('stats-grid');
  if (!grid) return;

  try {
    const [rhs, epis, frotas, mats, equipes, produtos, servicos] = await Promise.allSettled([
      bdApi.listRH(),
      bdApi.listEPI(),
      bdApi.listFrotas(),
      bdApi.listMat(),
      fichaApi.listEquipes(),
      fichaApi.listProdutos(),
      fichaApi.listServicos(),
    ]);

    const val = (r) => r.status === 'fulfilled' ? (r.value?.length ?? '—') : '!';

    grid.innerHTML = `
      ${stat('Cargos RH',    val(rhs),      'Recursos humanos')}
      ${stat('Materiais',    val(mats),     'Insumos cadastrados')}
      ${stat('Eq. Técnicas', val(equipes),  'Fichas de equipe')}
      ${stat('Serviços',     val(servicos), 'Fichas de serviço')}
    `;
  } catch {
    grid.innerHTML = '';
  }
}

// ── Helpers HTML ──────────────────────────────────────────────────────────────

function stat(label, value, sub) {
  return `
  <div class="stat-card">
    <div class="stat-label">${label}</div>
    <div class="stat-value">${value}</div>
    <div class="stat-sub">${sub}</div>
  </div>`;
}

function statSkeleton(n) {
  return Array.from({ length: n }, () => `
  <div class="stat-card" style="opacity:.4">
    <div class="stat-label">—</div>
    <div class="stat-value">…</div>
    <div class="stat-sub">carregando</div>
  </div>`).join('');
}

function quickCard(href, color, icon, title, desc) {
  return `
  <a class="quick-card" href="${href}">
    <div class="quick-icon ${color}">${icon}</div>
    <h4>${title}</h4>
    <p>${desc}</p>
  </a>`;
}

// SVG inline helpers (duplicados de app.js — evita import circular)
function iconPeople() { return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/></svg>`; }
function iconShield() { return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>`; }
function iconTruck()  { return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="1" y="3" width="15" height="13"/><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/></svg>`; }
function iconBox()    { return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>`; }
function iconUsers()  { return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg>`; }
function iconLayers() { return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>`; }
function iconWrench() { return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3.77-3.77a6 6 0 01-7.94 7.94l-6.91 6.91a2.12 2.12 0 01-3-3l6.91-6.91a6 6 0 017.94-7.94l-3.76 3.76z"/></svg>`; }
function iconDoc()    { return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>`; }
