/**
 * orcamentos.js — Tela de Orçamentos (lista + editor com grid editável)
 *
 * Roteamento interno via hash:
 *   #/orcamentos          → lista
 *   #/orcamentos/novo     → modal de criação (permanece na lista)
 *   #/orcamentos/{id}     → editor do orçamento
 */

import { orcamentoApi, clienteApi, fichaApi } from '../api.js';
import { toast } from '../app.js';

// ── Estado da página ──────────────────────────────────────────────────────────

const state = {
  orcamento: null,      // objeto Orcamento carregado
  itens: [],            // OrcamentoItem[]
  clientes: [],
  fichasServico: [],
  fichasProduto: [],
  dirtyRows: new Set(), // IDs de linhas com alteração pendente
  calculado: false,
};

// ── Entry point ───────────────────────────────────────────────────────────────

export async function renderOrcamentos(container) {
  const hash = window.location.hash;
  // Ex: #/orcamentos/42  → partes[2] = "42"
  const partes = hash.replace(/^#\//, '').split('/');
  const segmento = partes[1]; // "42", "novo" ou undefined

  if (segmento && segmento !== 'novo' && !isNaN(Number(segmento))) {
    await renderEditor(container, Number(segmento));
  } else {
    await renderLista(container);
    if (segmento === 'novo') openModalNovoOrcamento(() => renderLista(container));
  }
}

// ══════════════════════════════════════════════════════════════════════════════
//   LISTA DE ORÇAMENTOS
// ══════════════════════════════════════════════════════════════════════════════

async function renderLista(container) {
  container.innerHTML = `
  <div class="page-title">
    <h2>Orçamentos</h2>
    <p>Gestão de propostas comerciais</p>
  </div>

  <div class="list-toolbar">
    <div style="display:flex;gap:.5rem;flex-wrap:wrap">
      <button class="btn btn-sm ${statusFiltro('') ? 'btn-primary' : 'btn-secondary'}" data-filtro="">Todos</button>
      <button class="btn btn-sm ${statusFiltro('rascunho') ? 'btn-primary' : 'btn-secondary'}" data-filtro="rascunho">Rascunho</button>
      <button class="btn btn-sm ${statusFiltro('enviado') ? 'btn-primary' : 'btn-secondary'}" data-filtro="enviado">Enviado</button>
      <button class="btn btn-sm ${statusFiltro('aprovado') ? 'btn-primary' : 'btn-secondary'}" data-filtro="aprovado">Aprovado</button>
      <button class="btn btn-sm ${statusFiltro('rejeitado') ? 'btn-primary' : 'btn-secondary'}" data-filtro="rejeitado">Rejeitado</button>
    </div>
    <button class="btn btn-primary btn-sm" id="btn-novo-orc">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="width:14px;height:14px"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
      Novo Orçamento
    </button>
  </div>

  <div class="card">
    <table class="data-table" id="orc-table">
      <thead>
        <tr>
          <th>Nº Proposta</th>
          <th>Cliente</th>
          <th>Obra</th>
          <th>UF</th>
          <th>REIDI</th>
          <th>Total</th>
          <th>Status</th>
          <th></th>
        </tr>
      </thead>
      <tbody id="orc-tbody">
        <tr><td colspan="8" style="text-align:center;padding:2rem">
          <div class="spinner" style="margin:0 auto"></div>
        </td></tr>
      </tbody>
    </table>
  </div>`;

  // Filtro ativo
  let filtroAtivo = '';
  container.querySelectorAll('[data-filtro]').forEach(btn => {
    btn.addEventListener('click', () => {
      filtroAtivo = btn.dataset.filtro;
      container.querySelectorAll('[data-filtro]').forEach(b => {
        b.className = `btn btn-sm ${b.dataset.filtro === filtroAtivo ? 'btn-primary' : 'btn-secondary'}`;
      });
      renderOrcRows(todos, filtroAtivo, clientesMap);
    });
  });

  document.getElementById('btn-novo-orc')?.addEventListener('click', () => {
    openModalNovoOrcamento(() => renderLista(container));
  });

  let todos = [];
  let clientesMap = {};
  async function refresh() {
    try {
      [todos] = await Promise.all([
        orcamentoApi.list(),
        clienteApi.list().then(cs => { clientesMap = Object.fromEntries(cs.map(c => [c.id, c.razao_social])); }).catch(() => {}),
      ]);
      renderOrcRows(todos, filtroAtivo, clientesMap);
    } catch (err) {
      document.getElementById('orc-tbody').innerHTML =
        `<tr><td colspan="8" style="text-align:center;color:var(--danger)">Erro: ${err.message}</td></tr>`;
    }
  }
  await refresh();
}

function statusFiltro(s) { return false; } // helper inicial (estado local da lista)

function renderOrcRows(orcamentos, filtro, clientesMap = {}) {
  const tbody = document.getElementById('orc-tbody');
  if (!tbody) return;

  const filtrados = filtro ? orcamentos.filter(o => o.status === filtro) : orcamentos;

  if (!filtrados.length) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;padding:2rem;color:var(--text-muted)">
      Nenhum orçamento${filtro ? ` com status "${filtro}"` : ''}.
    </td></tr>`;
    return;
  }

  tbody.innerHTML = filtrados.map(o => `
    <tr data-id="${o.id}" style="cursor:pointer" class="orc-row">
      <td><code style="color:var(--primary);font-size:.8125rem">${esc(o.numero_proposta)}</code></td>
      <td style="font-size:.875rem">${esc(clientesMap[o.cliente_id] ?? `#${o.cliente_id}`)}</td>
      <td style="color:var(--text-muted);font-size:.8125rem">${esc(o.descricao_obra ?? '—')}</td>
      <td><span class="badge badge-neutral">${o.uf_execucao}</span></td>
      <td>${o.beneficio_reidi
        ? '<span class="badge badge-success">Sim</span>'
        : '<span class="badge badge-neutral">Não</span>'}</td>
      <td style="font-weight:600">${fmtBRL(o.total_proposta)}</td>
      <td>${badgeStatus(o.status)}</td>
      <td style="text-align:right;display:flex;gap:.25rem;justify-content:flex-end">
        <a href="#/orcamentos/${o.id}" class="btn btn-ghost btn-sm" title="Abrir">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
        </a>
        ${o.status === 'rascunho' ? `
        <button class="btn btn-ghost btn-sm btn-del-orc" data-id="${o.id}" title="Excluir">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;color:var(--danger)"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/></svg>
        </button>` : ''}
      </td>
    </tr>`).join('');

  tbody.querySelectorAll('.btn-del-orc').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.stopPropagation();
      if (!confirm('Excluir orçamento e todos os seus itens?')) return;
      try {
        await orcamentoApi.delete(Number(btn.dataset.id));
        toast('Orçamento excluído', 'success');
        const [todosUp, csUp] = await Promise.all([orcamentoApi.list(), clienteApi.list().catch(() => [])]);
        const cMap = Object.fromEntries(csUp.map(c => [c.id, c.razao_social]));
        renderOrcRows(todosUp, '', cMap);
      } catch (err) {
        toast(`Erro: ${err.message}`, 'error');
      }
    });
  });
}

// ── Modal: novo orçamento ─────────────────────────────────────────────────────

async function openModalNovoOrcamento(onSave) {
  let clientes = [];
  try { clientes = await clienteApi.list(); } catch (_) {}

  const backdrop = document.createElement('div');
  backdrop.className = 'modal-backdrop';
  backdrop.innerHTML = `
  <div class="modal">
    <div class="modal-header">
      <h3>Novo Orçamento</h3>
      <button class="btn btn-ghost btn-icon btn-fechar" aria-label="Fechar">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
      </button>
    </div>
    <form id="form-novo-orc">
      <div class="modal-body" style="display:grid;grid-template-columns:1fr 1fr;gap:1rem">
        <div class="form-group" style="grid-column:span 2">
          <label class="form-label">Nº Proposta *</label>
          <input name="numero_proposta" type="text" class="form-control" required placeholder="PROP-2025-001" />
        </div>
        <div class="form-group" style="grid-column:span 2">
          <label class="form-label">Cliente *</label>
          <select name="cliente_id" class="form-control" required>
            <option value="">Selecione…</option>
            ${clientes.map(c => `<option value="${c.id}">${esc(c.razao_social)}</option>`).join('')}
          </select>
          ${!clientes.length ? `<p style="color:var(--warning);font-size:.8rem;margin-top:.25rem">Nenhum cliente cadastrado. Crie um cliente primeiro.</p>` : ''}
        </div>
        <div class="form-group" style="grid-column:span 2">
          <label class="form-label">Descrição da Obra</label>
          <input name="descricao_obra" type="text" class="form-control" placeholder="Ex: Rodovia PR-444 — Lote 3" />
        </div>
        <div class="form-group">
          <label class="form-label">UF de Execução *</label>
          <select name="uf_execucao" class="form-control" required>
            <option value="PR">Paraná (PR)</option>
            <option value="SP">São Paulo (SP)</option>
            <option value="SC">Santa Catarina (SC)</option>
            <option value="RS">Rio Grande do Sul (RS)</option>
            <option value="MG">Minas Gerais (MG)</option>
          </select>
        </div>
        <div class="form-group" style="align-self:end">
          <label class="form-label">Benefício REIDI</label>
          <label style="display:flex;align-items:center;gap:.5rem;cursor:pointer;padding:.5625rem 0">
            <input type="checkbox" name="beneficio_reidi" value="true" style="width:18px;height:18px;accent-color:var(--primary)" />
            <span style="font-size:.9375rem">Suspensão PIS/COFINS</span>
          </label>
        </div>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary btn-fechar">Cancelar</button>
        <button type="submit" class="btn btn-primary" id="btn-criar-orc">Criar e Abrir</button>
      </div>
    </form>
  </div>`;

  document.body.appendChild(backdrop);
  backdrop.querySelectorAll('.btn-fechar').forEach(b => b.addEventListener('click', () => backdrop.remove()));
  backdrop.addEventListener('click', e => { if (e.target === backdrop) backdrop.remove(); });

  backdrop.querySelector('#form-novo-orc').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('btn-criar-orc');
    btn.disabled = true; btn.textContent = 'Criando…';

    const fd = new FormData(e.target);
    const payload = {
      numero_proposta: fd.get('numero_proposta'),
      cliente_id:      Number(fd.get('cliente_id')),
      descricao_obra:  fd.get('descricao_obra') || null,
      uf_execucao:     fd.get('uf_execucao'),
      beneficio_reidi: fd.get('beneficio_reidi') === 'true',
    };

    try {
      const novo = await orcamentoApi.create(payload);
      toast('Orçamento criado!', 'success');
      backdrop.remove();
      window.location.hash = `#/orcamentos/${novo.id}`;
    } catch (err) {
      toast(`Erro: ${err.message}`, 'error');
      btn.disabled = false; btn.textContent = 'Criar e Abrir';
    }
  });

  backdrop.querySelector('input')?.focus();
}

