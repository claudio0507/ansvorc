# Schema do Banco de Dados — Sinalys

## Diagrama de Relacionamentos

```
bd_BDI ────────────────────────────────────────────────┐
bd_RH ──────┐                                          │
bd_EPI ─────┤                                          │
bd_DESPESAS─┤──► fichas_equipe ──┐                     │
            │                     │                     │
bd_FROTAS ──┤                     ├──► fichas_servico ──┼────► orcamento_itens
bd_FERRAMENTAL ───────────────────┤                     │      ▲
            │                     │                     │      │
bd_MATERIAIS ───► fichas_produto ─┴─────────────────────┘      │
            │                                                  │
            └──────────────────────────────────────────────────┘
            (produtos também são orçáveis diretamente)

bd_ESTRUTURA_OPERACIONAL ──────────────────────────────┼────► orcamento_itens

clientes ──────────────────────────────────────────► orcamentos┘
usuarios ──► (RBAC em todas as telas)
```

---

## BLOCO 1 — Bancos de Dados (Gestor de BD)

### 1.1 `bd_BDI` — Parâmetros Tributários

| # | Campo | Tipo | Descrição |
|---|-------|------|-----------|
| 1 | `id` | INTEGER PRIMARY KEY AUTOINCREMENT | |
| 2 | `modalidade` | VARCHAR(20) NOT NULL | BDI-MAT+MO, BDI-MO, BDI+ICMS, FAT DIR SIMP |
| 3 | `uf` | CHAR(2) NOT NULL | PR, SP, etc. |
| 4 | `icms` | DECIMAL(5,4) NOT NULL DEFAULT 0 | Ex: 0.12 |
| 5 | `cofins` | DECIMAL(5,4) NOT NULL DEFAULT 0 | Ex: 0.03 |
| 6 | `pis` | DECIMAL(5,4) NOT NULL DEFAULT 0 | Ex: 0.0065 |
| 7 | `issqn` | DECIMAL(5,4) NOT NULL DEFAULT 0 | Ex: 0.05 |
| 8 | `custo_financeiro` | DECIMAL(5,4) NOT NULL DEFAULT 0.015 | CST FINAN |
| 9 | `irpj` | DECIMAL(5,4) NOT NULL DEFAULT 0 | Ex: 0.02 |
| 10 | `csll` | DECIMAL(5,4) NOT NULL DEFAULT 0 | Ex: 0.0108 |
| 11 | `despesas_adm` | DECIMAL(5,4) NOT NULL DEFAULT 0.13 | |
| 12 | `ativo` | BOOLEAN NOT NULL DEFAULT 1 | |

**UNIQUE:** (`modalidade`, `uf`)

### 1.2 `bd_RH` — Recursos Humanos

| # | Campo | Tipo |
|---|---|---|
| 1 | `id` | INTEGER PK |
| 2 | `cargo` | VARCHAR(100) NOT NULL |
| 3 | `custo_diario` | DECIMAL(10,4) NOT NULL |
| 4 | `ativo` | BOOLEAN DEFAULT 1 |

### 1.3 `bd_EPI` — Equipamentos de Proteção Individual

| # | Campo | Tipo |
|---|---|---|
| 1 | `id` | INTEGER PK |
| 2 | `item` | VARCHAR(100) NOT NULL |
| 3 | `custo_diario` | DECIMAL(10,4) NOT NULL |
| 4 | `ativo` | BOOLEAN DEFAULT 1 |

### 1.4 `bd_FERRAMENTAL` — Ferramentas por Seguimento

| # | Campo | Tipo |
|---|---|---|
| 1 | `id` | INTEGER PK |
| 2 | `seguimento` | VARCHAR(50) NOT NULL — EPS, HORIZONTAL, OBRA CIVIL, VERTICAL |
| 3 | `custo_diario` | DECIMAL(10,4) NOT NULL |
| 4 | `ativo` | BOOLEAN DEFAULT 1 |

### 1.5 `bd_FROTAS` — Veículos e Equipamentos

| # | Campo | Tipo |
|---|---|---|
| 1 | `id` | INTEGER PK |
| 2 | `seguimento` | VARCHAR(50) NOT NULL — APOIO, EPS, HORIZONTAL, VERTICAL |
| 3 | `custo_diario` | DECIMAL(10,4) NOT NULL |
| 4 | `ativo` | BOOLEAN DEFAULT 1 |

### 1.6 `bd_MATERIAIS` — Materiais

| # | Campo | Tipo |
|---|---|---|
| 1 | `id` | INTEGER PK |
| 2 | `material` | VARCHAR(200) NOT NULL |
| 3 | `unidade` | VARCHAR(10) NOT NULL — m², m, und, L, kg |
| 4 | `destinacao` | VARCHAR(50) — FABRICA, HORIZONTAL |
| 5 | `valor_unitario` | DECIMAL(12,4) NOT NULL |
| 6 | `ativo` | BOOLEAN DEFAULT 1 |

