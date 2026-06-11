CORRIJA e IMPLEMENTE as melhorias abaixo no repositório claudio0507/ansvorc.

Antes de qualquer alteração, leia obrigatoriamente:
- docs/01-visao-geral.md
- docs/02-schema-banco-dados.md
- docs/03-fichas-tecnicas.md
- docs/04-motor-calculo.md
- docs/05-ux-telas.md
- AGENTS.md
- design-system-preview.html (modelo visual de referência)

---

## BLOCO 1 — CÁLCULOS E REGRAS DE NEGÓCIO DE ORÇAMENTOS

### 1.1 Preço Unitário visível após cálculo + efeito do desconto

Atualmente o sistema mostra apenas o preço total da linha. Corrija para que:

- Após o cálculo (`/calcular`), cada linha em `orcamento_itens` exiba:
  - `preco_venda_unitario` — preço unitário ANTES do desconto
  - `preco_venda_unitario_final` — preço unitário APÓS o rateio do desconto
- O preço unitário final DEVE refletir o desconto rateado (item 1.2)
- Exibir ambos na tela de composição do orçamento
- Esta informação é essencial para o cliente comparar propostas

### 1.2 Desconto rateado apenas em Serviços e Produtos

**Atual:** O desconto está sendo rateado em TODOS os itens (incluindo Estrutura Operacional
e Custos Excepcionais).

**Correto:** O desconto NÃO deve ser aplicado em:
- Itens do bloco `operacional` (Estrutura Operacional)
- Itens do bloco `excepcionais` (Custos Excepcionais)

O desconto deve ser distribuído proporcionalmente APENAS entre:
- Itens do bloco `servicos`
- Itens do bloco `produtos`

Regra no motor:
```
subtotal_faturavel = soma(preco_venda_total dos blocos servicos + produtos)
desconto_total = subtotal_faturavel * (desconto_percentual / 100)
Para cada item nos blocos servicos/produtos:
  peso_item = preco_venda_total_item / subtotal_faturavel
  desconto_rateado_item = desconto_total * peso_item
  preco_venda_final_item = preco_venda_total_item - desconto_rateado_item
Itens operacional/excepcionais: desconto_rateado = 0
```

### 1.3 Histórico de descontos nas revisões

- Criar tabela `historico_descontos`:
```
id: INTEGER PK
orcamento_id: INTEGER FK → orcamentos.id
versao: INTEGER                  — versão do orçamento
desconto_percentual: DECIMAL(5,2)
subtotal_faturavel: DECIMAL(14,4)
desconto_total: DECIMAL(14,4)
criado_em: DateTime
```

- Ao aprovar um orçamento, salvar registro no histórico com o desconto concedido
- Ao reabrir (nova versão), manter rastreabilidade do desconto anterior
- Na tela de composição, mostrar "Histórico de Descontos" com as versões anteriores
- Isso permite análise crítica do andamento das propostas enviadas

### 1.4 Observações internas na aprovação

- Ao acionar o botão "Aprovar", ABRIR um modal/dialog com caixa de texto
- Campo: `observacoes_internas` (TEXT)
- O texto é obrigatório para concluir a aprovação
- Salvar no campo `observacoes_internas` da tabela `orcamentos`
- Este texto NÃO aparece na proposta enviada ao cliente
- Serve apenas para gerenciamento interno (rastreabilidade)
- Exibir na tela de composição como "Observações Internas" (ícone de nota)
- Manter no histórico quando o orçamento for reaberto

### 1.5 Seleção de Produtos no Orçamento — usar cadastro correto

**Erro atual:** Na tela de composição do orçamento, ao adicionar um produto, o sistema
está puxando da tabela `fichas_produto` (Produtos BOM / Ficha Técnica).

**Correto:**
- Produtos adicionados ao orçamento devem vir da tabela `produtos` (cadastro da tela
  "Produtos e Componentes")