// ══════════════════════════════════════════════════════════════════════════════
//   EDITOR DE ORÇAMENTO
// ══════════════════════════════════════════════════════════════════════════════

async function renderEditor(container, orcId) {
  container.innerHTML = `<div class="loading-overlay"><div class="spinner"></div><span>Carregando orçamento…</span></div>`;

  try {
    // Carrega dados em paralelo
    const [orc, itens, fichasServico, fichasProduto] = await Promise.all([
      orcamentoApi.get(orcId),
      orcamentoApi.listItens(orcId),
      fichaApi.listServicos().catch(() => []),
      fichaApi.listProdutos().catch(() => []),
    ]);

    state.orcamento = orc;
    state.itens = itens;
    state.fichasServico = fichasServico;
    state.fichasProduto = fichasProduto;
    state.dirtyRows.clear();
    state.calculado = itens.some(i => parseFloat(i.preco_venda_unitario) > 0);

    buildEditorShell(container);
    atualizarPainel();
  } catch (err) {
    container.innerHTML = `<div class="placeholder-page">
      <h3>Erro ao carregar orçamento</h3>
      <p>${err.message}</p>
      <a href="#/orcamentos" class="btn btn-secondary btn-sm mt-4">← Voltar</a>
    </div>`;
  }
}

function buildEditorShell(container) {
  const orc = state.orcamento;
  const readonly = orc.status !== 'rascunho';

  container.innerHTML = `
  <!-- Cabeçalho -->
  <div style="display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:1rem;margin-bottom:1.25rem">
    <div>
      <div style="display:flex;align-items:center;gap:.75rem;flex-wrap:wrap">
        <a href="#/orcamentos" class="btn btn-ghost btn-sm" style="padding:.25rem .5rem">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="width:14px;height:14px"><polyline points="15 18 9 12 15 6"/></svg>
        </a>
        <h2 style="margin:0">${esc(orc.numero_proposta)}</h2>
        ${badgeStatus(orc.status)}
        ${orc.beneficio_reidi ? '<span class="badge badge-success">REIDI</span>' : ''}
        <span class="badge badge-neutral">${orc.uf_execucao}</span>
      </div>
      ${orc.descricao_obra ? `<p style="margin-top:.25rem;font-size:.875rem">${esc(orc.descricao_obra)}</p>` : ''}
    </div>
    <div style="display:flex;gap:.5rem;flex-wrap:wrap">
      ${!readonly ? `
      <button class="btn btn-primary btn-sm" id="btn-calcular">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
        Calcular
      </button>
      <button class="btn btn-secondary btn-sm" id="btn-aprovar">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px"><path d="M20 6L9 17l-5-5"/></svg>
        Aprovar
      </button>` : `
      <button class="btn btn-secondary btn-sm" id="btn-nova-versao">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px"><path d="M1 4v6h6M23 20v-6h-6"/><path d="M20.49 9A9 9 0 005.64 5.64L1 10M23 14l-4.36 4.36A9 9 0 013.51 15"/></svg>
        Nova Versão
      </button>`}
      <button class="btn btn-ghost btn-sm" id="btn-exportar" title="PDF (Fase 4)">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
        Exportar
      </button>
    </div>
  </div>

  <!-- Layout: grid + painel -->
  <div style="display:grid;grid-template-columns:1fr 280px;gap:1.25rem;align-items:start">

    <!-- Grid de itens -->
    <div>
      ${!readonly ? `
      <div class="list-toolbar" style="margin-bottom:.75rem">
        <span style="font-size:.875rem;color:var(--text-muted)" id="hint-dirty"></span>
        <div style="display:flex;gap:.5rem">
          <button class="btn btn-secondary btn-sm" id="btn-add-servico">+ Serviço</button>
          <button class="btn btn-secondary btn-sm" id="btn-add-produto">+ Produto</button>
          <button class="btn btn-ghost btn-sm" id="btn-add-operacional">+ Operacional</button>
          <button class="btn btn-ghost btn-sm" id="btn-add-manual" style="color:var(--warning)">⚠ Manual</button>
        </div>
      </div>` : ''}

      <div class="table-wrap" id="grid-wrap">
        <table class="data-table orc-grid" id="orc-grid">
          <thead>
            <tr>
              <th style="width:90px">Bloco</th>
              <th>Descrição</th>
              <th style="width:50px">Und</th>
              <th style="width:80px;text-align:right">QTD</th>
              <th style="width:105px">MOD FAT</th>
              <th style="width:80px;text-align:right">Margem</th>
              <th style="width:100px;text-align:right">Custo Unit</th>
              <th style="width:105px;text-align:right">Preço Unit</th>
              <th style="width:110px;text-align:right">Preço Total</th>
              ${!readonly ? '<th style="width:36px"></th>' : ''}
            </tr>
          </thead>
          <tbody id="grid-tbody"></tbody>
        </table>
      </div>
    </div>

    <!-- Painel lateral -->
    <div class="painel-lateral" id="painel-lateral">
      <div class="painel-row painel-label">Subtotal Faturável</div>
      <div class="painel-row painel-val" id="p-faturavel">R$ —</div>

      <div class="painel-divider"></div>

      <div class="painel-row painel-label" style="color:var(--danger)">Total a Diluir</div>
      <div class="painel-row painel-val painel-danger" id="p-diluir">R$ —</div>

      <div class="painel-divider"></div>

      <div class="painel-row painel-label">Fator K</div>
      <div class="painel-row painel-val" id="p-fatork">—</div>

      <div class="painel-divider"></div>

      <div class="painel-row painel-label">Margem Líquida Real</div>
      <div class="painel-row painel-val painel-success" id="p-mlr">—</div>

      <div class="painel-divider"></div>

      <div class="painel-row painel-label" style="font-size:.875rem;font-weight:700;text-transform:uppercase;letter-spacing:.05em">Total da Proposta</div>
      <div class="painel-row painel-total" id="p-total">R$ —</div>

      ${!state.calculado ? `<div style="margin-top:.75rem;padding:.625rem;background:rgba(217,119,6,.1);border-radius:var(--radius);font-size:.8125rem;color:var(--warning);text-align:center">
        Clique em "Calcular" para obter os preços finais.
      </div>` : ''}
    </div>
  </div>`;

  renderGridRows();
  wireEditorActions();
}

