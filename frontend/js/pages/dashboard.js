/**
 * dashboard.js — Painel principal com métricas de orçamentação
 * Gráfico de barras CSS puro (sem libs externas).
 */

import { api } from '../api.js';

export async function renderDashboard(container) {
  container.innerHTML = `
  <div class="page-title">
    <h2>Dashboard</h2>
    <p>Visão geral das propostas comerciais</p>
  </div>
  <div id="dash-body">
    <div class="loading-overlay" style="min-height:200px;position:relative">
      <div class="spinner" style="position:static;margin:2rem auto"></div>
    </div>
  </div>`;

  try {
    const d = await api.get('/dashboard');
    renderConteudo(document.getElementById('dash-body'), d);
  } catch (err) {
    document.getElementById('dash-body').innerHTML =
      `<div class="placeholder-page" style="margin-top:2rem">
        <p style="color:var(--danger)">${err.message}</p>
      </div>`;
  }
}

function renderConteudo(target, d) {
  const total    = d.total_orcamentos ?? 0;
  const porStatus = d.por_status ?? {};
  const recentes  = d.orcamentos_recentes ?? [];
  const valorMes  = parseFloat(d.total_orcado_mes ?? 0);
  const margem    = parseFloat(d.margem_media ?? 0);

  const pendentes = (porStatus.rascunho ?? 0) + (porStatus.enviado ?? 0);

  target.innerHTML = `
  <!-- ── Cards de métricas ── -->
  <div class="dash-cards">
    <div class="dash-card">
      <div class="dash-card-icon" style="background:rgba(30,64,175,.12);color:#1e40af">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <polyline points="12 6 12 12 16 14"/>
        </svg>
      </div>
      <div class="dash-card-body">
        <div class="dash-card-value">${fmtBRL(valorMes)}</div>
        <div class="dash-card-label">Total Orçado (mês)</div>
      </div>
    </div>

    <div class="dash-card">
      <div class="dash-card-icon" style="background:rgba(5,150,105,.12);color:#059669">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
          <polyline points="17 6 23 6 23 12"/>
        </svg>
      </div>
      <div class="dash-card-body">
        <div class="dash-card-value">${fmtPct(margem)}</div>
        <div class="dash-card-label">Margem Média (MLR)</div>
      </div>
    </div>

    <div class="dash-card">
      <div class="dash-card-icon" style="background:rgba(234,179,8,.12);color:#ca8a04">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
          <line x1="16" y1="13" x2="8" y2="13"/>
          <line x1="16" y1="17" x2="8" y2="17"/>
        </svg>
      </div>
      <div class="dash-card-body">
        <div class="dash-card-value">${pendentes}</div>
        <div class="dash-card-label">Propostas Pendentes</div>
      </div>
    </div>

    <div class="dash-card">
      <div class="dash-card-icon" style="background:rgba(99,102,241,.12);color:#6366f1">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/>
        </svg>
      </div>
      <div class="dash-card-body">
        <div class="dash-card-value">${total}</div>
        <div class="dash-card-label">Total de Orçamentos</div>
      </div>
    </div>
  </div>

  <!-- ── Grid inferior ── -->
  <div class="dash-grid">
    <!-- Gráfico de barras CSS: por status -->
    <div class="card">
      <div class="card-header"><h3 class="card-title">Orçamentos por Status</h3></div>
      ${renderBarChart(porStatus, total)}
    </div>

    <!-- Fluxo visual de status -->
    <div class="card">
      <div class="card-header"><h3 class="card-title">Fluxo de Aprovação</h3></div>
      <div style="padding:1rem">
        ${renderFluxo(porStatus)}
      </div>
    </div>

    <!-- Recentes -->
    <div class="card" style="grid-column:span 2">
      <div class="card-header">
        <h3 class="card-title">Propostas Recentes</h3>
        <a href="#/orcamentos" class="btn btn-ghost btn-sm">Ver todas →</a>
      </div>
      ${renderRecentes(recentes)}
    </div>
  </div>`;
}

// ── Gráfico de barras CSS ─────────────────────────────────────────────────────