- Apenas itens onde `produtos.id` existe podem ser adicionados como produto no orçamento
- Componentes (`componentes`) NÃO devem aparecer na seleção de itens do orçamento
- Componentes são usados EXCLUSIVAMENTE na composição de fichas técnicas
- Se um produto possui ficha técnica vinculada (`possui_ficha_tecnica = TRUE`),
  o sistema deve usar os dados da ficha para calcular o custo, mas o ITEM no orçamento
  referencia o `produto_id`, não o `ficha_produto_id`

---

## BLOCO 2 — TELA DE EMISSÃO E COMPOSIÇÃO DA PROPOSTA

### 2.1 Tela de composição da proposta comercial

Criar nova rota `frontend/app/routes/proposta.tsx` (ou `orcamentos.$id.proposta.tsx`).

Esta tela deve conter:

**Cabeçalho da proposta:**
- Logotipo (PNG parametrizável — ver item 2.2)
- Nome do sistema: "orcOS"
- Subtítulo: "[NOME DA EMPRESA]" (parametrizável — ver item 5.4)
- Dados do cliente: nome, CNPJ/CPF, contato (puxados da tabela `clientes`)
- Nome do orçamentista responsável (puxado da tabela `usuarios_orcamentistas` — ver item 2.4)
- Número da proposta, data de emissão, validade

**Corpo da proposta:**
- Tabela com os itens do orçamento agrupados em blocos (Serviços, Produtos)
- Colunas: Item, Descrição, QTD, Un, Preço Unit, Preço Total
- Itens de Estrutura Operacional e Excepcionais NÃO aparecem na proposta
  (são custos internos absorvidos)
- Rodapé: subtotal, desconto, total líquido

**Textos parametrizáveis:**
- Validade da proposta (ex: "30 dias")
- Condições de pagamento (texto livre)
- Texto livre adicional (observações para o cliente)
- Estes campos são salvos na tabela `orcamentos` ou em tabela `config_proposta`

**Formatação:**
- Seguir o tema Discord Dark do sistema
- Fonte DM Sans
- Preparado para exportação PDF (usando o serviço `export_pdf.py` existente)

### 2.2 Logotipo parametrizável (PNG)

- Na tela de Parâmetros (`parametros.tsx`), adicionar upload de imagem PNG
- Salvar em `backend/static/logo.png` ou em caminho configurável
- Limite: 500 KB, dimensão máxima 400×120 px
- Exibir na proposta e na tela de login
- Se não houver logo cadastrado, mostrar apenas o texto "orcOS"

### 2.3 Ferramenta de conciliação de descrições

Na tela de proposta, PARA CADA LINHA do orçamento:

- Campo opcional: "Descrição do Cliente" (`descricao_cliente` no `orcamento_itens`)
- Se preenchido, a proposta exibe a descrição do cliente em vez da descrição técnica
- Essa conciliação serve para casos em que o cliente exige nomenclatura própria
- Exemplo: "Sinalização Horizontal Tinta Acrílica" → cliente vê "Pintura de Faixa"

### 2.4 Cadastro de usuários orçamentistas

Criar tabela `usuarios_orcamentistas`:
```
id: INTEGER PK
nome_completo: VARCHAR(200) NOT NULL
funcao: VARCHAR(100)           — ex: "Orçamentista Sênior"
email: VARCHAR(150)
telefone: VARCHAR(30)
ativo: BOOLEAN DEFAULT TRUE
```

- Nova aba ou seção dentro de Parâmetros: "Orçamentistas"
- CRUD completo
- Ao criar um orçamento, selecionar qual orçamentista é responsável
- Os dados do orçamentista aparecem na proposta (nome, função, telefone, email)

---

## BLOCO 3 — CADASTROS GERAIS, EDIÇÃO E EXCLUSÃO (CRUD)

### 3.1 Edição universal de itens

**Problema atual:** Para alterar qualquer item cadastrado, é necessário excluir e recriar.
Isso não é viável operacionalmente.