// ── Grid de linhas ────────────────────────────────────────────────────────────

function renderGridRows() {
  const tbody = document.getElementById('grid-tbody');
  if (!tbody) return;
  const orc = state.orcamento;
  const readonly = orc.status !== 'rascunho';

  if (!state.itens.length) {
    const cols = readonly ? 9 : 10;
    tbody.innerHTML = `<tr><td colspan="${cols}" style="text-align:center;padding:2rem;color:var(--text-muted)">
      Nenhum item adicionado. ${readonly ? '' : 'Use os botões acima para inserir serviços, produtos ou custos operacionais.'}
    </td></tr>`;
    return;
  }

  const BLOCOS_NAO_FAT = new Set(['operacional', 'excepcionais']);

  tbody.innerHTML = state.itens.map(item => {
    const dirty = state.dirtyRows.has(item.id);
    const naoFat = BLOCOS_NAO_FAT.has(item.bloco);
    const bg = dirty ? 'background:rgba(217,119,6,.08);' : '';
    const hasPrices = parseFloat(item.preco_venda_unitario) > 0;

    return `<tr data-id="${item.id}" style="${bg}transition:background .2s">
      <td>
        ${bloqueBadge(item.bloco)}
        ${item.demanda_aprovacao ? '<br><span class="badge badge-warning" style="font-size:.6875rem;margin-top:.15rem">Aprovação</span>' : ''}
      </td>
      <td style="max-width:180px">
        <div style="font-size:.875rem;font-weight:500;line-height:1.3;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${esc(item.descricao)}">${esc(item.descricao)}</div>
        <div style="font-size:.75rem;color:var(--text-muted)">${item.unidade_medida}</div>
      </td>
      <td style="font-size:.8125rem;color:var(--text-muted)">${item.unidade_medida}</td>
      <td style="text-align:right">
        ${readonly
          ? `<span style="font-size:.875rem">${fmtNum(item.quantidade)}</span>`
          : `<input class="cell-input" type="number" value="${item.quantidade}" min="0.0001" step="0.01"
               data-id="${item.id}" data-field="quantidade" style="width:72px" />`
        }
      </td>
      <td>
        ${readonly || naoFat
          ? `<span style="font-size:.8125rem;color:var(--text-muted)">${item.mod_fat}</span>`
          : `<select class="cell-select" data-id="${item.id}" data-field="mod_fat" style="width:100px">
              ${['BDI-MO','BDI-MAT+MO','BDI+ICMS','FAT DIR SIMP'].map(m =>
                `<option value="${m}" ${m === item.mod_fat ? 'selected' : ''}>${m}</option>`
              ).join('')}
            </select>`
        }
      </td>
      <td style="text-align:right">
        ${readonly || naoFat
          ? `<span style="font-size:.875rem;color:var(--text-muted)">${naoFat ? 'Sombra' : fmtPct(item.margem_percentual)}</span>`
          : `<input class="cell-input" type="number" value="${(parseFloat(item.margem_percentual) * 100).toFixed(1)}"
               min="0" max="99.9" step="0.1" data-id="${item.id}" data-field="margem_percentual" style="width:62px" /><span style="font-size:.8125rem;margin-left:2px">%</span>`
        }
      </td>
      <td style="text-align:right;font-size:.875rem">${fmtBRL(item.custo_direto_unitario)}</td>
      <td style="text-align:right">
        ${hasPrices
          ? `<span style="font-size:.875rem;font-weight:500">${fmtBRL(item.preco_final_unitario || item.preco_venda_unitario)}</span>
             ${item.rateio_absorvido > 0 ? `<div style="font-size:.6875rem;color:var(--success)">+${fmtBRL(item.rateio_absorvido)} K</div>` : ''}`
          : '<span style="color:var(--text-light);font-size:.8125rem">—</span>'
        }
      </td>
      <td style="text-align:right">
        ${hasPrices
          ? `<span style="font-size:.875rem;font-weight:600;color:var(--primary)">${fmtBRL(item.preco_venda_total)}</span>`
          : '<span style="color:var(--text-light);font-size:.8125rem">—</span>'
        }
      </td>
      ${!readonly ? `<td>
        <button class="btn btn-ghost btn-sm btn-del-item" data-id="${item.id}" title="Remover item">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:13px;height:13px;color:var(--danger)"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/></svg>
        </button>
      </td>` : ''}
    </tr>`;
  }).join('');

  // Inputs inline: marca dirty e persiste ao sair do campo
  tbody.querySelectorAll('.cell-input, .cell-select').forEach(el => {
    el.addEventListener('change', async () => {
      const id = Number(el.dataset.id);
      const field = el.dataset.field;
      let val = el.value;

      // Margem: converte percentual → fração
      if (field === 'margem_percentual') {
        val = String(parseFloat(val) / 100);
      }

      marcarDirty(id, el.closest('tr'));

      try {
        const updated = await orcamentoApi.updateItem(state.orcamento.id, id, { [field]: val });
        // Atualiza estado local
        const idx = state.itens.findIndex(i => i.id === id);
        if (idx >= 0) state.itens[idx] = { ...state.itens[idx], ...updated };
      } catch (err) {
        toast(`Erro ao salvar: ${err.message}`, 'error');
      }
    });
  });

  // Botões de remover item
  tbody.querySelectorAll('.btn-del-item').forEach(btn => {
    btn.addEventListener('click', async () => {
      const id = Number(btn.dataset.id);
      try {
        await orcamentoApi.deleteItem(state.orcamento.id, id);
        state.itens = state.itens.filter(i => i.id !== id);
        state.dirtyRows.delete(id);
        renderGridRows();
        atualizarPainel();
        toast('Item removido', 'success');
      } catch (err) {
        toast(`Erro: ${err.message}`, 'error');
      }
    });
  });
}

