/**
 * bds.js — Telas de Bancos de Dados (RH, EPI, Frotas, Materiais, Estrutura, Despesas)
 * Listagem com tabela + botão "Novo" → modal de cadastro simples.
 */

import { bdApi } from '../api.js';
import { toast } from '../app.js';

// ── Configuração de cada BD ───────────────────────────────────────────────────

const BD_CONFIG = {
  rh: {
    title: 'Recursos Humanos',
    cols: ['Código', 'Cargo', 'Categoria', 'Salário Base', 'Custo/hora', 'Status'],
    row: (r) => {
      const custoHora = (parseFloat(r.salario_base) * (1 + parseFloat(r.encargos_percentual)) / parseFloat(r.horas_mes)).toFixed(2);
      return [
        r.codigo,
        `<strong>${r.cargo}</strong>`,
        badgeCat(r.categoria),
        `R$ ${parseFloat(r.salario_base).toLocaleString('pt-BR', {minimumFractionDigits:2})}`,
        `R$ ${custoHora}`,
        r.ativo ? badge('Ativo','success') : badge('Inativo','neutral'),
      ];
    },
    list:   () => bdApi.listRH(),
    delete: (id) => bdApi.deleteRH(id),
    formFields: [
      { name: 'codigo',    label: 'Código',     type: 'text',   required: true, placeholder: 'RH-001' },
      { name: 'cargo',     label: 'Cargo',      type: 'text',   required: true, placeholder: 'Encarregado Geral' },
      { name: 'categoria', label: 'Categoria',  type: 'select', required: true, options: ['OPERACIONAL','TECNICO','ADMINISTRATIVO'] },
      { name: 'salario_base',         label: 'Salário Base (R$)',  type: 'number', required: true, step:'0.01', min:'0' },
      { name: 'encargos_percentual',  label: 'Encargos (decimal)', type: 'number', required: true, step:'0.0001', value:'0.72' },
      { name: 'horas_mes',            label: 'Horas/Mês',          type: 'number', required: true, step:'0.01', value:'220' },
    ],
    create: (d) => bdApi.createRH(d),
  },

  epi: {
    title: 'EPIs',
    cols: ['Código', 'Descrição', 'Und', 'Custo Unit.', 'Vida Útil', 'Status'],
    row: (r) => [
      r.codigo,
      r.descricao,
      r.unidade_medida,
      `R$ ${parseFloat(r.custo_unitario).toLocaleString('pt-BR',{minimumFractionDigits:2})}`,
      r.vida_util_dias ? `${r.vida_util_dias} dias` : '—',
      r.ativo ? badge('Ativo','success') : badge('Inativo','neutral'),
    ],
    list:   () => bdApi.listEPI(),
    delete: (id) => bdApi.deleteEPI(id),
    formFields: [
      { name: 'codigo',        label: 'Código',       type: 'text',   required: true  },
      { name: 'descricao',     label: 'Descrição',    type: 'text',   required: true  },
      { name: 'unidade_medida',label: 'Unidade',      type: 'text',   required: true, placeholder: 'un, par…' },
      { name: 'custo_unitario',label: 'Custo Unit. (R$)', type: 'number', required: true, step:'0.01', min:'0' },
      { name: 'vida_util_dias',label: 'Vida Útil (dias)', type: 'number', step:'1', min:'1' },
    ],
    create: (d) => bdApi.createEPI(d),
  },

  frotas: {
    title: 'Frotas',
    cols: ['Código', 'Descrição', 'Tipo', 'Diária', 'R$/km', 'Status'],
    row: (r) => [
      r.codigo,
      r.descricao,
      badgeCat(r.tipo),
      `R$ ${parseFloat(r.custo_diaria).toLocaleString('pt-BR',{minimumFractionDigits:2})}`,
      r.custo_km ? `R$ ${parseFloat(r.custo_km).toFixed(2)}` : '—',
      r.ativo ? badge('Ativo','success') : badge('Inativo','neutral'),
    ],
    list:   () => bdApi.listFrotas(),
    delete: (id) => bdApi.deleteFrota(id),
    formFields: [
      { name: 'codigo',      label: 'Código',    type: 'text',   required: true },
      { name: 'descricao',   label: 'Descrição', type: 'text',   required: true },
      { name: 'tipo',        label: 'Tipo',      type: 'select', required: true, options: ['VEICULO_LEVE','VEICULO_PESADO','EQUIPAMENTO','PRANCHA'] },
      { name: 'custo_diaria',label: 'Diária (R$)', type: 'number', required: true, step:'0.01', min:'0' },
      { name: 'custo_km',    label: 'R$/km (opcional)', type: 'number', step:'0.01', min:'0' },
    ],
    create: (d) => bdApi.createFrota(d),
  },

  materiais: {
    title: 'Materiais',
    cols: ['Código', 'Descrição', 'Categoria', 'Und', 'Custo Unit.', 'ICMS', 'Status'],
    row: (r) => [
      r.codigo,
      r.descricao,
      badgeCat(r.categoria),
      r.unidade_medida,
      `R$ ${parseFloat(r.custo_unitario).toLocaleString('pt-BR',{minimumFractionDigits:2})}`,
      r.icms_incide ? badge('Sim','warning') : badge('Não','neutral'),
      r.ativo ? badge('Ativo','success') : badge('Inativo','neutral'),
    ],
    list:   () => bdApi.listMat(),
    delete: (id) => bdApi.deleteMat(id),
    formFields: [
      { name: 'codigo',        label: 'Código',    type: 'text',   required: true },
      { name: 'descricao',     label: 'Descrição', type: 'text',   required: true },
      { name: 'categoria',     label: 'Categoria', type: 'select', required: true, options: ['PLACA','PELICULA','TINTA','PERFIL','PARAFUSO','OUTROS'] },
      { name: 'unidade_medida',label: 'Unidade',   type: 'text',   required: true },
      { name: 'custo_unitario',label: 'Custo Unit. (R$)', type: 'number', required: true, step:'0.01', min:'0' },
      { name: 'fornecedor',    label: 'Fornecedor (opcional)', type: 'text' },
    ],
    create: (d) => bdApi.createMat(d),
  },

  estrutura: {
    title: 'Estrutura Operacional',
    cols: ['Código', 'Descrição', 'Tipo', 'Und', 'Custo Unit.', 'Status'],
    row: (r) => [
      r.codigo,
      r.descricao,
      badgeCat(r.tipo),
      r.unidade_medida,
      `R$ ${parseFloat(r.custo_unitario).toLocaleString('pt-BR',{minimumFractionDigits:2})}`,
      r.ativo ? badge('Ativo','success') : badge('Inativo','neutral'),
    ],
    list:   () => bdApi.listEst(),
    delete: (id) => bdApi.deleteEst(id),
    formFields: [
      { name: 'codigo',        label: 'Código',    type: 'text',   required: true },
      { name: 'descricao',     label: 'Descrição', type: 'text',   required: true },
      { name: 'tipo',          label: 'Tipo',      type: 'select', required: true, options: ['ALOJAMENTO','LOGISTICA','MOBILIZACAO','COMUNICACAO','OUTROS'] },
      { name: 'unidade_medida',label: 'Unidade',   type: 'text',   required: true },
      { name: 'custo_unitario',label: 'Custo Unit. (R$)', type: 'number', required: true, step:'0.01', min:'0' },
    ],
    create: (d) => bdApi.createEst(d),
  },

  despesas: {
    title: 'Despesas',
    cols: ['Código', 'Descrição', 'Tipo', 'Percentual', 'Valor Fixo', 'Status'],
    row: (r) => [
      r.codigo,
      r.descricao,
      badgeCat(r.tipo),
      r.percentual ? `${(parseFloat(r.percentual)*100).toFixed(2)}%` : '—',
      r.valor_fixo  ? `R$ ${parseFloat(r.valor_fixo).toLocaleString('pt-BR',{minimumFractionDigits:2})}` : '—',
      r.ativo ? badge('Ativo','success') : badge('Inativo','neutral'),
    ],
    list:   () => bdApi.listDesp(),
    delete: (id) => bdApi.deleteDesp(id),
    formFields: [
      { name: 'codigo',     label: 'Código',    type: 'text',   required: true },
      { name: 'descricao',  label: 'Descrição', type: 'text',   required: true },
      { name: 'tipo',       label: 'Tipo',      type: 'select', required: true, options: ['ADMINISTRATIVA','FINANCEIRA','SEGURO','OUTROS'] },
      { name: 'percentual', label: 'Percentual (decimal, ex: 0.13)', type: 'number', step:'0.0001' },
      { name: 'valor_fixo', label: 'Valor Fixo (R$, ex: 1500)',      type: 'number', step:'0.01' },
    ],
    create: (d) => bdApi.createDesp(d),
  },
};

