/**
 * app.js — SPA router + shell principal do Sinalys
 *
 * Hash-based routing: #/login, #/dashboard, #/bds/rh, etc.
 * Importa páginas lazily para manter bundles separados.
 */

import { auth } from './api.js';
import { renderLogin }     from './pages/login.js';
import { renderDashboard } from './pages/dashboard.js';
import { renderBDs }       from './pages/bds.js';
import { renderFichas }    from './pages/fichas.js';
import { renderOrcamentos} from './pages/orcamentos.js';

// ── Toast ─────────────────────────────────────────────────────────────────────

export function toast(message, type = 'info', duration = 3500) {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const icons = {
    success: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M20 6L9 17l-5-5"/></svg>`,
    error:   `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>`,
    info:    `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`,
  };

  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.innerHTML = `${icons[type] ?? ''}<span>${message}</span>`;
  container.appendChild(el);

  setTimeout(() => {
    el.style.transition = 'opacity .3s, transform .3s';
    el.style.opacity = '0';
    el.style.transform = 'translateY(8px)';
    setTimeout(() => el.remove(), 320);
  }, duration);
}

// ── Rotas ─────────────────────────────────────────────────────────────────────

const ROUTES = {
  '/login':       { render: renderLogin,      auth: false, title: 'Entrar'           },
  '/dashboard':   { render: renderDashboard,  auth: true,  title: 'Dashboard'        },
  '/bds':         { render: renderBDs,        auth: true,  title: 'Bancos de Dados'  },
  '/bds/rh':      { render: (el) => renderBDs(el, 'rh'),   auth: true, title: 'BD Recursos Humanos' },
  '/bds/epi':     { render: (el) => renderBDs(el, 'epi'),  auth: true, title: 'BD EPIs' },
  '/bds/frotas':  { render: (el) => renderBDs(el, 'frotas'), auth: true, title: 'BD Frotas' },
  '/bds/materiais':{ render: (el) => renderBDs(el, 'materiais'), auth: true, title: 'BD Materiais' },
  '/bds/estrutura':{ render: (el) => renderBDs(el, 'estrutura'), auth: true, title: 'BD Estrutura Operacional' },
  '/bds/despesas':{ render: (el) => renderBDs(el, 'despesas'), auth: true, title: 'BD Despesas' },
  '/fichas':      { render: renderFichas,     auth: true,  title: 'Fichas Técnicas'  },
  '/fichas/equipes':   { render: (el) => renderFichas(el, 'equipes'),   auth: true, title: 'Fichas de Equipe'   },
  '/fichas/produtos':  { render: (el) => renderFichas(el, 'produtos'),  auth: true, title: 'Fichas de Produto'  },
  '/fichas/servicos':  { render: (el) => renderFichas(el, 'servicos'),  auth: true, title: 'Fichas de Serviço'  },
  '/orcamentos':  { render: renderOrcamentos, auth: true,  title: 'Orçamentos'       },
  '/orcamentos/novo': { render: (el) => renderOrcamentos(el, 'novo'), auth: true, title: 'Novo Orçamento' },
};

