# AGENTS.md — Guia para Agentes de IA

Instruções para agentes de IA (Claude Code, Copilot, Codex, etc.) que trabalham neste repositório.

---

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Backend | FastAPI 0.133 + SQLAlchemy 2.0 (sync) + Pydantic v2 |
| Auth | PyJWT HS256 + bcrypt 5.x direto (sem passlib) |
| Banco | SQLite (dev/testes) → PostgreSQL 16 (produção) |
| Frontend | Vanilla JS · Hash-based SPA · ES Modules · sem frameworks |
| PDF | WeasyPrint 69 — CSS inline, sem URLs externas |
| Deploy | Docker multi-stage + docker-compose + Caddy |
| CI/CD | GitHub Actions (lint + test + security + deploy) |

---

## Regras Inegociáveis

- **Decimal para TUDO.** Nunca `float` em valores monetários ou percentuais.
- **NUNCA UPDATE em `orcamento_itens`** quando `status=aprovado`. Usar `_guard_rascunho()`.
- **SEM frameworks JS.** Vanilla JS puro — sem React, Vue, Alpine etc.
- **ORM exclusivo.** Sem raw SQL concatenado. SQLAlchemy ORM + parâmetros sempre.
- **Commits em português** seguindo Conventional Commits (ver seção abaixo).

---

## Estrutura do Projeto

```
backend/
  auth.py               — JWT + bcrypt + get_current_user
  config.py             — Settings (pydantic-settings, .env)
  database.py           — engine, SessionLocal, get_db, Base
  main.py               — app FastAPI, middleware, routers, StaticFiles
  middleware.py         — AuthMiddleware ASGI + RBAC por prefixo
  models/               — SQLAlchemy Mapped[] models
  routers/              — endpoints FastAPI
  schemas/              — Pydantic v2 schemas
  services/
    export_pdf.py       — WeasyPrint PDF generator
    motor_bdi.py        — motor de cálculo BDI/Fator K/MLR
  seeds.py              — seed de desenvolvimento
  seeds_prod.py         — seed de produção (senhas via env)

frontend/
  index.html            — SPA entry point
  css/style.css         — design system glassmorphism + dark mode
  js/
    api.js              — fetch wrapper /api/v1
    app.js              — router hash-based + sidebar + auth
    pages/              — módulo por tela (dashboard, orcamentos, etc.)

tests/                  — pytest, SQLite in-memory, TestClient httpx
docs/                   — documentação técnica
```

---

## Padrões de Código

### Backend (Python)
- `black` + `isort --profile black` — formatação obrigatória antes de commit
- Type hints em toda função pública: `Mapped[]`, `list[X]`, `X | None`
- `_guard_rascunho(orc)` em toda mutação de orçamento/item
- `_get_or_404(db, Model, pk)` para lookups por PK
- Paginação `skip: int = 0, limit: int = Query(100, le=500)` em list endpoints
- `html.escape()` em todo dado de usuário interpolado em HTML/PDF

### Frontend (JavaScript)
- ES Modules (`import/export`) — sem bundler, sem transpilação
- Cada tela = um arquivo em `frontend/js/pages/`
- `api.js` centraliza todos os `fetch` para `/api/v1/`
- Dark mode via classe `.dark` no `:root` + `localStorage`

### Testes
- `pytest tests/ -q` deve passar sem falhas antes de qualquer commit
- Banco: SQLite in-memory via `StaticPool` (sem dependência de Postgres em CI)
- Fixtures em `tests/conftest.py`

---

## Máquina de Estados do Orçamento

```
rascunho → enviado → aprovado
                  ↘ rejeitado → rascunho
```

Transições fora desta sequência retornam HTTP 422.
`aprovado` é terminal — nenhuma edição permitida.

---

## RBAC — Papéis e Permissões

| Papel | Acesso |
|-------|--------|
| `orcamentista` | clientes, orçamentos, dashboard |
| `parametrizador` | fichas, clientes, orçamentos, dashboard |
| `gestor_bd` | bd-*, clientes, dashboard |
| `sponsor` | tudo |

Definido em `backend/middleware.py → _RBAC`.

---

## Variáveis de Ambiente

| Variável | Obrigatório em produção | Default dev |
|----------|------------------------|-------------|
| `JWT_SECRET` | Sim (≥ 32 chars) | placeholder inseguro (warning no startup) |
| `DATABASE_URL` | Sim | `sqlite:///./sinalys.db` |
| `DEBUG` | Não | `False` |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | Para seeds_prod | — |

---

## Fluxo de Branches e PRs

- `main`: branch protegida (requer PR)
- `feat/<nome>`: branches de feature
- `fix/<nome>`: branches de correção

Fluxo:
1. Criar branch: `git checkout -b feat/nome-da-feature`
2. Desenvolver + commits atômicos
3. Abrir PR contra `main`
4. CI roda automaticamente (lint + test + security)
5. Revisão + merge (squash recomendado)

Commits seguem conventional commits:
- `feat:` nova funcionalidade
- `fix:` correção de bug
- `style:` formatação (black/isort)
- `chore:` tarefas de manutenção
- `docs:` documentação
- `refactor:` refatoração sem mudança de comportamento

Não commitar direto na `main` nas próximas fases.