// ── Render principal ──────────────────────────────────────────────────────────

export async function renderBDs(container, section = 'rh') {
  const cfg = BD_CONFIG[section];
  if (!cfg) {
    container.innerHTML = `<div class="placeholder-page"><h3>Módulo não encontrado: ${section}</h3></div>`;
    return;
  }

  container.innerHTML = `
  <div class="page-title">
    <h2>${cfg.title}</h2>
    <p>Cadastro e atualização de insumos</p>
  </div>

  <div class="list-toolbar">
    <div class="search-box">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
      </svg>
      <input type="text" id="search-input" class="form-control" placeholder="Filtrar…" />
    </div>
    <button class="btn btn-primary btn-sm" id="btn-novo">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="width:14px;height:14px"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
      Novo
    </button>
  </div>

  <div class="table-wrap card">
    <table class="data-table">
      <thead>
        <tr>${cfg.cols.map(c => `<th>${c}</th>`).join('')}<th></th></tr>
      </thead>
      <tbody id="bd-tbody">
        <tr><td colspan="${cfg.cols.length + 1}" style="text-align:center;padding:2rem;color:var(--text-muted)">
          <div class="spinner" style="margin:0 auto"></div>
        </td></tr>
      </tbody>
    </table>
  </div>
  `;

  document.getElementById('btn-novo').addEventListener('click', () => openModal(cfg, section, null, refresh));

  const searchEl = document.getElementById('search-input');
  searchEl.addEventListener('input', () => {
    const q = searchEl.value.toLowerCase();
    document.querySelectorAll('#bd-tbody tr[data-id]').forEach(tr => {
      tr.style.display = tr.textContent.toLowerCase().includes(q) ? '' : 'none';
    });
  });

  let allRows = [];
  async function refresh() {
    try {
      allRows = await cfg.list();
      renderTable(allRows, cfg, section, refresh);
    } catch (err) {
      document.getElementById('bd-tbody').innerHTML =
        `<tr><td colspan="${cfg.cols.length + 1}" style="text-align:center;color:var(--danger)">Erro: ${err.message}</td></tr>`;
    }
  }

  await refresh();
}