### 1.7 `bd_ESTRUTURA_OPERACIONAL` — Custos Operacionais

| # | Campo | Tipo |
|---|---|---|
| 1 | `id` | INTEGER PK |
| 2 | `item` | VARCHAR(150) NOT NULL |
| 3 | `unidade` | VARCHAR(10) NOT NULL |
| 4 | `tipo` | VARCHAR(50) NOT NULL — Base_de_Apoio, Moradia, Administrativo, Operacional, Logística |
| 5 | `valor_unitario` | DECIMAL(12,4) NOT NULL |
| 6 | `ativo` | BOOLEAN DEFAULT 1 |

### 1.8 `bd_DESPESAS` — Despesas por Seguimento

| # | Campo | Tipo |
|---|---|---|
| 1 | `id` | INTEGER PK |
| 2 | `seguimento` | VARCHAR(50) NOT NULL — EPS, HORIZONTAL, VERTICAL, APOIO |
| 3 | `epc` | DECIMAL(10,4) NOT NULL DEFAULT 0 |
| 4 | `refeicao` | DECIMAL(10,4) NOT NULL DEFAULT 0 |
| 5 | `hospedagem` | DECIMAL(10,4) NOT NULL DEFAULT 0 |
| 6 | `ativo` | BOOLEAN DEFAULT 1 |

---

## BLOCO 2 — Fichas Técnicas (Parametrizador)

### 2.1 `fichas_equipe`

| # | Campo | Tipo |
|---|---|---|
| 1 | `id` | INTEGER PK |
| 2 | `codigo` | VARCHAR(20) UNIQUE NOT NULL |
| 3 | `seguimento` | VARCHAR(50) NOT NULL — EPS, HORIZONTAL, VERTICAL, APOIO |
| 4 | `custo_dia_total` | DECIMAL(12,4) NOT NULL |
| 5 | `created_at` | TIMESTAMP |
| 6 | `ativo` | BOOLEAN DEFAULT 1 |

### 2.2 `fichas_equipe_itens`

| # | Campo | Tipo |
|---|---|---|
| 1 | `id` | INTEGER PK |
| 2 | `ficha_equipe_id` | FK → fichas_equipe.id |
| 3 | `rh_id` | FK → bd_RH.id |
| 4 | `quantidade` | INTEGER NOT NULL |
| 5 | `custo_mo` | DECIMAL(10,4) NOT NULL |
| 6 | `epi_id` | FK → bd_EPI.id |
| 7 | `custo_epi` | DECIMAL(10,4) NOT NULL |
| 8 | `refeicao` | DECIMAL(10,4) NOT NULL |
| 9 | `hospedagem` | DECIMAL(10,4) NOT NULL |
| 10 | `custo_dia_linha` | DECIMAL(10,4) NOT NULL |

### 2.3 `fichas_produto`

| # | Campo | Tipo |
|---|---|---|
| 1 | `id` | INTEGER PK |
| 2 | `codigo` | VARCHAR(20) UNIQUE NOT NULL |
| 3 | `nome` | VARCHAR(200) NOT NULL |
| 4 | `unidade` | VARCHAR(10) NOT NULL |
| 5 | `custo_total` | DECIMAL(12,4) NOT NULL |
| 6 | `possui_ficha` | BOOLEAN DEFAULT 1 |
| 7 | `created_at` | TIMESTAMP |
| 8 | `ativo` | BOOLEAN DEFAULT 1 |

### 2.4 `fichas_produto_itens`

| # | Campo | Tipo |
|---|---|---|
| 1 | `id` | INTEGER PK |
| 2 | `ficha_produto_id` | FK → fichas_produto.id |
| 3 | `material_id` | FK → bd_MATERIAIS.id (NULLABLE) |
| 4 | `componente_filho_id` | FK → fichas_produto.id (NULLABLE) |
| 5 | `quantidade` | DECIMAL(12,6) NOT NULL |
| 6 | `unidade` | VARCHAR(10) NOT NULL |
| 7 | `custo_unitario` | DECIMAL(12,4) NOT NULL |
| 8 | `custo_total_linha` | DECIMAL(12,4) NOT NULL |

**CHECK:** Exatamente um de material_id ou componente_filho_id preenchido.

### 2.5 `fichas_servico`

