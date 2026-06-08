/**
 * fichas.js — Telas de Fichas Técnicas (Equipes, Produtos, Serviços)
 */

import { fichaApi } from '../api.js';
import { toast } from '../app.js';

export async function renderFichas(container, section = 'equipes') {
  const SECTIONS = {
    equipes:  { title: 'Fichas de Equipe',   list: fichaApi.listEquipes,  type: 'equipe'  },
    produtos: { title: 'Fichas de Produto',  list: fichaApi.listProdutos, type: 'produto' },
    servicos: { title: 'Fichas de Serviço',  list: fichaApi.listServicos, type: 'servico' },
  };

  const cfg = SECTIONS[section];
  if (!cfg) {
    container.innerHTML = `<div class="placeholder-page"><h3>Seção inválida: ${section}</h3></div>`;
    return;
  }

  container.innerHTML = `
  <div class="page-title">
    <h2>${cfg.title}</h2>
    <p>Parametrização de fichas técnicas</p>
  </div>

  <div class="list-toolbar">
    <div class="search-box">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
      </svg>
      <input type="text" id="search-input" class="form-control" placeholder="Filtrar fichas…" />
    </div>
    <button class="btn btn-primary btn-sm" id="btn-nova-ficha">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="width:14px;height:14px"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
      Nova Ficha
    </button>
  </div>

  <div class="card">
    <table class="data-table">
      <thead>
        <tr>
          <th>Código</th>
          <th>Nome</th>
          <th>Detalhes</th>
          <th>Itens</th>
          <th>Status</th>
          <th></th>
        </tr>
      </thead>
      <tbody id="fichas-tbody">
        <tr><td colspan="6" style="text-align:center;padding:2rem">
          <div class="spinner" style="margin:0 auto"></div>
        </td></tr>
      </tbody>
    </table>
  </div>
  `;

  const searchEl = document.getElementById('search-input');
  searchEl.addEventListener('input', () => {
    const q = searchEl.value.toLowerCase();
    document.querySelectorAll('#fichas-tbody tr[data-id]').forEach(tr => {
      tr.style.display = tr.textContent.toLowerCase().includes(q) ? '' : 'none';
    });
  });

  document.getElementById('btn-nova-ficha').addEventListener('click', () =>
    openCriarFichaModal(section, refresh)
  );

  async function refresh() {
    try {
      const fichas = await cfg.list();
      renderFichasTable(fichas, section, refresh);
    } catch (err) {
      document.getElementById('fichas-tbody').innerHTML =
        `<tr><td colspan="6" style="text-align:center;color:var(--danger)">Erro: ${err.message}</td></tr>`;
    }
  }

  await refresh();
}

// ── Tabela de fichas ──────────────────────────────────────────────────────────

function renderFichasTable(fichas, section, refresh) {
  const tbody = document.getElementById('fichas-tbody');
  if (!tbody) return;

  if (!fichas.length) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:2rem;color:var(--text-muted)">Nenhuma ficha cadastrada.</td></tr>`;
    return;
  }

  tbody.innerHTML = fichas.map(f => {
    const detalhe = section === 'equipes'
      ? `Produção: ${f.producao_diaria} ${f.unidade_producao}`
      : section === 'servicos'
      ? `${f.tipo_servico} | Prod: ${f.producao_diaria} ${f.unidade_medida}`
      : `Und: ${f.unidade_medida}`;

    const flag = section === 'servicos' ? f.possui_recursos : f.possui_itens;
    const flagLabel = section === 'servicos' ? 'Recursos' : 'Itens';

    return `<tr data-id="${f.id}">
      <td><code style="font-size:.8125rem;color:var(--primary)">${f.codigo}</code></td>
      <td><strong>${f.nome}</strong></td>
      <td style="color:var(--text-muted);font-size:.8125rem">${detalhe}</td>
      <td>${flag
        ? `<span class="badge badge-success">${flagLabel} OK</span>`
        : `<span class="badge badge-warning">Sem ${flagLabel.toLowerCase()}</span>`
      }</td>
      <td>${f.ativo
        ? `<span class="badge badge-success">Ativa</span>`
        : `<span class="badge badge-neutral">Inativa</span>`
      }</td>
      <td style="text-align:right">
        <button class="btn btn-ghost btn-sm btn-del" data-id="${f.id}" title="Excluir">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;color:var(--danger)"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/></svg>
        </button>
      </td>
    </tr>`;
  }).join('');

  tbody.querySelectorAll('.btn-del').forEach(btn => {
    btn.addEventListener('click', async () => {
      if (!confirm('Excluir ficha e todos os seus itens?')) return;
      const id = Number(btn.dataset.id);
      try {
        const deleteMap = {
          equipes:  fichaApi.deleteEquipe,
          produtos: fichaApi.deleteProduto,
          servicos: fichaApi.deleteServico,
        };
        await deleteMap[section](id);
        toast('Ficha excluída', 'success');
        await refresh();
      } catch (err) {
        toast(`Erro: ${err.message}`, 'error');
      }
    });
  });
}

