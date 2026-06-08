/**
 * orcamentos.js — Tela de Orçamentos (placeholder Fase 2)
 */

export function renderOrcamentos(container) {
  container.innerHTML = `
  <div class="page-title">
    <h2>Orçamentos</h2>
    <p>Gestão de propostas comerciais</p>
  </div>

  <div class="placeholder-page">
    <div class="placeholder-icon">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="width:64px;height:64px;color:var(--primary);opacity:.5">
        <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
        <line x1="16" y1="13" x2="8" y2="13"/>
        <line x1="16" y1="17" x2="8" y2="17"/>
        <polyline points="10 9 9 9 8 9"/>
      </svg>
    </div>
    <h3>Módulo em desenvolvimento</h3>
    <p>O módulo de orçamentos será implementado na Fase 2.<br/>
       Ele integrará BDs + Fichas Técnicas para composição de custos com BDI, REIDI e Fator K.</p>
    <div style="margin-top:1.5rem;display:flex;gap:.75rem;justify-content:center;flex-wrap:wrap">
      <div class="badge badge-neutral">BDI Primário</div>
      <div class="badge badge-neutral">BDI Sombra</div>
      <div class="badge badge-neutral">Fator K</div>
      <div class="badge badge-neutral">REIDI</div>
      <div class="badge badge-neutral">MOD FAT</div>
    </div>
  </div>
  `;
}