function resolveRoute(hash) {
  const path = hash.replace(/^#/, '') || '/login';
  if (ROUTES[path]) return { path, route: ROUTES[path] };
  // Fallback: rota mais específica que seja prefixo
  const match = Object.keys(ROUTES)
    .filter(r => path.startsWith(r))
    .sort((a, b) => b.length - a.length)[0];
  return match ? { path: match, route: ROUTES[match] } : null;
}

// ── Shell HTML ────────────────────────────────────────────────────────────────

function buildShell() {
  return `
  <nav class="sidebar" id="sidebar">
    <div class="sidebar-header">
      <div class="sidebar-logo">
        ${logoSvg()}
      </div>
      <span class="sidebar-brand">Sinalys</span>
      <button class="sidebar-toggle btn-icon" id="sidebar-toggle" title="Recolher menu" aria-label="Toggle sidebar">
        ${chevronLeft()}
      </button>
    </div>

    <div class="sidebar-nav">

      <div class="nav-section-title">Principal</div>

      <a class="nav-item" href="#/dashboard" data-route="/dashboard">
        <span class="nav-icon">${iconHome()}</span>
        <span class="nav-label">Dashboard</span>
      </a>

      <div class="nav-section-title">Bancos de Dados</div>

      <a class="nav-item" href="#/bds/rh" data-route="/bds/rh">
        <span class="nav-icon">${iconPeople()}</span>
        <span class="nav-label">Recursos Humanos</span>
      </a>
      <a class="nav-item" href="#/bds/epi" data-route="/bds/epi">
        <span class="nav-icon">${iconShield()}</span>
        <span class="nav-label">EPIs</span>
      </a>
      <a class="nav-item" href="#/bds/frotas" data-route="/bds/frotas">
        <span class="nav-icon">${iconTruck()}</span>
        <span class="nav-label">Frotas</span>
      </a>
      <a class="nav-item" href="#/bds/materiais" data-route="/bds/materiais">
        <span class="nav-icon">${iconBox()}</span>
        <span class="nav-label">Materiais</span>
      </a>
      <a class="nav-item" href="#/bds/estrutura" data-route="/bds/estrutura">
        <span class="nav-icon">${iconBuilding()}</span>
        <span class="nav-label">Estrutura Op.</span>
      </a>
      <a class="nav-item" href="#/bds/despesas" data-route="/bds/despesas">
        <span class="nav-icon">${iconReceipt()}</span>
        <span class="nav-label">Despesas</span>
      </a>

      <div class="nav-section-title">Fichas Técnicas</div>

      <a class="nav-item" href="#/fichas/equipes" data-route="/fichas/equipes">
        <span class="nav-icon">${iconUsers()}</span>
        <span class="nav-label">Equipes</span>
      </a>
      <a class="nav-item" href="#/fichas/produtos" data-route="/fichas/produtos">
        <span class="nav-icon">${iconLayers()}</span>
        <span class="nav-label">Produtos (BOM)</span>
      </a>
      <a class="nav-item" href="#/fichas/servicos" data-route="/fichas/servicos">
        <span class="nav-icon">${iconWrench()}</span>
        <span class="nav-label">Serviços</span>
      </a>

      <div class="nav-section-title">Orçamentação</div>

      <a class="nav-item" href="#/orcamentos" data-route="/orcamentos">
        <span class="nav-icon">${iconDoc()}</span>
        <span class="nav-label">Orçamentos</span>
      </a>

    </div><!-- /.sidebar-nav -->

    <div class="sidebar-footer">
      <div class="user-tile" id="user-tile">
        <div class="user-avatar" id="user-avatar">—</div>
        <div class="user-info">
          <div class="user-name" id="user-name">Usuário</div>
          <div class="user-role" id="user-role">Sem perfil</div>
        </div>
      </div>
    </div>
  </nav><!-- /.sidebar -->

  <div class="main-area">
    <header class="topbar">
      <span class="topbar-title" id="topbar-title">Dashboard</span>
      <div class="topbar-actions">
        <button class="btn btn-ghost btn-sm" id="logout-btn">
          ${iconLogout()} Sair
        </button>
      </div>
    </header>
    <main class="page-content" id="page-content"></main>
  </div>
  `;
}

// ── Router ────────────────────────────────────────────────────────────────────

let currentPath = null;

async function navigate(hash) {
  const resolved = resolveRoute(hash);

  if (!resolved) {
    window.location.hash = auth.isLoggedIn() ? '#/dashboard' : '#/login';
    return;
  }

  const { path, route } = resolved;

  // Guard: rota protegida sem auth
  if (route.auth && !auth.isLoggedIn()) {
    window.location.hash = '#/login';
    return;
  }

  // Guard: já está na tela de login mas está autenticado
  if (path === '/login' && auth.isLoggedIn()) {
    window.location.hash = '#/dashboard';
    return;
  }

  const isLoginRoute = path === '/login';

  // Mostra tela de login sem shell
  const screenApp   = document.getElementById('screen-app');
  const screenLogin = document.getElementById('screen-login');

  if (isLoginRoute) {
    if (screenApp)   screenApp.classList.add('hidden');
    if (screenLogin) screenLogin.classList.remove('hidden');
    renderLogin(screenLogin);
    currentPath = path;
    return;
  }

  // Mostra shell + conteúdo
  if (screenLogin) screenLogin.classList.add('hidden');

  if (!screenApp.innerHTML.trim() || !document.getElementById('page-content')) {
    screenApp.innerHTML = buildShell();
    wireShell();
  }

  screenApp.classList.remove('hidden');
  setActiveNav(path);
  setTopbarTitle(route.title);
  updateUserTile();

  const content = document.getElementById('page-content');
  content.innerHTML = '<div class="loading-overlay"><div class="spinner"></div><span>Carregando…</span></div>';

  try {
    await route.render(content);
  } catch (err) {
    content.innerHTML = `<div class="placeholder-page">
      ${iconAlert()}
      <h3>Erro ao carregar</h3>
      <p>${err.message}</p>
      <button class="btn btn-secondary btn-sm mt-4" onclick="window.location.reload()">Recarregar</button>
    </div>`;
  }

  currentPath = path;
}

function wireShell() {
  const toggle = document.getElementById('sidebar-toggle');
  if (toggle) {
    toggle.addEventListener('click', () => {
      document.getElementById('sidebar').classList.toggle('collapsed');
      localStorage.setItem('sidebar_collapsed', document.getElementById('sidebar').classList.contains('collapsed'));
    });
  }

  // Restaura estado do sidebar
  if (localStorage.getItem('sidebar_collapsed') === 'true') {
    document.getElementById('sidebar')?.classList.add('collapsed');
  }

  const logoutBtn = document.getElementById('logout-btn');
  if (logoutBtn) logoutBtn.addEventListener('click', auth.logout);

  const userTile = document.getElementById('user-tile');
  if (userTile) userTile.addEventListener('click', () => toast('Perfil em desenvolvimento', 'info'));
}

function setActiveNav(path) {
  document.querySelectorAll('.nav-item').forEach(a => {
    const r = a.dataset.route;
    a.classList.toggle('active', r === path || (r && path.startsWith(r) && r !== '/'));
  });
}

function setTopbarTitle(title) {
  const el = document.getElementById('topbar-title');
  if (el) el.textContent = title;
}

function updateUserTile() {
  const user = auth.getUser();
  if (!user) return;
  const nameEl  = document.getElementById('user-name');
  const roleEl  = document.getElementById('user-role');
  const avEl    = document.getElementById('user-avatar');
  if (nameEl) nameEl.textContent = user.nome ?? user.email ?? 'Usuário';
  if (roleEl) roleEl.textContent = user.papel ?? 'Operador';
  if (avEl)   avEl.textContent   = (user.nome ?? user.email ?? 'U')[0].toUpperCase();
}

// ── Bootstrap ─────────────────────────────────────────────────────────────────

export function initRouter() {
  window.addEventListener('hashchange', () => navigate(window.location.hash));

  const hash = window.location.hash || (auth.isLoggedIn() ? '#/dashboard' : '#/login');
  navigate(hash);
}

// ── Inline SVG helpers ────────────────────────────────────────────────────────
// (evita dependência de CDN externo)

function logoSvg()    { return `<svg viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5zm0 10L2 7v10l10 5 10-5V7l-10 5z"/></svg>`; }
function chevronLeft(){ return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>`; }
function iconHome()   { return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>`; }
function iconPeople() { return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/></svg>`; }
function iconShield() { return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>`; }
function iconTruck()  { return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="1" y="3" width="15" height="13"/><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/></svg>`; }
function iconBox()    { return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>`; }
function iconBuilding(){ return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14"/><path d="M16 21V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v16"/></svg>`; }
function iconReceipt(){ return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>`; }
function iconUsers()  { return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg>`; }
function iconLayers() { return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>`; }
function iconWrench() { return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3.77-3.77a6 6 0 01-7.94 7.94l-6.91 6.91a2.12 2.12 0 01-3-3l6.91-6.91a6 6 0 017.94-7.94l-3.76 3.76z"/></svg>`; }
function iconDoc()    { return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>`; }
function iconLogout() { return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px;height:16px"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>`; }
function iconAlert()  { return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`; }