function renderBarChart(porStatus, total) {
  if (!total) {
    return `<div style="padding:2rem;text-align:center;color:var(--text-muted)">
      Nenhum orçamento cadastrado.</div>`;
  }

  const STATUS = [
    { key: 'rascunho',  label: 'Rascunho',  color: '#94a3b8' },
    { key: 'enviado',   label: 'Enviado',   color: '#f59e0b' },
    { key: 'aprovado',  label: 'Aprovado',  color: '#10b981' },
    { key: 'rejeitado', label: 'Rejeitado', color: '#ef4444' },
  ];

  const itens = STATUS.map(s => ({ ...s, n: porStatus[s.key] ?? 0 }))
    .filter(s => s.n > 0)
    .sort((a, b) => b.n - a.n);

  const maxN = Math.max(...itens.map(s => s.n), 1);

  return `
  <div class="bar-chart" style="padding:1rem 1.25rem">
    ${itens.map(s => {
      const pct   = Math.round((s.n / maxN) * 100);
      const share = Math.round((s.n / total) * 100);
      return `
      <div class="bar-row">
        <div class="bar-label">${s.label}</div>
        <div class="bar-track">
          <div class="bar-fill" style="width:${pct}%;background:${s.color}"></div>
        </div>
        <div class="bar-value">${s.n} <span class="bar-pct">(${share}%)</span></div>
      </div>`;
    }).join('')}
  </div>`;
}

// ── Fluxo visual ──────────────────────────────────────────────────────────────

function renderFluxo(p) {
  const steps = [
    { key: 'rascunho',  label: 'Rascunho',  desc: 'Em elaboração'      },
    { key: 'enviado',   label: 'Enviado',   desc: 'Aguardando resposta' },
    { key: 'aprovado',  label: 'Aprovado',  desc: 'Proposta aceita'     },
    { key: 'rejeitado', label: 'Rejeitado', desc: 'Proposta recusada'   },
  ];

  return `<div class="status-flow">
    ${steps.map((s, i) => `
    <div class="flow-step">
      <div class="flow-badge" style="background:${statusBg(s.key)};color:${statusFg(s.key)}">
        <span class="flow-count">${p[s.key] ?? 0}</span>
      </div>
      <div class="flow-label">${s.label}</div>
      <div class="flow-desc">${s.desc}</div>
    </div>
    ${i < steps.length - 1 ? '<div class="flow-arrow">→</div>' : ''}
    `).join('')}
  </div>`;
}

// ── Tabela recentes ───────────────────────────────────────────────────────────

function renderRecentes(recentes) {
  if (!recentes.length) {
    return `<div style="padding:1.5rem;text-align:center;color:var(--text-muted)">
      Nenhum orçamento cadastrado.</div>`;
  }

  return `<div class="table-wrap">
  <table class="data-table">
    <thead>
      <tr>
        <th>Nº Proposta</th>
        <th>Status</th>
        <th>Total</th>
        <th>Data</th>
        <th></th>
      </tr>
    </thead>
    <tbody>
      ${recentes.map(o => `
      <tr>
        <td><code style="color:var(--primary);font-size:.8125rem">${esc(o.numero_proposta)}</code></td>
        <td>${badgeStatus(o.status)}</td>
        <td style="font-weight:600">${fmtBRL(parseFloat(o.total_proposta ?? 0))}</td>
        <td style="font-size:.8125rem;color:var(--text-muted)">${fmtData(o.criado_em)}</td>
        <td><a href="#/orcamentos/${o.id}" class="btn btn-ghost btn-sm">Abrir →</a></td>
      </tr>`).join('')}
    </tbody>
  </table></div>`;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function fmtBRL(n) {
  return (n || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

function fmtPct(n) {
  return ((n || 0) * 100).toLocaleString('pt-BR', {
    minimumFractionDigits: 1, maximumFractionDigits: 1,
  }) + '%';
}

function fmtData(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('pt-BR');
}

function esc(s) {
  if (s == null) return '';
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function badgeStatus(s) {
  const map = {
    rascunho: ['neutral','Rascunho'], enviado: ['warning','Enviado'],
    aprovado: ['success','Aprovado'], rejeitado: ['danger','Rejeitado'],
  };
  const [cls, label] = map[s] ?? ['neutral', s];
  return `<span class="badge badge-${cls}">${label}</span>`;
}

function statusBg(s) {
  return { rascunho:'#e5e5e5', enviado:'#fef3c7', aprovado:'#d1fae5', rejeitado:'#fee2e2' }[s] ?? '#e5e5e5';
}

function statusFg(s) {
  return { rascunho:'#475569', enviado:'#92400e', aprovado:'#065f46', rejeitado:'#991b1b' }[s] ?? '#475569';
}
