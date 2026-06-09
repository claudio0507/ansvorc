/**
 * clientes.js — CRM básico: tabela, busca, modal criar/editar, vínculo com orçamentos
 */

import { clienteApi, orcamentoApi } from '../api.js';
import { toast } from '../app.js';

// ── Entry point ───────────────────────────────────────────────────────────────

export async function renderClientes(container) {
  container.innerHTML = `
  <div class="page-title">
    <h2>Clientes</h2>
    <p>Cadastro de contratantes e histórico de propostas</p>
  </div>

  <div class="list-toolbar">
    <div style="position:relative;flex:1;max-width:380px">
      <svg style="position:absolute;left:.75rem;top:50%;transform:translateY(-50%);width:15px;height:15px;color:var(--text-muted);pointer-events:none"
           viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
      </svg>
      <input id="cli-busca" type="text" class="form-control"
             placeholder="Buscar por nome ou CNPJ…"
             style="padding-left:2.25rem" />
    </div>
    <div style="display:flex;gap:.5rem">
      <label style="display:flex;align-items:center;gap:.375rem;font-size:.875rem;cursor:pointer">
        <input type="checkbox" id="cli-so-ativos" checked style="accent-color:var(--primary)" />
        Somente ativos
      </label>
      <button class="btn btn-primary btn-sm" id="btn-novo-cli">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="width:14px;height:14px">
          <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
        Novo Cliente
      </button>
    </div>
  </div>

  <div class="card">
    <table class="data-table" id="cli-table">
      <thead>
        <tr>
          <th>Razão Social</th>
          <th>CNPJ/CPF</th>
          <th>Contato</th>
          <th>UF Sede</th>
          <th>Status</th>
          <th>Orçamentos</th>
          <th></th>
        </tr>
      </thead>
      <tbody id="cli-tbody">
        <tr><td colspan="7" style="text-align:center;padding:2rem">
          <div class="spinner" style="margin:0 auto"></div>
        </td></tr>
      </tbody>
    </table>
  </div>`;

  let todos = [];
  let busca = '';
  let soAtivos = true;

  document.getElementById('cli-busca').addEventListener('input', (e) => {
    busca = e.target.value.toLowerCase();
    render(todos);
  });

  document.getElementById('cli-so-ativos').addEventListener('change', (e) => {
    soAtivos = e.target.checked;
    render(todos);
  });

  document.getElementById('btn-novo-cli').addEventListener('click', () => {
    openModal(null, async () => { todos = await clienteApi.list(); render(todos); });
  });

  try {
    todos = await clienteApi.list();
    render(todos);
  } catch (err) {
    document.getElementById('cli-tbody').innerHTML =
      `<tr><td colspan="7" style="text-align:center;color:var(--danger)">${err.message}</td></tr>`;
  }

  function render(lista) {
    let filtrados = lista;
    if (soAtivos) filtrados = filtrados.filter(c => c.ativo);
    if (busca) filtrados = filtrados.filter(c =>
      c.razao_social.toLowerCase().includes(busca) ||
      (c.cnpj ?? '').toLowerCase().includes(busca)
    );
    renderTabela(filtrados, () => { todos = lista; render(lista); });
  }
}

// ── Tabela ────────────────────────────────────────────────────────────────────

