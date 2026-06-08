/**
 * login.js — Tela de autenticação
 *
 * Fase de desenvolvimento: aceita qualquer credencial e grava um token
 * simulado + perfil de usuário. Quando o backend implementar /auth/login,
 * basta substituir a chamada `simulateLogin` por `api.post('/auth/login', ...)`.
 */

import { auth } from '../api.js';
import { toast } from '../app.js';

const PERFIS = {
  'gestor@alta.com':        { nome: 'Gestor BD',      papel: 'Gestor de BD' },
  'param@alta.com':         { nome: 'Parametrizador', papel: 'Parametrizador' },
  'orcamentista@alta.com':  { nome: 'Orçamentista',   papel: 'Orçamentista' },
};

export function renderLogin(container) {
  container.innerHTML = `
  <div class="login-card">
    <div class="login-logo">
      <div class="logo-badge">
        <svg viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5zm0 10L2 7v10l10 5 10-5V7l-10 5z"/></svg>
      </div>
      <h1>Sinalys</h1>
      <p>ERP de Orçamentação Viária</p>
    </div>

    <form id="login-form" novalidate>
      <div class="form-group">
        <label class="form-label" for="login-email">E-mail</label>
        <input
          id="login-email"
          type="email"
          class="form-control"
          placeholder="seuemail@alta.com"
          autocomplete="username"
          required
        />
      </div>

      <div class="form-group mt-4">
        <label class="form-label" for="login-password">Senha</label>
        <input
          id="login-password"
          type="password"
          class="form-control"
          placeholder="••••••••"
          autocomplete="current-password"
          required
        />
      </div>

      <div id="login-error" class="login-error hidden"></div>

      <button type="submit" class="login-submit" id="login-submit">
        Entrar
      </button>
    </form>

    <p style="text-align:center;margin-top:1.25rem;font-size:.8125rem;color:rgba(255,255,255,.3);">
      Dev: use qualquer e-mail + senha "admin"
    </p>
  </div>
  `;

  const form    = document.getElementById('login-form');
  const emailEl = document.getElementById('login-email');
  const passEl  = document.getElementById('login-password');
  const errEl   = document.getElementById('login-error');
  const btn     = document.getElementById('login-submit');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    errEl.classList.add('hidden');
    errEl.textContent = '';

    const email = emailEl.value.trim();
    const pass  = passEl.value;

    if (!email || !pass) {
      showError('Preencha e-mail e senha.');
      return;
    }

    btn.textContent = 'Entrando…';
    btn.disabled = true;

    try {
      await simulateLogin(email, pass);
      toast('Bem-vindo ao Sinalys!', 'success');
      window.location.hash = '#/dashboard';
    } catch (err) {
      showError(err.message);
    } finally {
      btn.textContent = 'Entrar';
      btn.disabled = false;
    }
  });

  function showError(msg) {
    errEl.textContent = msg;
    errEl.classList.remove('hidden');
  }
}

async function simulateLogin(email, password) {
  // Simula latência de rede
  await new Promise(r => setTimeout(r, 400));

  if (password !== 'admin') {
    throw new Error('Senha incorreta. (dev: use "admin")');
  }

  const perfil = PERFIS[email] ?? { nome: email.split('@')[0], papel: 'Operador' };

  // Token fictício para dev — substituir por JWT real quando backend implementar /auth
  const fakeToken = btoa(`${email}:${Date.now()}`);
  auth.setToken(fakeToken);
  auth.setUser({ email, ...perfil });
}
