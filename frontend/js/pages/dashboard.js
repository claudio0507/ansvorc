/**
 * dashboard.js — Painel principal com métricas de orçamentação
 * Identidade Alta Noroeste · estética editorial/blueprint
 * Gráfico de barras CSS puro (sem libs externas).
 */

import { api } from '../api.js';

export async function renderDashboard(container) {
  container.innerHTML = `
  <div class="page-title">
    <div class="dash-eyebrow">Alta Noroeste &middot; Orçamentação Viária</div>
    <h2>Painel de Controle</h2>
    <p>Visão geral das propostas comerciais e do funil de aprovação.</p>
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
        <p style="color:var(--danger)">${esc(err.message)}</p>
      </div>`;
  }
}

function renderConteudo(target, d) {
  const total     = d.total_orcamentos ?? 0;
  const porStatus = d.por_status ?? {};
  const recentes  = d.orcamentos_recentes ?? [];
  const valorMes  = parseFloat(d.total_orcado_mes ?? 0);
  const margem    = parseFloat(d.margem_media ?? 0);

  const pendentes = (porStatus.rascunho ?? 0) + (porStatus.enviado ?? 0);
  const aprovados = porStatus.aprovado ?? 0;
  const taxaAprov = total ? Math.round((aprovados / total) * 100) : 0;

  target.innerHTML = `
  <!-- ── Indicadores ── -->
  <div class="dash-eyebrow">Indicadores do período</div>
  <div class="dash-cards">

    <div class="dash-card is-primary">
      <div class="dash-card-top">
        <span class="dash-card-label">Total Orçado · Mês</span>
        <span class="dash-card-icon">${icoCoin()}</span>
      </div>
      <div class="dash-card-value">${fmtBRL(valorMes)}</div>
      <div class="dash-card-foot">Soma das propostas emitidas no mês corrente</div>
    </div>

    <div class="dash-card">
      <div class="dash-card-top">
        <span class="dash-card-label">Margem Média · MLR</span>
        <span class="dash-card-icon">${icoTrend()}</span>
      </div>
      <div class="dash-card-value">${fmtPct(margem)}</div>
      <div class="dash-card-foot">Margem líquida real consolidada</div>
    </div>

    <div class="dash-card">
      <div class="dash-card-top">
        <span class="dash-card-label">Propostas Pendentes</span>
        <span class="dash-card-icon">${icoClock()}</span>
      </div>
      <div class="dash-card-value">${pendentes}</div>
      <div class="dash-card-foot">Rascunhos + enviados aguardando</div>
    </div>

    <div class="dash-card">
      <div class="dash-card-top">
        <span class="dash-card-label">Taxa de Aprovação</span>
        <span class="dash-card-icon">${icoCheck()}</span>
      </div>
      <div class="dash-card-value">${taxaAprov}%</div>
      <div class="dash-card-foot">${aprovados} de ${total} orçamentos aprovados</div>
    </div>

  </div>

  <!-- ── Análise ── -->
  <div class="dash-eyebrow">Distribuição &amp; funil</div>
  <div class="dash-grid">
    <div class="card">
      <div class="card-header"><h3 class="card-title">Orçamentos por Status</h3></div>
      ${renderBarChart(porStatus, total)}
    </div>

    <div class="card">
      <div class="card-header"><h3 class="card-title">Fluxo de Aprovação</h3></div>
      <div style="padding:1.25rem 1rem">
        ${renderFluxo(porStatus)}
      </div>
    </div>

    <div class="card" style="grid-column:span 2">
      <div class="card-header">
        <h3 class="card-title">Propostas Recentes</h3>
        <a href="#/orcamentos" class="btn btn-ghost btn-sm">Ver todas &rarr;</a>
      </div>
      ${renderRecentes(recentes)}
    </div>
  </div>`;
}

// ── Gráfico de barras CSS — escala cinza + acento vermelho ───────────────────