function renderTable(rows, cfg, section, refresh) {
  const tbody = document.getElementById('bd-tbody');
  if (!tbody) return;

  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="${cfg.cols.length + 1}" style="text-align:center;padding:2rem;color:var(--text-muted)">Nenhum registro encontrado.</td></tr>`;
    return;
  }

  tbody.innerHTML = rows.map(r => {
    const cells = cfg.row(r).map(c => `<td>${c}</td>`).join('');
    return `<tr data-id="${r.id}">
      ${cells}
      <td style="text-align:right">
        <button class="btn btn-ghost btn-sm btn-del" data-id="${r.id}" title="Excluir">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;color:var(--danger)"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6M14 11v6"/><path d="M9 6V4h6v2"/></svg>
        </button>
      </td>
    </tr>`;
  }).join('');

  // Bind delete buttons
  tbody.querySelectorAll('.btn-del').forEach(btn => {
    btn.addEventListener('click', async () => {
      const id = Number(btn.dataset.id);
      if (!confirm('Excluir este registro?')) return;
      try {
        await cfg.delete(id);
        toast('Registro excluído', 'success');
        await refresh();
      } catch (err) {
        toast(`Erro: ${err.message}`, 'error');
      }
    });
  });
}

// ── Modal de cadastro ─────────────────────────────────────────────────────────

function openModal(cfg, section, existing, onSave) {
  const isEdit = !!existing;
  const backdrop = document.createElement('div');
  backdrop.className = 'modal-backdrop';

  const fields = cfg.formFields.map(f => {
    const val = existing?.[f.name] ?? f.value ?? '';
    if (f.type === 'select') {
      const opts = f.options.map(o => `<option value="${o}" ${o === val ? 'selected' : ''}>${o}</option>`).join('');
      return `<div class="form-group">
        <label class="form-label">${f.label}${f.required ? ' *' : ''}</label>
        <select name="${f.name}" class="form-control">${opts}</select>
      </div>`;
    }
    return `<div class="form-group">
      <label class="form-label">${f.label}${f.required ? ' *' : ''}</label>
      <input name="${f.name}" type="${f.type}" class="form-control"
        value="${val}"
        ${f.required ? 'required' : ''}
        ${f.placeholder ? `placeholder="${f.placeholder}"` : ''}
        ${f.step ? `step="${f.step}"` : ''}
        ${f.min  ? `min="${f.min}"` : ''}
      />
    </div>`;
  }).join('');

  backdrop.innerHTML = `
  <div class="modal" role="dialog" aria-modal="true">
    <div class="modal-header">
      <h3>${isEdit ? 'Editar' : 'Novo'} — ${cfg.title}</h3>
      <button class="btn btn-ghost btn-icon btn-close-modal" aria-label="Fechar">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
      </button>
    </div>
    <form id="modal-form">
      <div class="modal-body" style="display:grid;grid-template-columns:1fr 1fr;gap:1rem">
        ${fields}
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary btn-close-modal">Cancelar</button>
        <button type="submit" class="btn btn-primary" id="modal-submit">
          ${isEdit ? 'Salvar' : 'Criar'}
        </button>
      </div>
    </form>
  </div>`;

  document.body.appendChild(backdrop);

  backdrop.querySelectorAll('.btn-close-modal').forEach(b => {
    b.addEventListener('click', () => backdrop.remove());
  });
  backdrop.addEventListener('click', (e) => { if (e.target === backdrop) backdrop.remove(); });

  backdrop.querySelector('#modal-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const submitBtn = backdrop.querySelector('#modal-submit');
    const fd = new FormData(e.target);
    const data = {};
    for (const [k, v] of fd.entries()) {
      data[k] = v === '' ? null : v;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = 'Salvando…';
    try {
      await cfg.create(data);
      toast('Registro salvo com sucesso', 'success');
      backdrop.remove();
      await onSave();
    } catch (err) {
      toast(`Erro: ${err.message}`, 'error');
      submitBtn.disabled = false;
      submitBtn.textContent = isEdit ? 'Salvar' : 'Criar';
    }
  });

  // Foco no primeiro campo
  backdrop.querySelector('input, select')?.focus();
}

// ── Badge helpers ─────────────────────────────────────────────────────────────

function badge(text, type) {
  return `<span class="badge badge-${type}">${text}</span>`;
}

function badgeCat(text) {
  const map = {
    OPERACIONAL:'primary', TECNICO:'blue', ADMINISTRATIVO:'neutral',
    PLACA:'primary', PELICULA:'blue', TINTA:'amber', PERFIL:'green', PARAFUSO:'neutral',
    VEICULO_LEVE:'blue', VEICULO_PESADO:'primary', EQUIPAMENTO:'amber', PRANCHA:'purple',
    ALOJAMENTO:'blue', LOGISTICA:'green', MOBILIZACAO:'amber', COMUNICACAO:'neutral',
    ADMINISTRATIVA:'primary', FINANCEIRA:'blue', SEGURO:'amber',
  };
  const cls = map[text] ?? 'neutral';
  return `<span class="badge badge-${cls}">${text}</span>`;
}
