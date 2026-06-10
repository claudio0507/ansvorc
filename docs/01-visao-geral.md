# Sinalys — Sistema de Orçamentação para Engenharia Viária

## Visão Geral

**Sinalys** é um ERP de orçamentação técnica focado em engenharia viária, desenvolvido para a **Alta Noroeste Sinalização Viária Ltda**. O sistema substitui planilhas Excel por uma plataforma web com banco de dados relacional, motor de cálculo tributário (BDI), fichas técnicas parametrizáveis e controle de orçamentos.

### Objetivo

Transformar requisitos de engenharia rodoviária em propostas comerciais precisas, aplicando automaticamente regras fiscais (REIDI, ISS por UF, MOD FAT) e distribuindo custos indiretos via Fator K.

### Filosofia

> "Este não é apenas um sistema de cálculo de materiais. É uma ferramenta de engenharia de custos tributários."

---

## Papéis de Usuário (RBAC)

| Papel | Responsabilidade | O que pode fazer |
|---|---|---|
| **Gestor de BD** | Alimentar custos brutos | CRUD em todos os bancos de dados (RH, Materiais, Frotas, EPI, Ferramental, Estrutura, Despesas, BDI) |
| **Parametrizador** | Criar fichas técnicas | Montar equipes, produtos (BOM) e serviços vinculando recursos |
| **Orçamentista** | Elaborar propostas | Criar orçamentos, aplicar MOD FAT e margens, gerenciar clientes |

---

## Arquitetura do Sistema

```
Frontend (HTML5 + CSS3 + JS vanilla → React com shadcn)
        │
Backend (Python 3.12 + FastAPI + SQLAlchemy)
        │
Banco de Dados (SQLite dev / PostgreSQL prod)
  7 BD tables + 3 Ficha tables + Orçamento + Clientes
```

## Estrutura do Projeto

```
ansvorc/
├── README.md
├── AGENTS.md                    # Instruções para agentes LLM
├── docs/
│   ├── 01-visao-geral.md        # Este documento
│   ├── 02-schema-banco-dados.md # Schema completo (14 tabelas)
│   ├── 03-fichas-tecnicas.md    # Estrutura e lógica das fichas
│   ├── 04-motor-calculo.md      # Motor BDI e Fator K
│   ├── 05-ux-telas.md           # Wireframes e fluxos de tela
│   └── 06-plano-fases.md        # Roadmap de implementação
├── backend/
├── frontend/
└── tests/
```

## Documentos Relacionados (Google Drive)

- `instruções de continuidade.txt` — Modelo de dados e regras de negócio
- `definições do modelo.txt` — Consolidação estratégica
- `DADOS-BD.xlsx` — Campos dos 7 bancos de dados
- `FICHAS/` — 5 tipos de ficha técnica em Excel

*Schema consolidado em 08/06/2026.*