**Corrigir em TODAS as telas de cadastro:**

| Tela | Campos editáveis |
|---|---|
| **BDs (RH, EPI, Ferramental, Frotas, Materiais, Estrutura, Despesas)** | Todos os campos, inclusive preço |
| **Produtos** | Nome, descrição, características, dimensões, peso, volume, depósito, setor, unidade |
| **Componentes** | Idem Produtos |
| **Serviços** (fichas_servico) | Nome, produtividade_dia, unidade |
| **Fichas de Equipe** | Código, seguimento, itens (cargos, quantidades) |
| **Fichas de Produto (BOM)** | Nome, unidade, itens (materiais, quantidades) |
| **Parâmetros** | Nome, ativo/inativo |
| **Unidades de Medida** | Sigla, nome |

- Implementar modal de edição com formulário preenchido com dados atuais
- Botão de lápis (ícone) em cada linha
- Salvar alterações via PUT/PATCH
- `updated_at` deve ser atualizado automaticamente

### 3.2 Critérios de exclusão seguros

**Problema:** Exclusão de itens pode quebrar integridade referencial — fichas que usam
aquele item, orçamentos já calculados, etc.

**Implementar soft delete + verificação de dependências:**

- NENHUM item é excluído fisicamente (DELETE) se possuir dependências
- Ao tentar excluir, verificar:
  - Se o item está em alguma ficha técnica → exibir mensagem: "Este item é usado em
    X ficha(s). Remova-o das fichas primeiro ou inative-o."
  - Se o item está em algum orçamento → bloquear exclusão: "Este item consta em
    X orçamento(s). Exclusão não permitida."
- Se não houver dependências, marcar `ativo = FALSE` (soft delete)
- Itens inativos não aparecem nos selects de cadastro mas mantêm integridade histórica
- Nos relatórios, itens inativos devem aparecer com flag "Inativo"

### 3.3 Integração de dados — unidades de medida

- TODOS os campos de unidade no sistema DEVEM usar a tabela `unidades_medida`
- Verificar e corrigir:
  - `bd_MATERIAIS.unidade` → FK para `unidades_medida.id`
  - `fichas_produto.unidade` → FK para `unidades_medida.id`
  - `fichas_servico.unidade` → FK para `unidades_medida.id`
  - `orcamento_itens.unidade` → FK para `unidades_medida.id`
  - `produtos.unidade_id` → FK para `unidades_medida.id` (já está)
  - `componentes.unidade_id` → FK para `unidades_medida.id` (já está)
- Onde houver campo de unidade, ABRIR select com a lista de unidades parametrizadas
- Produtos e Componentes devem expor todas as informações cadastradas nos endpoints
  da API para consumo dos relatórios

---

## BLOCO 4 — NOVO MÓDULO DE BUSINESS INTELLIGENCE (HISTÓRICO DE PREÇOS)

### 4.1 Monitoramento estatístico de preços

Criar nova tela `frontend/app/routes/bi-precos.tsx` com:

- **Seleção de escopo:**
  - Tipo: Produto, Serviço, Componente
  - Item específico (dropdown)
  - Período: último mês, 3 meses, 6 meses, 12 meses, todo período

- **Métricas exibidas:**
  - Preço médio praticado
  - Preço máximo
  - Preço mínimo
  - Preço atual (último orçamento)
  - Variação percentual no período
  - Número de orçamentos em que o item aparece

- **Origem dos dados:**
  - Consultar `orcamento_itens` filtrando por `ficha_servico_id`, `ficha_produto_id`,
    `produto_id` ou `componente_id`
  - Agrupar por mês/trimestre
  - Considerar apenas orçamentos com status `aprovado`

### 4.2 Gráficos e visualização

Usar a biblioteca de gráficos já disponível no projeto (`recharts` via `chart.tsx` shadcn):