function marcarDirty(id, tr) {
  state.dirtyRows.add(id);
  state.calculado = false;
  if (tr) tr.style.background = 'rgba(217,119,6,.08)';
  const hint = document.getElementById('hint-dirty');
  if (hint) hint.textContent = `${state.dirtyRows.size} linha(s) alterada(s) — clique em Calcular`;
}

// ── Painel lateral ────────────────────────────────────────────────────────────

function atualizarPainel(resultado) {
  const p = (id) => document.getElementById(id);
  if (!resultado) {
    // Tenta mostrar totais salvos no orçamento
    const orc = state.orcamento;
    if (orc && parseFloat(orc.total_proposta) > 0) {
      p('p-faturavel') && (p('p-faturavel').textContent = fmtBRL(orc.total_proposta));
      p('p-total')    && (p('p-total').textContent     = fmtBRL(orc.total_proposta));
      p('p-mlr')      && (p('p-mlr').textContent       = fmtPct(orc.margem_liquida_real));
    }
    return;
  }

  const sub  = parseFloat(resultado.subtotal_faturavel)   || 0;
  const nfat = parseFloat(resultado.total_nao_faturavel)  || 0;
  const tot  = parseFloat(resultado.total_proposta)       || 0;
  const mlr  = parseFloat(resultado.margem_liquida_real)  || 0;
  const fk   = parseFloat(resultado.fator_k_percentual)   || 0;

  if (p('p-faturavel')) p('p-faturavel').textContent = fmtBRL(sub);
  if (p('p-diluir'))   p('p-diluir').textContent    = fmtBRL(nfat);
  if (p('p-fatork'))   p('p-fatork').textContent    = fk.toFixed(2) + '%';
  if (p('p-mlr'))      p('p-mlr').textContent       = (mlr * 100).toFixed(2) + '%';
  if (p('p-total'))    p('p-total').textContent     = fmtBRL(tot);

  // Remove aviso de "não calculado"
  document.querySelector('.painel-lateral [style*="warning"]')?.remove();
}

