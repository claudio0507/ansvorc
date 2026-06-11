CORRIJA o repositório claudio0507/ansvorc conforme as especificações abaixo.

Antes de qualquer alteração, leia obrigatoriamente:
- docs/01-visao-geral.md
- docs/02-schema-banco-dados.md
- docs/03-fichas-tecnicas.md
- docs/04-motor-calculo.md
- docs/05-ux-telas.md
- AGENTS.md
- design-system-preview.html (modelo visual de referência)

---

## BLOCO 1 — CORREÇÕES DE BUGS

### 1.1 Dashboard — Erro 500

O endpoint `GET /api/v1/dashboard` está quebrando. Causa: o código referencia
`Orcamento.criado_em` mas o campo se chama `created_at`. Corrija o nome do campo
e também o tipo de data usado no filtro para ser compatível com DateTime.

### 1.2 Quantidade exigindo decimais incorretos

Todo campo de "Quantidade" está exigindo formato com seis zeros e um numeral "1"
após a vírgula (ex: "1,000001"). Corrija o input para aceitar números decimais
normais (ponto ou vírgula, sem padding forçado). Use step="any" nos inputs HTML
ou remova validações excessivas nos schemas Pydantic.

### 1.3 Orçamento aprovado não mostra valores firmados

Quando um orçamento aprovado é revisitado, ele não exibe todos os valores que
foram firmados no momento da aprovação. Corrija para que:
- Ao aprovar, todos os campos de `orcamento_itens` sejam congelados (snapshot)
- Ao revisitar um orçamento aprovado, a tela mostre exatamente os valores do snapshot
- Campos bloqueados para edição (readonly) quando status != rascunho
- Mostrar: preco_unitario, custo_total_linha, preco_venda_linha, bdi_aplicado,
  desconto_rateado para cada linha

---

## BLOCO 2 — REGRAS DE NEGÓCIO E CÁLCULOS

### 2.1 Desconto com rateio proporcional

**Atual:** O desconto (`desconto_percentual`) é aplicado apenas sobre o total
da proposta, sem distribuir nas linhas.

**Correto:** O desconto deve ser rateado proporcionalmente em TODOS os itens:
- Cada linha em `orcamento_itens` recebe o campo `desconto_rateado`
- `desconto_rateado = preco_venda_linha * (desconto_percentual / 100)`
- `preco_venda_final = preco_venda_linha - desconto_rateado`
- O `total_proposta` reflete a soma dos preços finais com desconto
- Atualize o serviço `motor_bdi.py` e o endpoint `POST /api/v1/orcamentos/{id}/calcular`
- Exiba o valor diluído por linha na tela de composição

---

## BLOCO 3 — CADASTROS GERAIS E PARAMETRIZAÇÃO

### 3.1 Código automático para todos os itens

Para TODOS os itens cadastráveis, gere código automático no formato:
- 3 primeiras letras do tipo + hífen + número sequencial com 4 dígitos

| Tipo | Prefixo | Exemplo |
|---|---|---|
| Materiais | MAT | MAT-0001 |
| RH / Cargos | RH | RH-0001 |
| EPI | EPI | EPI-0001 |
| Ferramental | FER | FER-0001 |
| Frotas | FRO | FRO-0001 |
| Estrutura Operacional | EST | EST-0001 |
| Despesas | DES | DES-0001 |
| BDI | BDI | BDI-0001 |
| Componentes | CMP | CMP-0001 |
| Produtos | PRD | PRD-0001 |
| Ficha Equipe | FEQ | FEQ-0001 |
| Ficha Produto | FPR | FPR-0001 |
| Ficha Serviço | FSV | FSV-0001 |
| Orçamento | ORC | ORC-2026-0001 |

O sequencial deve ser por tipo (ex: MAT-0001, MAT-0002...), autoincremental,
calculado no backend no momento da criação. O campo `codigo` pode ser gerado
automaticamente se o frontend não enviar.

### 3.2 Botão de edição + data da última atualização

Para bd_RH, bd_EPI, bd_FERRAMENTAL, bd_FROTAS, bd_MATERIAIS,
bd_ESTRUTURA_OPERACIONAL, bd_DESPESAS e bd_BDI:

- Adicionar coluna `atualizado_em` (DateTime) em cada tabela
- Atualizar automaticamente no PUT/PATCH (trigger ou lógica no router)
- Frontend: ao lado de cada preço, mostrar "Atualizado em DD/MM/AAAA"
- Frontend: botão de edição (ícone de lápis) em cada linha da tabela
- A data de atualização deve aparecer nos relatórios de controle pós-aprovação

### 3.3 Unidades de medida padronizadas