function renderBarChart(porStatus, total) {
  if (!total) {
    return `<div style="padding:2rem;text-align:center;color:var(--text-muted)">
      Nenhum orçamento cadastrado.</div>`;
  }

  const STATUS = [
    { key: 'rascunho',  label: 'Rascunho'  },
    { key: 'enviado',   label: 'Enviado'   },
    { key: 'aprovado',  label: 'Aprovado'  },
    { key: 'rejeitado', label: 'Rejeitado' },
  ];

  const itens = STATUS.map(s => ({ ...s, n: porStatus[s.key] ?? 0 }))
    .filter(s => s.n > 0)
    .sort((a, b) => b.n - a.n);

  const maxN = Math.max(...itens.map(s => s.n), 1);

  // Barra de maior valor recebe o vermelho da marca; demais em escala de cinza.
  const GRAY = ['var(--text-light)', 'var(--border-strong)', 'var(--text-muted)'];

  return `
  <div class="bar-chart" style="padding:1.25rem">
    ${itens.map((s, i) => {
      const pct   = Math.round((s.n / maxN) * 100);
      const share = Math.round((s.n / total) * 100);
      const color = i === 0 ? 'var(--primary)' : GRAY[(i - 1) % GRAY.length];
      return `
      <div class="bar-row">
        <div class="bar-label">${s.label}</div>
        <div class="bar-track">
          <div class="bar-fill" style="width:${pct}%;background:${color}"></div>
        </div>
        <div class="bar-value">${s.n} <span class="bar-pct">${share}%</span></div>
      </div>`;
    }).join('')}
  </div>`;
}

// ── Fluxo visual — paleta neutra/vermelha da marca ───────────────────────────

function renderFluxo(p) {
  const steps = [
    { key: 'rascunho',  label: 'Rascunho',  desc: 'Em elaboração'       },
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
    ${i < steps.length - 1 ? '<div class="flow-arrow">&rarr;</div>' : ''}
    `).join('')}
  </div>`;
}

// ── Tabela recentes ──────────────────────────────────────────────────────────

function renderRecentes(recentes) {
  if (!recentes.length) {
    return `<div style="padding:1.5rem;text-align:center;color:var(--text-muted)">
      Nenhum orçamento cadastrado.</div>`;
  }

  return `<div class="table-wrap" style="border:none">
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
        <td><code style="font-family:var(--font-mono);color:var(--primary);font-size:.8125rem">${esc(o.numero_proposta)}</code></td>
        <td>${badgeStatus(o.status)}</td>
        <td style="font-weight:600">${fmtBRL(parseFloat(o.total_proposta ?? 0))}</td>
        <td style="font-size:.8125rem;color:var(--text-muted)">${fmtData(o.criado_em)}</td>
        <td><a href="#/orcamentos/${o.id}" class="btn btn-ghost btn-sm">Abrir &rarr;</a></td>
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

// Funil: cinza neutro → âmbar → vermelho-marca → vermelho-tijolo (via tokens)
function statusBg(s) {
  return {
    rascunho:  'var(--bg-subtle)',
    enviado:   'var(--warning-soft)',
    aprovado:  'var(--primary-alpha)',
    rejeitado: 'var(--danger-soft)',
  }[s] ?? 'var(--bg-subtle)';
}

function statusFg(s) {
  return {
    rascunho:  'var(--text-muted)',
    enviado:   'var(--warning)',
    aprovado:  'var(--primary)',
    rejeitado: 'var(--danger)',
  }[s] ?? 'var(--text-muted)';
}

// ── Ícones (stroke monocromático, herdam currentColor) ───────────────────────

function icoCoin()  { return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M14.5 9.5a2.5 2 0 0 0-2.5-1.5c-1.5 0-2.5.7-2.5 1.8 0 2.4 5 1.2 5 3.6 0 1.2-1 1.9-2.5 1.9a2.5 2 0 0 1-2.5-1.5"/><path d="M12 6.5v11"/></svg>`; }
function icoTrend() { return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>`; }
function icoClock() { return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><polyline points="12 7 12 12 16 14"/></svg>`; }
function icoCheck() { return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>`; }