// ── Ações do editor ───────────────────────────────────────────────────────────

function wireEditorActions() {
  // Calcular
  document.getElementById('btn-calcular')?.addEventListener('click', async () => {
    const btn = document.getElementById('btn-calcular');
    btn.disabled = true; btn.textContent = 'Calculando…';
    try {
      const resultado = await orcamentoApi.calcular(state.orcamento.id);
      state.itens = resultado.itens;
      state.orcamento = { ...state.orcamento,
        total_proposta:      resultado.total_proposta,
        margem_liquida_real: resultado.margem_liquida_real,
      };
      state.dirtyRows.clear();
      state.calculado = true;
      renderGridRows();
      atualizarPainel(resultado);
      const hint = document.getElementById('hint-dirty');
      if (hint) hint.textContent = '';
      toast('Cálculo atualizado com sucesso', 'success');
    } catch (err) {
      toast(`Erro no cálculo: ${err.message}`, 'error');
    } finally {
      btn.disabled = false; btn.textContent = 'Calcular';
    }
  });

  // Aprovar
  document.getElementById('btn-aprovar')?.addEventListener('click', async () => {
    if (!confirm('Aprovar este orçamento? O grid ficará somente leitura e os valores serão congelados.')) return;
    try {
      const atualizado = await orcamentoApi.update(state.orcamento.id, { status: 'aprovado' });
      state.orcamento = atualizado;
      toast('Orçamento aprovado e congelado', 'success');
      const container = document.getElementById('page-content');
      if (container) buildEditorShell(container);
    } catch (err) {
      toast(`Erro: ${err.message}`, 'error');
    }
  });

  // Nova versão (orçamento aprovado)
  document.getElementById('btn-nova-versao')?.addEventListener('click', () => {
    toast('Nova versão: disponível na Fase 3', 'info');
  });

  // Exportar PDF
  document.getElementById('btn-exportar')?.addEventListener('click', async () => {
    const btn = document.getElementById('btn-exportar');
    if (btn) { btn.disabled = true; btn.textContent = 'Gerando PDF…'; }
    try {
      const orcId = state.orcamento.id;
      const token = (await import('../api.js')).auth.getAccessToken();
      const resp  = await fetch(`/api/v1/orcamentos/${orcId}/export/pdf`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail ?? `Erro ${resp.status}`);
      }
      const blob = await resp.blob();
      const url  = URL.createObjectURL(blob);
      const a    = document.createElement('a');
      a.href     = url;
      a.download = `proposta_${state.orcamento.numero_proposta}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
      toast('PDF gerado com sucesso', 'success');
    } catch (err) {
      toast(`Erro ao gerar PDF: ${err.message}`, 'error');
    } finally {
      if (btn) { btn.disabled = false; btn.textContent = 'Exportar'; }
    }
  });

  // Adicionar serviço
  document.getElementById('btn-add-servico')?.addEventListener('click', () => {
    openModalAddItem('servicos');
  });

  // Adicionar produto
  document.getElementById('btn-add-produto')?.addEventListener('click', () => {
    openModalAddItem('produtos');
  });

  // Adicionar operacional
  document.getElementById('btn-add-operacional')?.addEventListener('click', () => {
    openModalAddItem('operacional');
  });

  // Adicionar manual
  document.getElementById('btn-add-manual')?.addEventListener('click', () => {
    openModalAddItem('excepcionais');
  });
}

// ── Modal adicionar item ──────────────────────────────────────────────────────

function openModalAddItem(bloco) {
  const isFaturavel = bloco === 'servicos' || bloco === 'produtos';
  const isServico = bloco === 'servicos';
  const labels = {
    servicos: 'Serviço',
    produtos: 'Produto',
    operacional: 'Custo Operacional',
    excepcionais: 'Custo Excepcional / Manual',
  };

  const fichas = isServico ? state.fichasServico : state.fichasProduto;
  const fichaSelect = (bloco === 'servicos' || bloco === 'produtos') ? `
    <div class="form-group" style="grid-column:span 2">
      <label class="form-label">Ficha Técnica</label>
      <select id="sel-ficha" class="form-control">
        <option value="">Selecione para pré-preencher (opcional)…</option>
        ${fichas.map(f => `<option value="${f.id}" data-nome="${esc(f.nome)}" data-und="${esc(f.unidade_medida ?? 'un')}">${esc(f.codigo)} — ${esc(f.nome)}</option>`).join('')}
      </select>
    </div>` : '';

  const backdrop = document.createElement('div');
  backdrop.className = 'modal-backdrop';
  backdrop.innerHTML = `
  <div class="modal">
    <div class="modal-header">
      <h3>Adicionar ${labels[bloco]}</h3>
      <button class="btn btn-ghost btn-icon btn-fechar">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
      </button>
    </div>
    <form id="form-add-item">
      <div class="modal-body" style="display:grid;grid-template-columns:1fr 1fr;gap:1rem">
        ${fichaSelect}
        <div class="form-group" style="grid-column:span 2">
          <label class="form-label">Descrição *</label>
          <input name="descricao" id="inp-descricao" type="text" class="form-control" required placeholder="Descrição do item…" />
        </div>
        <div class="form-group">
          <label class="form-label">Unidade *</label>
          <input name="unidade_medida" id="inp-unidade" type="text" class="form-control" required value="un" />
        </div>
        <div class="form-group">
          <label class="form-label">Quantidade *</label>
          <input name="quantidade" type="number" class="form-control" required value="1" min="0.0001" step="0.01" />
        </div>
        <div class="form-group">
          <label class="form-label">Custo Direto Unit. (R$) *</label>
          <input name="custo_direto_unitario" type="number" class="form-control" required value="0" min="0" step="0.01" />
        </div>
        ${isFaturavel ? `
        <div class="form-group">
          <label class="form-label">MOD FAT</label>
          <select name="mod_fat" class="form-control">
            <option value="BDI-MAT+MO">BDI-MAT+MO</option>
            <option value="BDI-MO">BDI-MO</option>
            <option value="BDI+ICMS">BDI+ICMS</option>
            <option value="FAT DIR SIMP">FAT DIR SIMP</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">Margem (%)</label>
          <input name="margem_percentual" type="number" class="form-control" value="10" min="0" max="99.9" step="0.1" />
        </div>` : `
        <input type="hidden" name="mod_fat" value="-" />
        <input type="hidden" name="margem_percentual" value="0" />`}
        ${bloco === 'excepcionais' ? `<input type="hidden" name="item_excepcional" value="true" />` : ''}
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary btn-fechar">Cancelar</button>
        <button type="submit" class="btn btn-primary" id="btn-salvar-item">Adicionar Item</button>
      </div>
    </form>
  </div>`;

  document.body.appendChild(backdrop);
  backdrop.querySelectorAll('.btn-fechar').forEach(b => b.addEventListener('click', () => backdrop.remove()));
  backdrop.addEventListener('click', e => { if (e.target === backdrop) backdrop.remove(); });

  // Auto-preencher descrição/unidade ao selecionar ficha
  const selFicha = backdrop.querySelector('#sel-ficha');
  if (selFicha) {
    selFicha.addEventListener('change', () => {
      const opt = selFicha.selectedOptions[0];
      if (opt?.value) {
        const descEl = backdrop.querySelector('#inp-descricao');
        const undEl  = backdrop.querySelector('#inp-unidade');
        if (descEl) descEl.value = opt.dataset.nome ?? '';
        if (undEl)  undEl.value  = opt.dataset.und  ?? 'un';
      }
    });
  }

  backdrop.querySelector('#form-add-item').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('btn-salvar-item');
    btn.disabled = true; btn.textContent = 'Adicionando…';

    const fd = new FormData(e.target);
    const payload = {
      bloco,
      descricao:             fd.get('descricao'),
      unidade_medida:        fd.get('unidade_medida'),
      quantidade:            fd.get('quantidade'),
      custo_direto_unitario: fd.get('custo_direto_unitario'),
      mod_fat:               fd.get('mod_fat'),
      margem_percentual:     String(parseFloat(fd.get('margem_percentual') ?? '0') / 100),
      item_excepcional:      fd.get('item_excepcional') === 'true',
    };

    const fichaId = selFicha?.value ? Number(selFicha.value) : null;
    if (fichaId) {
      if (bloco === 'servicos') payload.ficha_servico_id = fichaId;
      else if (bloco === 'produtos') payload.ficha_produto_id = fichaId;
    }

    try {
      const novoItem = await orcamentoApi.addItem(state.orcamento.id, payload);
      state.itens.push(novoItem);
      state.calculado = false;
      renderGridRows();
      atualizarPainel();
      backdrop.remove();
      toast('Item adicionado', 'success');
    } catch (err) {
      toast(`Erro: ${err.message}`, 'error');
      btn.disabled = false; btn.textContent = 'Adicionar Item';
    }
  });

  backdrop.querySelector('input:not([type=hidden])')?.focus();
}

// ── Helpers de formatação ─────────────────────────────────────────────────────

function fmtBRL(v) {
  const n = parseFloat(v) || 0;
  return n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

function fmtNum(v) {
  const n = parseFloat(v) || 0;
  return n.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 4 });
}

function fmtPct(v) {
  const n = parseFloat(v) || 0;
  return (n * 100).toFixed(2) + '%';
}

function esc(s) {
  if (s == null) return '';
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function badgeStatus(s) {
  const map = {
    rascunho:  ['neutral',  'Rascunho'],
    enviado:   ['warning',  'Enviado'],
    aprovado:  ['success',  'Aprovado'],
    rejeitado: ['danger',   'Rejeitado'],
  };
  const [cls, label] = map[s] ?? ['neutral', s];
  return `<span class="badge badge-${cls}">${label}</span>`;
}

function bloqueBadge(b) {
  const map = {
    servicos:     ['primary', 'Serviço'],
    produtos:     ['info',    'Produto'],
    operacional:  ['warning', 'Oper.'],
    excepcionais: ['danger',  'Excep.'],
  };
  const [cls, label] = map[b] ?? ['neutral', b];
  return `<span class="badge badge-${cls}" style="font-size:.6875rem">${label}</span>`;
}