| # | Campo | Tipo |
|---|---|---|
| 1 | `id` | INTEGER PK |
| 2 | `codigo` | VARCHAR(20) UNIQUE NOT NULL |
| 3 | `nome` | VARCHAR(200) NOT NULL |
| 4 | `seguimento` | VARCHAR(50) NOT NULL |
| 5 | `produtividade_dia` | DECIMAL(10,2) NOT NULL CHECK(> 0) |
| 6 | `unidade` | VARCHAR(10) NOT NULL |
| 7 | `possui_ficha` | BOOLEAN DEFAULT 1 |
| 8 | `custo_unitario` | DECIMAL(12,4) NOT NULL |
| 9 | `created_at` | TIMESTAMP |
| 10 | `ativo` | BOOLEAN DEFAULT 1 |

### 2.6 `fichas_servico_recursos`

| # | Campo | Tipo |
|---|---|---|
| 1 | `id` | INTEGER PK |
| 2 | `ficha_servico_id` | FK → fichas_servico.id |
| 3 | `ficha_equipe_id` | FK → fichas_equipe.id |
| 4 | `frota_id` | FK → bd_FROTAS.id |
| 5 | `ferramental_id` | FK → bd_FERRAMENTAL.id |
| 6 | `ficha_produto_id` | FK → fichas_produto.id (NULLABLE) |

**Fórmula:** custo_unitario = (equipe.custo_dia_total + frota.custo_diario + ferr.custo_diario) / produtividade_dia + produto.custo_total

---

## BLOCO 3 — Orçamentos e CRM

### 3.1 `clientes`

| # | Campo | Tipo |
|---|---|---|
| 1 | `id` | INTEGER PK |
| 2 | `nome` | VARCHAR(200) NOT NULL |
| 3 | `tipo` | VARCHAR(20) |
| 4 | `cnpj_cpf` | VARCHAR(20) |
| 5 | `contato_nome` | VARCHAR(100) |
| 6 | `contato_email` | VARCHAR(150) |
| 7 | `contato_telefone` | VARCHAR(30) |
| 8 | `ativo` | BOOLEAN DEFAULT 1 |

### 3.2 `orcamentos`

| # | Campo | Tipo |
|---|---|---|
| 1 | `id` | INTEGER PK |
| 2 | `numero` | VARCHAR(20) UNIQUE NOT NULL |
| 3 | `cliente_id` | FK → clientes.id |
| 4 | `obra` | VARCHAR(300) |
| 5 | `uf_execucao` | CHAR(2) NOT NULL |
| 6 | `beneficio_reidi` | BOOLEAN NOT NULL DEFAULT 0 |
| 7 | `desconto_percentual` | DECIMAL(5,2) DEFAULT 0 |
| 8 | `status` | VARCHAR(20) DEFAULT 'rascunho' |
| 9 | `versao` | INTEGER DEFAULT 1 |
| 10 | `orcamento_origem_id` | FK → orcamentos.id (NULLABLE) |
| 11 | `created_by` | FK → usuarios.id |
| 12 | `created_at` | TIMESTAMP |
| 13 | `aprovado_em` | TIMESTAMP |

### 3.3 `orcamento_itens`

| # | Campo | Tipo |
|---|---|---|
| 1 | `id` | INTEGER PK |
| 2 | `orcamento_id` | FK → orcamentos.id |
| 3 | `bloco` | VARCHAR(30) NOT NULL |
| 4 | `ficha_servico_id` | FK → fichas_servico.id (NULLABLE) |
| 5 | `ficha_produto_id` | FK → fichas_produto.id (NULLABLE) |
| 6 | `tipo_origem` | VARCHAR(20) NOT NULL |
| 7 | `descricao` | VARCHAR(300) NOT NULL |
| 8 | `unidade` | VARCHAR(10) NOT NULL |
| 9 | `quantidade` | DECIMAL(12,4) NOT NULL |
| 10 | `mod_fat` | VARCHAR(20) NOT NULL |
| 11 | `margem_lucro` | DECIMAL(5,2) NOT NULL |
| 12 | `custo_direto_unitario` | DECIMAL(12,4) NOT NULL |
| 13 | `bdi_aplicado` | DECIMAL(10,6) NOT NULL |
| 14 | `preco_venda_unitario` | DECIMAL(12,4) NOT NULL |
| 15 | `preco_venda_total` | DECIMAL(14,4) NOT NULL |
| 16 | `lucro_absoluto` | DECIMAL(12,4) NOT NULL |
| 17 | `peso_rateio` | DECIMAL(8,6) NOT NULL |
| 18 | `desconto_rateado` | DECIMAL(12,4) DEFAULT 0 |
| 19 | `flag_aprovacao` | BOOLEAN DEFAULT 0 |

---

## Regras de Integridade

1. **Flag `possui_ficha`:** Serviço/produto com FALSE não pode ser usado em orçamento
2. **Snapshot imutável:** Após aprovado, orcamento_itens nunca sofre UPDATE
3. **REIDI em cascata:** Se TRUE, PIS e COFINS zerados em todas as linhas
4. **Produtos orçáveis diretamente:** ficha_produto_id pode ser usado sem ficha_servico_id