function renderTabela(clientes, onRefresh) {
  const tbody = document.getElementById('cli-tbody');
  if (!tbody) return;

  if (!clientes.length) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:2rem;color:var(--text-muted)">
      Nenhum cliente encontrado.</td></tr>`;
    return;
  }

  tbody.innerHTML = clientes.map(c => `
    <tr>
      <td>
        <div style="font-weight:500">${esc(c.razao_social)}</div>
        ${c.contato_email ? `<div style="font-size:.75rem;color:var(--text-muted)">${esc(c.contato_email)}</div>` : ''}
      </td>
      <td style="font-size:.8125rem">${esc(c.cnpj ?? '—')}</td>
      <td style="font-size:.8125rem">
        ${esc(c.contato_nome ?? '—')}
        ${c.contato_telefone ? `<div style="color:var(--text-muted)">${esc(c.contato_telefone)}</div>` : ''}
      </td>
      <td>${c.uf_sede ? `<span class="badge badge-neutral">${c.uf_sede}</span>` : '—'}</td>
      <td>${c.ativo
        ? '<span class="badge badge-success">Ativo</span>'
        : '<span class="badge badge-danger">Inativo</span>'
      }</td>
      <td>
        <button class="btn btn-ghost btn-sm btn-ver-orc" data-id="${c.id}" data-nome="${esc(c.razao_social)}"
                style="font-size:.8125rem">Ver →</button>
      </td>
      <td style="display:flex;gap:.25rem;justify-content:flex-end">
        <button class="btn btn-ghost btn-sm btn-edit-cli" data-id="${c.id}" title="Editar">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px">
            <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
            <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
          </svg>
        </button>
        <button class="btn btn-ghost btn-sm btn-toggle-cli" data-id="${c.id}" data-ativo="${c.ativo}" title="${c.ativo ? 'Desativar' : 'Ativar'}">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;color:${c.ativo ? 'var(--warning)' : 'var(--success)'}">
            ${c.ativo
              ? '<path d="M18.36 6.64a9 9 0 11-12.73 0"/><line x1="12" y1="2" x2="12" y2="12"/>'
              : '<path d="M12 2v10m6.36-3.36a9 9 0 11-12.72 0"/>'}
          </svg>
        </button>
      </td>
    </tr>`).join('');

  // Ver orçamentos do cliente
  tbody.querySelectorAll('.btn-ver-orc').forEach(btn => {
    btn.addEventListener('click', () => openOrcamentosDoCliente(Number(btn.dataset.id), btn.dataset.nome));
  });

  // Editar
  tbody.querySelectorAll('.btn-edit-cli').forEach(btn => {
    btn.addEventListener('click', async () => {
      const cli = (await clienteApi.list()).find(c => c.id === Number(btn.dataset.id));
      openModal(cli, onRefresh);
    });
  });

  // Toggle ativo
  tbody.querySelectorAll('.btn-toggle-cli').forEach(btn => {
    btn.addEventListener('click', async () => {
      const id    = Number(btn.dataset.id);
      const ativo = btn.dataset.ativo === 'true';
      try {
        await clienteApi.update(id, { ativo: !ativo });
        toast(!ativo ? 'Cliente ativado' : 'Cliente desativado', 'success');
        onRefresh();
      } catch (err) {
        toast(`Erro: ${err.message}`, 'error');
      }
    });
  });
}

// ── Modal criar / editar ──────────────────────────────────────────────────────

function openModal(cliente, onSave) {
  const editando = !!cliente;

  const backdrop = document.createElement('div');
  backdrop.className = 'modal-backdrop';
  backdrop.innerHTML = `
  <div class="modal">
    <div class="modal-header">
      <h3>${editando ? 'Editar Cliente' : 'Novo Cliente'}</h3>
      <button class="btn btn-ghost btn-icon btn-fechar" aria-label="Fechar">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </div>
    <form id="form-cliente">
      <div class="modal-body" style="display:grid;grid-template-columns:1fr 1fr;gap:1rem">
        <div class="form-group" style="grid-column:span 2">
          <label class="form-label">Razão Social / Nome *</label>
          <input name="razao_social" type="text" class="form-control" required
                 value="${esc(cliente?.razao_social ?? '')}"
                 placeholder="Ex: Motiva Rodovias S.A." />
        </div>
        <div class="form-group">
          <label class="form-label">CNPJ / CPF</label>
          <input name="cnpj" type="text" class="form-control"
                 value="${esc(cliente?.cnpj ?? '')}"
                 placeholder="00.000.000/0001-00" />
        </div>
        <div class="form-group">
          <label class="form-label">UF Sede</label>
          <select name="uf_sede" class="form-control">
            <option value="">—</option>
            ${['PR','SP','SC','RS','MG','RJ','GO','DF','BA','PE','CE'].map(uf =>
              `<option value="${uf}" ${(cliente?.uf_sede ?? '') === uf ? 'selected' : ''}>${uf}</option>`
            ).join('')}
          </select>
        </div>
        <div class="form-group" style="grid-column:span 2">
          <label class="form-label">Nome do Contato</label>
          <input name="contato_nome" type="text" class="form-control"
                 value="${esc(cliente?.contato_nome ?? '')}"
                 placeholder="Ex: João Silva" />
        </div>
        <div class="form-group">
          <label class="form-label">E-mail do Contato</label>
          <input name="contato_email" type="email" class="form-control"
                 value="${esc(cliente?.contato_email ?? '')}"
                 placeholder="joao@empresa.com" />
        </div>
        <div class="form-group">
          <label class="form-label">Telefone</label>
          <input name="contato_telefone" type="tel" class="form-control"
                 value="${esc(cliente?.contato_telefone ?? '')}"
                 placeholder="(41) 9 9999-9999" />
        </div>
        ${editando ? `
        <div class="form-group" style="grid-column:span 2;align-self:end">
          <label style="display:flex;align-items:center;gap:.5rem;cursor:pointer">
            <input type="checkbox" name="ativo" ${cliente.ativo ? 'checked' : ''}
                   style="width:18px;height:18px;accent-color:var(--primary)" />
            <span>Cliente ativo</span>
          </label>
        </div>` : ''}
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary btn-fechar">Cancelar</button>
        <button type="submit" class="btn btn-primary" id="btn-salvar-cli">
          ${editando ? 'Salvar Alterações' : 'Criar Cliente'}
        </button>
      </div>
    </form>
  </div>`;

  document.body.appendChild(backdrop);
  backdrop.querySelectorAll('.btn-fechar').forEach(b => b.addEventListener('click', () => backdrop.remove()));
  backdrop.addEventListener('click', e => { if (e.target === backdrop) backdrop.remove(); });

  backdrop.querySelector('#form-cliente').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('btn-salvar-cli');
    btn.disabled = true; btn.textContent = editando ? 'Salvando…' : 'Criando…';

    const fd = new FormData(e.target);
    const payload = {
      razao_social:      fd.get('razao_social'),
      cnpj:              fd.get('cnpj')             || null,
      uf_sede:           fd.get('uf_sede')           || null,
      contato_nome:      fd.get('contato_nome')      || null,
      contato_email:     fd.get('contato_email')     || null,
      contato_telefone:  fd.get('contato_telefone')  || null,
    };
    if (editando) payload.ativo = fd.get('ativo') === 'on';

    try {
      if (editando) {
        await clienteApi.update(cliente.id, payload);
        toast('Cliente atualizado', 'success');
      } else {
        await clienteApi.create(payload);
        toast('Cliente criado', 'success');
      }
      backdrop.remove();
      await onSave();
    } catch (err) {
      toast(`Erro: ${err.message}`, 'error');
      btn.disabled = false;
      btn.textContent = editando ? 'Salvar Alterações' : 'Criar Cliente';
    }
  });

  backdrop.querySelector('input[name="razao_social"]')?.focus();
}

// ── Painel de orçamentos do cliente ──────────────────────────────────────────

async function openOrcamentosDoCliente(clienteId, nomeCliente) {
  const backdrop = document.createElement('div');
  backdrop.className = 'modal-backdrop';
  backdrop.innerHTML = `
  <div class="modal" style="max-width:640px">
    <div class="modal-header">
      <h3>Orçamentos — ${esc(nomeCliente)}</h3>
      <button class="btn btn-ghost btn-icon btn-fechar">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </div>
    <div class="modal-body" id="orc-cli-body">
      <div class="spinner" style="margin:1rem auto;display:block"></div>
    </div>
    <div class="modal-footer">
      <button class="btn btn-secondary btn-fechar">Fechar</button>
    </div>
  </div>`;

  document.body.appendChild(backdrop);
  backdrop.querySelectorAll('.btn-fechar').forEach(b => b.addEventListener('click', () => backdrop.remove()));
  backdrop.addEventListener('click', e => { if (e.target === backdrop) backdrop.remove(); });

  try {
    const todos = await orcamentoApi.list();
    const doCliente = todos.filter(o => o.cliente_id === clienteId);
    const body = document.getElementById('orc-cli-body');

    if (!doCliente.length) {
      body.innerHTML = `<p style="color:var(--text-muted);text-align:center;padding:1rem">Nenhum orçamento vinculado.</p>`;
      return;
    }

    body.innerHTML = `
    <table class="data-table">
      <thead><tr><th>Nº Proposta</th><th>Obra</th><th>Status</th><th>Total</th><th></th></tr></thead>
      <tbody>
        ${doCliente.map(o => `<tr>
          <td><code style="color:var(--primary);font-size:.8125rem">${esc(o.numero_proposta)}</code></td>
          <td style="font-size:.8125rem;color:var(--text-muted)">${esc(o.descricao_obra ?? '—')}</td>
          <td>${badgeStatus(o.status)}</td>
          <td style="font-weight:600">${fmtBRL(o.total_proposta)}</td>
          <td><a href="#/orcamentos/${o.id}" class="btn btn-ghost btn-sm" onclick="document.querySelector('.modal-backdrop').remove()">Abrir →</a></td>
        </tr>`).join('')}
      </tbody>
    </table>`;
  } catch (err) {
    document.getElementById('orc-cli-body').innerHTML =
      `<p style="color:var(--danger)">${err.message}</p>`;
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function fmtBRL(v) {
  const n = parseFloat(v) || 0;
  return n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

function esc(s) {
  if (s == null) return '';
  return String(s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function badgeStatus(s) {
  const map = { rascunho: ['neutral','Rascunho'], enviado: ['warning','Enviado'],
                aprovado: ['success','Aprovado'], rejeitado: ['danger','Rejeitado'] };
  const [cls, label] = map[s] ?? ['neutral', s];
  return `<span class="badge badge-${cls}">${label}</span>`;
}