Criar tabela `unidades_medida`:
```
id: INTEGER PK
sigla: VARCHAR(10) UNIQUE NOT NULL   — "m", "mm", "m²", "und", "L", "mL", "kg", "dia", "mês", "h", "R$"
nome: VARCHAR(50) NOT NULL           — "Metro", "Milímetro", "Metro Quadrado", "Unidade"...
ativo: BOOLEAN DEFAULT TRUE
```

- Pré-cadastrar as 12 unidades listadas via seed
- Todo campo de unidade nos cadastros deve ser um select (dropdown) dessa tabela
- NÃO permitir digitação livre de unidade — sempre selecionar da lista
- Parametrizador pode inserir novas unidades (botão "+ Nova Unidade" no select)

### 3.4 Aba para parametrizar Segmentos e Tipos

Criar tabelas de parâmetros:

**Tabela `parametros_seguimentos`:**
```
id: INTEGER PK
nome: VARCHAR(50) UNIQUE NOT NULL   — EPS, HORIZONTAL, VERTICAL, APOIO...
ativo: BOOLEAN DEFAULT TRUE
```

**Tabela `parametros_tipos_estrutura`:**
```
id: INTEGER PK
nome: VARCHAR(50) UNIQUE NOT NULL   — Base_de_Apoio, Moradia, Administrativo...
ativo: BOOLEAN DEFAULT TRUE
```

- Nova aba "Parâmetros" no menu, visível para Parametrizador e Sponsor
- Sub-abas: "Segmentos" e "Tipos de Estrutura Operacional"
- CRUD completo (adicionar, editar, inativar)
- Os selects de seguimento e tipo de estrutura passam a consultar essas tabelas
- Atualizar seeds com os valores padrão (EPS, HORIZONTAL, VERTICAL, APOIO...)
- Frontend: rota nova `frontend/app/routes/parametros.tsx`

---

## BLOCO 4 — PRODUTOS, COMPONENTES E FICHAS TÉCNICAS

### 4.1 Tela de cadastro de Componentes e Produtos

Criar tabela `componentes` (além da `fichas_produto` já existente):

```
id: INTEGER PK
codigo: VARCHAR(20) UNIQUE       — auto: CMP-0001
nome: VARCHAR(200) NOT NULL
descricao: TEXT
caracteristicas: TEXT            — descrição técnica
dimensoes: VARCHAR(100)          — ex: "100x50x30 cm"
volume_m3: DECIMAL(10,4)
peso_kg: DECIMAL(10,4)
deposito_produtivo: VARCHAR(100) — depósito ou centro produtivo
setor: VARCHAR(100)              — setor de produção
industrializado_terceiros: BOOLEAN DEFAULT FALSE
unidade_id: INTEGER FK → unidades_medida.id
possui_ficha_tecnica: BOOLEAN DEFAULT FALSE
ativo: BOOLEAN DEFAULT TRUE
created_at: DateTime
updated_at: DateTime
```

Criar tabela `produtos`:
```
id: INTEGER PK
codigo: VARCHAR(20) UNIQUE       — auto: PRD-0001
nome: VARCHAR(200) NOT NULL
descricao: TEXT
caracteristicas: TEXT
dimensoes: VARCHAR(100)
volume_m3: DECIMAL(10,4)
peso_kg: DECIMAL(10,4)
deposito_produtivo: VARCHAR(100)
setor: VARCHAR(100)
industrializado_terceiros: BOOLEAN DEFAULT FALSE
unidade_id: INTEGER FK → unidades_medida.id
possui_ficha_tecnica: BOOLEAN DEFAULT FALSE
ativo: BOOLEAN DEFAULT TRUE
created_at: DateTime
updated_at: DateTime
```

- Nova rota `frontend/app/routes/produtos-componentes.tsx`
- Tabs: "Produtos" e "Componentes"
- Grid com todas as colunas + flag "Ficha Técnica" (badge: SIM/NÃO)
- Botão de ação "Atribuir Ficha Técnica" em cada linha
- Modal: selecionar ficha(s) técnica(s) do catálogo para vincular ao item

### 4.2 Flag de ficha técnica + botão de atribuição

- Na tela de Produtos e Componentes, cada linha mostra:
  - Badge verde "SIM" se possui_ficha_tecnica = TRUE
  - Badge cinza "NÃO" se FALSE
- Botão "Atribuir Ficha Técnica" abre modal com:
  - Lista de fichas técnicas cadastradas (fichas_produto, fichas_servico, fichas_equipe)
  - Checkbox para selecionar múltiplas fichas
  - Tabela associativa `item_fichas`:
    ```
    id: INTEGER PK
    componente_id: INTEGER FK → componentes.id (nullable)
    produto_id: INTEGER FK → produtos.id (nullable)
    ficha_servico_id: INTEGER FK → fichas_servico.id (nullable)
    ficha_produto_id: INTEGER FK → fichas_produto.id (nullable)
    ficha_equipe_id: INTEGER FK → fichas_equipe.id (nullable)
    ```
  - CHECK: pelo menos um item_id e pelo menos uma ficha_id