- **Gráfico 1 — Linha do tempo:** Preço unitário ao longo do tempo (eixo X: mês/ano, eixo Y: R$)
  - Linha do preço médio
  - Área do intervalo (mín-máx)
- **Gráfico 2 — Barras:** Distribuição de preços por cliente/obra
- **Gráfico 3 — Tendência:** Linha de regressão/ tendência com média móvel

- Tabela abaixo dos gráficos com os dados detalhados (data, cliente, obra, preço unitário,
  quantidade, valor total)
- Exportar tabela para CSV

---

## BLOCO 5 — UI/UX E NOMENCLATURAS (WHITE LABEL)

### 5.1 Padronização visual dos campos QNT, Margem e MOD FAT

Na tela de composição do orçamento (`orcamentos.$id.tsx`):

- **QNT:** Aumentar a largura do input (de `w-20` para `w-24`) e exibir APENAS
  1 casa decimal após a vírgula (ex: "1.200,0" em vez de "1.200,0000")
- **Margem:** Diminuir a largura do input (de `w-20` para `w-14`), exibir em
  percentual com 1 casa decimal (ex: "15.0%")
- **MOD FAT:** Manter como select com as opções existentes
- Todos os 3 campos devem usar a MESMA fonte e tamanho que o restante da tabela
  (`text-[0.6875rem]`)

### 5.2 Renomear "Produtos (BOM)" para "Ficha Técnica"

Em TODAS as ocorrências no sistema:

| Onde | De | Para |
|---|---|---|
| Sidebar / Menu | Produtos (BOM) | Ficha Técnica |
| Título da página fichas.tsx | Fichas de Produto | Ficha Técnica |
| Tabs da tela de fichas | Produtos | Fichas Técnicas |
| seeds / comentários | BOM | Ficha Técnica |
| Schemas e models | manter `fichas_produto` internamente | (nomenclatura do BD não muda) |

### 5.3 White Label — Renomear "Sinalys" para "orcOS"

Em TODAS as ocorrências VISÍVEIS ao usuário:

| Onde | De | Para |
|---|---|---|
| Título da aplicação (app.css, config.py) | Sinalys | orcOS |
| Tela de login | Sinalys | orcOS |
| Sidebar (logo) | Sinalys | orcOS |
| Títulos de página | Sinalys | orcOS |
| Emails e notificações | Sinalys | orcOS |
| Rodapés de relatórios PDF | Sinalys | orcOS |
| `<title>` do HTML | Sinalys | orcOS |
| Seeds (nome de usuários, descrições) | Sinalys | orcOS |

**NÃO alterar:**
- Nomes de arquivos/pastas
- Nomes de classes/tabelas internas (`Sinalys` no código)
- Configs técnicas

### 5.4 Subtítulo da empresa (parametrizável)

- Adicionar campo `nome_empresa` na tabela de configurações ou em `parametros`
- Valor padrão: "ALTA NOROESTE"
- Exibir como subtítulo menor abaixo de "orcOS" em:
  - Tela de login
  - Sidebar
  - Proposta comercial (ver BLOCO 2)
- Editável na tela de Parâmetros

### 5.5 Créditos "Desenvolvido por Viaxis Tech HUB"

Incluir o texto em:

- Tela de login: abaixo do formulário, fonte pequena e discreta
- Rodapé dos relatórios PDF exportados: "Desenvolvido por Viaxis Tech HUB"
- Rodapé do sistema (se houver): mesma linha

---

## REGRAS DE EXECUÇÃO

1. Leia `docs/02-schema-banco-dados.md` antes de alterar QUALQUER model
2. Campos monetários: SEMPRE `DECIMAL`, NUNCA `float`
3. Commits em português, um por bloco lógico
4. NÃO delete os docs/ existentes
5. NÃO faça deploy
6. Mantenha o tema shadcn + Discord Dark — sem novas cores saturadas
7. Soft delete: NUNCA excluir fisicamente itens com dependências
8. Testes: adicionar testes para os novos serviços (motor, histórico, BI)
