# Prompt: Implementar Template de Proposta Comercial (FOR 077)

## Contexto

O orcOS (repo `claudio0507/ansvorc`, branch `feat/melhorias-v2`) já possui o backend com 13 campos novos no model `Orcamento` e 12 campos novos no `ConfigSistema`, mais o doc `docs/08-template-proposta.md` com o mapeamento completo. O que falta é o **frontend**: a tela de proposta comercial onde o orçamentista edita as seções, visualiza o resultado e exporta.

## Referência Visual

Abrir `proposta-template-preview.html` na raiz do repo. Esse HTML mostra o layout exato com 19 seções, usando o tema Discord Dark (#111214 bg, #2b2d31 card, #c32a30 acento, gg sans). Replicar esse visual.

## Regras de Negócio

### 1. Descrições dos itens = EDITÁVEIS, Valores = READ-ONLY

Esta é a regra mais importante. Na seção de Preço (seção 7), a planilha mostra os itens do orçamento agrupados por seguimento. O orçamentista pode:
- **EDITAR** a coluna `descrição` de cada item (tanto de serviço quanto de produto)
- **NÃO pode editar** nenhum valor (quantidade, preço unitário, preço total, BDI, margem)

Valores são calculados pelo motor BDI (`POST /orcamentos/{id}/calcular`). A edição da descrição é um `PATCH /orcamentos/{id}/itens/{item_id}` com `{ "descricao": "novo texto" }` — apenas esse campo é alterável.

### 2. Campos da Proposta — Fallback ConfigSistema

Se um campo do orçamento estiver vazio (null), usa o valor padrão do `ConfigSistema`:

| Campo Orcamento (vazio) | Fallback ConfigSistema |
|---|---|
| `texto_topo_proposta` | `declaracoes_padrao` |
| `clausula_tributaria` | `clausula_tributaria_padrao` |
| `reajustamento` | `reajustamento_padrao` |
| `garantia_retencao_pct` | `garantia_retencao_padrao_pct` (5) |
| `garantia_devolucao_dias` | `garantia_devolucao_padrao_dias` (60) |
| `faturamento_direto` | "Não aplicável." |
| `entrega_as_built` | "Não aplicável." |
| `modalidade` | "Preço Unitário" |

### 3. Ordem das Seções na Proposta

1. Cabeçalho (número, versão, data, cidade) — sistema
2. À (Cliente) — do cadastro
3. Objeto (`obra`) — editável
4. Declarações (`texto_topo_proposta`) — editável, richtext/bullets
5. Escopo (`escopo`) — editável
6. Modalidade (`modalidade`) — dropdown: Preço Unitário, Preço Global, Empreitada
7. Preço (planilha com itens + total + REIDI + alíquotas) — **valores read-only, descrições editáveis**
8. Prazo (`prazo_entrega`) + Cláusula Tributária (`clausula_tributaria`) — editável
9. Faturamento Direto (`faturamento_direto`) — editável
10. Medição e Pagamento (`medicao_pagamento`) — editável
11. Dados Bancários — do ConfigSistema (`banco`, `agencia`, `conta_corrente`), editável em Parâmetros
12. Representante Legal — do ConfigSistema (`diretor_*` + `diretor_cpf` + `cnpj`)
13. Testemunha (`testemunha_nome`, `testemunha_email`, `testemunha_cpf`) — editável
14. Reajustamento (`reajustamento`) — editável
15. Garantia Contratual (`garantia_retencao_pct` + `garantia_devolucao_dias`) — editável, monta texto automático: "Retenção de X%, com devolução em Y dias após o termo de encerramento."
16. Entrega de As Built (`entrega_as_built`) — editável
17. Validade da Proposta (`validade_proposta`) — editável
18. Observação (`texto_livre_proposta`) — editável
19. Contato Comercial — do ConfigSistema (`contato_comercial_*`)

### 4. Campos Novos no Backend (JÁ IMPLEMENTADOS)

**Model Orcamento** — 13 campos novos:
- `escopo` (Text)
- `modalidade` (String 50)
- `faturamento_direto` (String 300)
- `medicao_pagamento` (Text)
- `clausula_tributaria` (Text)
- `reajustamento` (Text)
- `garantia_retencao_pct` (Decimal 5,2)
- `garantia_devolucao_dias` (Integer)
- `entrega_as_built` (String 300)
- `testemunha_nome` (String 200)
- `testemunha_email` (String 150)
- `testemunha_cpf` (String 20)

**Model ConfigSistema** — 12 campos novos:
- `cnpj` (String 20)
- `banco` (String 100), `agencia` (String 20), `conta_corrente` (String 30)
- `diretor_cpf` (String 20)
- `contato_comercial_nome` (String 200), `contato_comercial_funcao` (String 100), `contato_comercial_fone` (String 30), `contato_comercial_email` (String 150)
- `clausula_tributaria_padrao` (Text), `reajustamento_padrao` (Text)
- `garantia_retencao_padrao_pct` (Decimal 5,2), `garantia_devolucao_padrao_dias` (Integer)
- `declaracoes_padrao` (Text)

**Schemas** OrcamentoCreate, OrcamentoUpdate, OrcamentoRead e ConfigSistemaRead/Update já estão sincronizados.

## Tarefas

### Tarefa 1: Endpoint PATCH para editar descrição de item

Criar `PATCH /api/v1/orcamentos/{id}/itens/{item_id}` que aceita apenas `{ "descricao": "novo texto" }`. Retornar 403 se o orçamento não estiver em status `rascunho`. Qualquer outro campo no payload → 422.

### Tarefa 2: Expandir o endpoint de ConfigSistema

O `PUT /api/v1/config` já existe mas só aceita os 5 campos antigos. Atualizar para aceitar todos os 17 campos novos (12 dados + 5 diretor). Atualizar também o seed para popular os campos novos com os valores do FOR 077:

```
cnpj: "20.945.724/0001-15"
banco: "Bradesco"
agencia: "0110"
conta_corrente: "0287852-6"
diretor_cpf: "277.540.838-92"
contato_comercial_nome: "Milaini Carvalho Miranda"
contato_comercial_funcao: "Comercial"
contato_comercial_fone: "(18) 99683-6472"
contato_comercial_email: "comercial@altanoroeste.com.br"
clausula_tributaria_padrao: "Os preços apresentados nesta proposta contemplam a carga tributária atual exigida pela legislação pertinente. Eventuais contratos com execuções ou vigência posterior a 31/12/2026 estarão sujeitos a revisão e renegociação obrigatória, visando o repasse dos impactos tributários causados pela transição da Reforma Tributária (IBS/CBS)."
reajustamento_padrao: "Os preços poderão ser atualizados anualmente, mediante aplicação do índice de menor variação acumulada no período entre o Índice Nacional de Preços ao Consumidor Amplo – IPCA ou o Índice Geral de Preços do Mercado – IGPM. A data-base para fins de reajuste será a data de assinatura do contrato."
garantia_retencao_padrao_pct: 5
garantia_devolucao_padrao_dias: 60
declaracoes_padrao: "Que respeita integralmente as condições estabelecidas na TR.ENG.{numero}.\nQue possui conhecimento das Políticas de Meio Ambiente, corporativa sobre Mudanças Climáticas e de Responsabilidade Social.\nQue possui conhecimento e que cumpre a legislação anticorrupção e, em especial a Lei 12.846/13;\nQue executará os serviços de acordo com o projeto e suas modificações, ordem de serviço, e de acordo com as normas e especificações técnicas;\nQue se obriga a dispor, para emprego imediato, de todos os recursos necessários para a execução dos serviços contratados, no prazo estipulado, sem custos adicionais;\nQue tem pleno conhecimento das condições locais necessárias para a formação dos preços;\nQue não possui em seu quadro de empregados, menor de 18 anos em trabalho noturno, insalubre ou perigoso, e, ainda, não possuir empregado menor de 16 anos;\nQue a proponente não mantém qualquer relação ou vínculo de qualquer natureza com a Contratante ou empresas do mesmo Conglomerado econômico a qual pertence;\nQue conhece o Código de Ética e Integridade, constantes nos documentos recebidos.\nSe comprometer a estar instalado e pronto para o início dos serviços no prazo imposto no termo de referência;\nQue em seu preço estão inclusas todas as despesas com a prestação dos serviços, equipamentos, mão-de-obra, tributos, encargos, impostos, lucro, e as demais despesas diretas e indiretas que possam recair sobre a presente prestação de serviços;\nQue executará todos os serviços de acordo com o preço e o prazo, estipulados nesta carta;\nQue tem pleno conhecimento sobre a retenção de X% das medições sobre o valor bruto da medição a título de caução."
```

### Tarefa 3: Tela de Parâmetros — Aba "Empresa"

Na tela existente de Parâmetros (`/parametros`), adicionar uma aba "Empresa" com os 17 campos do ConfigSistema organizados em cards:

- Card "Dados da Empresa": `nome_empresa`, `cnpj`, `logo_path`
- Card "Representante Legal": `diretor_nome`, `diretor_funcao`, `diretor_cpf`, `diretor_telefone`, `diretor_email`
- Card "Contato Comercial": `contato_comercial_nome`, `contato_comercial_funcao`, `contato_comercial_fone`, `contato_comercial_email`
- Card "Dados Bancários": `banco`, `agencia`, `conta_corrente`
- Card "Textos Padrão da Proposta": `declaracoes_padrao` (textarea), `clausula_tributaria_padrao` (textarea), `reajustamento_padrao` (textarea), `garantia_retencao_padrao_pct` (number), `garantia_devolucao_padrao_dias` (number)

Usar o estilo shadcn existente (Input, Textarea, Label, Card, Button). Salvar via `PUT /api/v1/config`.

### Tarefa 4: Tela de Proposta — Editor por Seções

Criar `app/routes/proposta.$id.tsx` com layout de 2 colunas (como o preview HTML):

**Sidebar esquerda (280px)**: navegação com 19 seções, badge NOVO/EXISTENTE/SISTEMA, scroll para a seção clicada.

**Área principal**: uma rota que carrega `GET /api/v1/orcamentos/{id}` e `GET /api/v1/config`. Renderiza as 19 seções em cards. Cada seção tem:

- Campos editáveis (Input/Textarea shadcn) para campos do Orcamento
- Campos read-only (com visual cinza/dimmed) para campos calculados/sistema
- Badge de fallback quando o campo está vazio e usando padrão do ConfigSistema: mostrar texto do padrão com badge "PADRÃO" e botão "Usar este texto" que copia o padrão pro campo
- Seção 7 (Preço): tabela de itens read-only, exceto coluna `descrição` que é editável inline (click → input → blur salva via PATCH)

**Quando o orçamento NÃO está em `rascunho`**: todos os campos são read-only, com badge "PROPOSTA ENVIADA".

Salvamento: `PATCH /api/v1/orcamentos/{id}` com apenas os campos alterados. Auto-save on blur com debounce (500ms). Toast de confirmação.

### Tarefa 5: Seção de Preço — Descrições Editáveis

Na seção 7 (Preço), a tabela de itens mostra:

| Item | Descrição ✏️ | Un | Qtd | Preço Unit. | Preço Total |
|---|---|---|---|---|---|
| 1 | Pintura faixa central | m | 5.000 | R$ 12,50 | R$ 62.500,00 |

- Coluna **Descrição**: click → vira Input editável → blur → `PATCH /api/v1/orcamentos/{id}/itens/{item_id}` com `{ "descricao": "novo texto" }`
- Demais colunas: **read-only**, valor cinza
- Agrupamento por seguimento (EPS, HORIZONTAL, VERTICAL, APOIO) com header colorido
- Ao final: Total Geral, Margem Líquida Real, Total da Proposta
- Toggle REIDI: checkbox que chama `POST /api/v1/orcamentos/{id}/calcular` com `beneficio_reidi` toggle
- Se REIDI ativo: mostrar PIS/COFINS zerados e valor com isenção

### Tarefa 6: Testes

- Teste do endpoint `PATCH /orcamentos/{id}/itens/{item_id}` — edita descrição, rejeita outros campos, rejeita se não-rascunho
- Teste do `PUT /api/v1/config` com todos os 17 campos novos
- Teste de fallback: orçamento com campos vazios retorna valores do ConfigSistema

## Design System

Usar EXATAMENTE o tema existente do projeto (Discord Dark):
- BG: `#111214`, Surface: `#1e1f22`, Card: `#2b2d31`, Elevated: `#313338`
- Acento: `#c32a30`, Font: `gg sans`
- Componentes shadcn existentes (Card, Input, Textarea, Label, Button, Badge, Table, Select)
- Labels: `uppercase, 11px, font-weight 600, color var(--dimmed)`
- Cards: `background var(--card), border 1px solid var(--border), border-radius 8px`
- Inputs editáveis: `background var(--elevated), border var(--border)`
- Inputs read-only: `background var(--input), opacity 0.6, cursor default`

## Não fazer

- NÃO mexer no motor BDI ou nos cálculos
- NÃO criar endpoint de export PDF agora (fica como D2)
- NÃO alterar as telas de BDI, fichas ou orçamento existentes
- NÃO adicionar Alembic/migrations — o sistema usa `Base.metadata.create_all()` com SQLite vazio a cada seed

## Arquivos relevantes

- `backend/models/orcamento_models.py` — model Orcamento com 13 campos novos
- `backend/models/extra_models.py` — model ConfigSistema com 12 campos novos
- `backend/schemas/orcamento_schemas.py` — schemas atualizados
- `backend/schemas/extra_schemas.py` — schemas atualizados
- `backend/routers/orcamento_routers.py` — router de orçamentos
- `backend/routers/extra_routers.py` — router de config (PUT /config)
- `backend/routers/param_routers.py` — router de parâmetros
- `backend/services/motor_bdi.py` — motor BDI (não mexer)
- `frontend/app/routes/orcamentos.$id.tsx` — tela atual de orçamento
- `frontend/app/routes/bds.tsx` — referência visual de cards/editores
- `frontend/app/app.css` — tokens do tema
- `proposta-template-preview.html` — layout de referência
- `docs/08-template-proposta.md` — mapeamento completo dos campos