### 4.3 Tela separada para construção de fichas técnicas

Refatorar a tela de fichas (`fichas.tsx`) para incluir:

- **Passo 1 — Tipo e Segmento:**
  - Select: Tipo de ficha (Produto, Componente, Serviço)
  - Select: Segmento (EPS, HORIZONTAL, VERTICAL, APOIO...)
  - Estes campos são obrigatórios e definem o escopo da ficha

- **Passo 2 — Composição (editor de itens existente):**
  - Ficha Produto: grid de materiais + componentes com quantidade e custo
  - Ficha Serviço: grid de equipes + frotas + ferramentais com produtividade
  - Cálculo automático de custo total

- **Ações:**
  - Salvar rascunho / Publicar ficha
  - Clonar ficha existente (para variações)
  - Exportar composição (PDF/impressão)

---

## BLOCO 5 — TELAS DE COMPOSIÇÃO E ORÇAMENTO

### 5.1 Composição do Orçamento — ajustes de layout

No arquivo `orcamentos.$id.tsx`:

- **Altura das linhas:** Reduzir padding das células da tabela (de `p-2` para `p-1`
  ou `py-0.5 px-2`)
- **Tamanho da fonte:** Reduzir proporcionalmente em toda a tela:
  - Títulos de bloco: `text-[0.625rem]` (10px)
  - Células de tabela: `text-[0.6875rem]` (11px)
  - Labels: `text-[0.625rem]`
- **Valor diluído:** Exibir coluna "Desc. Rateado" em cada linha com o valor
  do desconto proporcional (`desconto_rateado`)
- **Margem e MOD FAT editáveis:** Adicionar inputs inline nas colunas:
  - `margem_lucro` — editável por linha (número percentual)
  - `mod_fat` — editável por linha
  - Ao alterar, recalcular automaticamente via endpoint `/calcular`

### 5.2 Cores uniformes nos blocos

Todos os 4 blocos (Serviços, Produtos, Estrutura, Excepcionais) devem usar a
**mesma cor de fundo** na barra de título: `bg-secondary text-secondary-foreground`
(neutro conforme Discord Dark). Apenas o texto do título diferencia o bloco.
Remover cores distintas (vermelho, verde, amarelo) das barras de título.

### 5.3 Gerenciamento de Orçamentos — ocultar versões

Na tela de listagem (`orcamentos._index.tsx`):
- NÃO exibir coluna de versão/revisão
- Mostrar apenas o orçamento mais recente de cada grupo de versões
- O controle de versões (histórico, reabrir, nova versão) deve ficar DENTRO
  da tela de composição (`orcamentos.$id.tsx`), como já está parcialmente implementado

---

## BLOCO 6 — UI/UX (Interface do Usuário)

### 6.1 Contraste no tema dark

O modelo de referência é o `design-system-preview.html` (Discord Dark).

**Problema atual:** O `--background` está muito escuro, quase preto puro,
dificultando a distinção entre as camadas de superfície.

**Corrigir no `app.css`:**
```
Escada de superfícies (dark):
  --background:        #1a1b1e  (clarear um pouco — atualmente está #111214)
  --card (--surface):  #2b2d31  (manter)
  --surface-elevated:  #313338  (manter)

Texto:
  --foreground:        #e3e5e8  (manter)
  --text-secondary:    #b5bac1  (manter)
  --text-muted:        #80848e  (manter)
```

- Cards devem ter `ring-1 ring-foreground/6` para borda sutil visível
- Inputs devem usar `bg-surface-elevated` (mais claro que o fundo)
- Hover states: `hover:bg-foreground/5`
- Separadores visíveis entre seções

### 6.2 Ajustes gerais de UI

- **Sidebar:** ícones mais visíveis, avatar do usuário logado no rodapé
- **Header das páginas:** breadcrumb ou título + subtítulo descritivo
- **Tooltips:** em botões de ação (ícones sem label)
- **Loading states:** skeleton nos cards enquanto carrega dados
- **Empty states:** mensagem amigável quando não há registros ("Nenhum orçamento
  encontrado. Clique em '+ Novo Orçamento' para começar.")

---

## REGRAS DE EXECUÇÃO

1. Leia `docs/02-schema-banco-dados.md` antes de alterar QUALQUER model
2. Campos monetários: SEMPRE `DECIMAL`, NUNCA `float`
3. Commits em português, um por bloco lógico
4. NÃO delete os docs/ existentes
5. NÃO faça deploy
6. Mantenha o tema shadcn + Discord Dark — não introduza novas cores saturadas
   (sem verde, sem amarelo, sem azul além do acento #c32a30)
7. Extraia os tokens do `design-system-preview.html` como referência visual