// ── Modal criar ficha ─────────────────────────────────────────────────────────

function openCriarFichaModal(section, onSave) {
  const titles = { equipes: 'Equipe', produtos: 'Produto', servicos: 'Serviço' };

  const equipeFields = `
    <div class="form-group">
      <label class="form-label">Produção Diária *</label>
      <input name="producao_diaria" type="number" class="form-control" value="1" step="0.01" min="0" required />
    </div>
    <div class="form-group">
      <label class="form-label">Unidade de Produção *</label>
      <input name="unidade_producao" type="text" class="form-control" value="dia" required />
    </div>`;

  const produtoFields = `
    <div class="form-group">
      <label class="form-label">Unidade de Medida *</label>
      <input name="unidade_medida" type="text" class="form-control" value="un" required />
    </div>`;

  const servicoFields = `
    <div class="form-group">
      <label class="form-label">Tipo de Serviço *</label>
      <select name="tipo_servico" class="form-control" required>
        <option>VERTICAL</option><option>HORIZONTAL</option><option>SH</option><option>OUTROS</option>
      </select>
    </div>
    <div class="form-group">
      <label class="form-label">Unidade de Medida *</label>
      <input name="unidade_medida" type="text" class="form-control" value="m²" required />
    </div>
    <div class="form-group">
      <label class="form-label">Produção Diária *</label>
      <input name="producao_diaria" type="number" class="form-control" value="1" step="0.01" min="0" required />
    </div>`;

  const extraFields = { equipes: equipeFields, produtos: produtoFields, servicos: servicoFields }[section] ?? '';

  const backdrop = document.createElement('div');
  backdrop.className = 'modal-backdrop';
  backdrop.innerHTML = `
  <div class="modal">
    <div class="modal-header">
      <h3>Nova Ficha de ${titles[section]}</h3>
      <button class="btn btn-ghost btn-icon btn-close" aria-label="Fechar">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
      </button>
    </div>
    <form id="ficha-form">
      <div class="modal-body" style="display:grid;grid-template-columns:1fr 1fr;gap:1rem">
        <div class="form-group">
          <label class="form-label">Código *</label>
          <input name="codigo" type="text" class="form-control" required placeholder="EQ-001" />
        </div>
        <div class="form-group" style="grid-column:span 2">
          <label class="form-label">Nome *</label>
          <input name="nome" type="text" class="form-control" required placeholder="Nome da ficha…" />
        </div>
        <div class="form-group" style="grid-column:span 2">
          <label class="form-label">Descrição</label>
          <input name="descricao" type="text" class="form-control" placeholder="Opcional…" />
        </div>
        ${extraFields}
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary btn-close">Cancelar</button>
        <button type="submit" class="btn btn-primary">Criar Ficha</button>
      </div>
    </form>
  </div>`;

  document.body.appendChild(backdrop);
  backdrop.querySelectorAll('.btn-close').forEach(b => b.addEventListener('click', () => backdrop.remove()));
  backdrop.addEventListener('click', (e) => { if (e.target === backdrop) backdrop.remove(); });

  backdrop.querySelector('#ficha-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const data = {};
    for (const [k, v] of fd.entries()) data[k] = v === '' ? null : v;

    const createMap = {
      equipes:  fichaApi.createEquipe,
      produtos: fichaApi.createProduto,
      servicos: fichaApi.createServico,
    };

    const btn = backdrop.querySelector('[type="submit"]');
    btn.disabled = true; btn.textContent = 'Criando…';
    try {
      await createMap[section](data);
      toast('Ficha criada com sucesso', 'success');
      backdrop.remove();
      await onSave();
    } catch (err) {
      toast(`Erro: ${err.message}`, 'error');
      btn.disabled = false; btn.textContent = 'Criar Ficha';
    }
  });

  backdrop.querySelector('input')?.focus();
}
