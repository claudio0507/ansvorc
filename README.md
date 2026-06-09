# Sinalys — ERP de Orçamentação Viária

[![CI](https://github.com/claudiorf/ansvorc/actions/workflows/ci.yml/badge.svg)](https://github.com/claudiorf/ansvorc/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.133-green)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-orange)

ERP de orçamentação para a **Alta Noroeste Sinalização Viária** — cobre todo o ciclo de propostas comerciais: BDs de insumos, fichas técnicas, cálculo BDI/Fator K/MLR, CRM de clientes e exportação de propostas em PDF.

---

## Arquitetura

```
┌─────────────────────────────────────────────────┐
│                   Browser                        │
│       Vanilla JS · Hash SPA · Glassmorphism      │
└──────────────────────┬──────────────────────────┘
                       │ HTTPS (Caddy reverse proxy)
┌──────────────────────▼──────────────────────────┐
│            FastAPI 0.133 + Uvicorn               │
│  Auth (JWT/bcrypt) · RBAC Middleware · REST API  │
└──────────┬───────────────────────┬──────────────┘
           │ SQLAlchemy 2.0        │ WeasyPrint
┌──────────▼──────────┐  ┌────────▼────────────────┐
│  PostgreSQL 16       │  │  PDF proposals           │
│  (SQLite em dev)     │  │  A4 landscape CSS-only   │
└─────────────────────┘  └─────────────────────────┘
```

---

## Início rápido (desenvolvimento local)

```bash
# Clonar e criar ambiente virtual
git clone https://github.com/claudiorf/ansvorc.git
cd ansvorc
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Seed de dados de exemplo
python -m backend.seeds

# Iniciar servidor
uvicorn backend.main:app --reload
# → http://localhost:8000
```

Credenciais de desenvolvimento:

| E-mail                          | Senha    | Papel            |
|---------------------------------|----------|------------------|
| admin@altanoroeste.com.br       | admin123 | gestor_bd        |
| param@altanoroeste.com.br       | param123 | parametrizador   |
| orc@altanoroeste.com.br         | orc123   | orcamentista     |

---

## Deploy com Docker Compose

```bash
# 1. Copiar e editar variáveis de ambiente
cp .env.example .env
# Edite .env: defina JWT_SECRET e DB_PASSWORD

# 2. Subir os serviços (app + PostgreSQL)
docker compose up -d

# 3. Verificar saúde
curl http://localhost:8000/health
# → {"status": "ok", "version": "1.0.0"}

# 4. Swagger
# → http://localhost:8000/docs
```

### Deploy com HTTPS (produção)

```bash
# Edite Caddyfile: substitua sinalys.altanoroeste.com.br pelo seu domínio
docker compose --profile production up -d
```

O Caddy gerencia o certificado Let's Encrypt automaticamente.

---

## Variáveis de ambiente

| Variável        | Obrigatória em prod | Descrição                           |
|-----------------|---------------------|-------------------------------------|
| `JWT_SECRET`    | Sim                 | Secret HMAC-HS256 (mín. 32 chars)   |
| `DATABASE_URL`  | Sim                 | URL SQLAlchemy (postgres:// ou sqlite://) |
| `DB_PASSWORD`   | Sim                 | Senha do PostgreSQL                 |
| `DEBUG`         | Não                 | `false` em produção                 |
| `ADMIN_PASSWORD`| Não                 | Senha do admin inicial              |

Gere um `JWT_SECRET` seguro:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Testes

```bash
pytest tests/ -v --tb=short
# 135 testes · SQLite in-memory · ~7s
```

---

## Backup e restore

```bash
# Backup manual
./scripts/backup.sh

# Restore
gunzip -c backups/backup_2025-01-15_1430.sql.gz | \
  psql -h localhost -U sinalys sinalys
```

---

## Stack

| Camada       | Tecnologia                          |
|--------------|-------------------------------------|
| Backend      | Python 3.12, FastAPI 0.133, Uvicorn |
| ORM          | SQLAlchemy 2.0 (sync)               |
| Banco (dev)  | SQLite 3                            |
| Banco (prod) | PostgreSQL 16                       |
| Auth         | PyJWT (HS256) + bcrypt 5.x          |
| PDF          | WeasyPrint 69 (CSS inline, A4)      |
| Frontend     | Vanilla JS (ES Modules), CSS        |
| Proxy/HTTPS  | Caddy 2 (auto Let's Encrypt)        |
| CI/CD        | GitHub Actions                      |
| Container    | Docker + Docker Compose             |
