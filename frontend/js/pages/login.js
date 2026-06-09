/**
 * login.js — Tela de autenticação (Fase 3: login real via /api/v1/auth/login)
 */

import { api, auth } from '../api.js';
import { toast } from '../app.js';

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
          placeholder="seuemail@altanoroeste.com.br"
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

    const email = emailEl.value.trim();
    const senha = passEl.value;

    if (!email || !senha) {
      showError('Preencha e-mail e senha.');
      return;
    }

    btn.textContent = 'Entrando…';
    btn.disabled = true;

    try {
      const data = await api.post('/auth/login', { email, senha });
      auth.setTokens(data.access_token, data.refresh_token);
      auth.setUser({ email, nome: data.nome, papel: data.papel, id: data.usuario_id });
      toast('Bem-vindo ao Sinalys!', 'success');
      window.location.hash = '#/dashboard';
    } catch (err) {
      showError(err.status === 401 ? 'E-mail ou senha incorretos.' : err.message);
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
