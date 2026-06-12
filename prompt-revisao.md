Faça uma REVISÃO COMPLETA do repositório claudio0507/ansvorc (branch main).

Antes de qualquer alteração, leia obrigatoriamente TODOS os arquivos em:
- docs/ (01 a 07)
- backend/ (models, routers, schemas, services, config, database, auth, middleware, seeds)
- frontend/ (app.css, routes/, components/, lib/api.ts, routes.ts)

## OBJETIVO

Garantir que o sistema funcione sem quebras, removendo código morto/obsoleto,
revisando segurança e implementando melhorias práticas de forma conservadora.

---

## BLOCO 1 — LIMPEZA DE CÓDIGO OBSOLETO

### 1.1 Remover imports não utilizados
- Em todos os arquivos .py e .tsx, remover imports que não são referenciados no corpo do arquivo
- Ex: componentes UI importados mas não usados, funções não chamadas

### 1.2 Remover variáveis e funções mortas
- Funções definidas mas nunca chamadas
- Variáveis de estado declaradas mas nunca lidas
- Props de componentes não utilizadas
- Código comentado com `//` ou `/* */` que seja obsoleto

### 1.3 Consolidar duplicação
- Se um padrão se repete em 3+ lugares, extrair para função/componente reutilizável
- Ex: formatação de datas, padrões de fetch com try/catch, modais CRUD repetidos

### 1.4 Verificar arquivos não referenciados
- Arquivos na raiz ou em subpastas que não são importados por nenhum outro arquivo
- Remover ou documentar o propósito

---

## BLOCO 2 — REVISÃO DE SEGURANÇA

### 2.1 Autenticação e JWT
- Verificar se o JWT_SECRET é forte e NÃO está hardcoded com valor padrão em produção
- Token deve expirar (verificar `ACCESS_TOKEN_EXPIRE_MINUTES`)
- Refresh token deve ser rotacionado a cada uso
- Logout deve invalidar refresh token

### 2.2 RBAC (Controle de Acesso)
- Verificar se TODAS as rotas /api/v1/* têm proteção RBAC adequada
- Confirmar que o middleware cobre TODOS os routers (auth, bd, ficha, orcamento, param, produto, bi, relatorio, extra)
- Rotas que retornam 403 devem ter mensagem clara

### 2.3 Validação de Input
- Todos os endpoints POST/PUT/PATCH devem ter schema Pydantic com validação
- Campos monetários: garantir que aceitam Decimal e rejeitam valores negativos onde não faz sentido
- Campos de texto: sanitizar contra XSS (remover tags HTML)
- Limitar tamanho de strings (nomes 200 char, descrições 500 char, etc.)
- Validar formato de email, telefone, CNPJ onde aplicável

### 2.4 SQL Injection e ORM
- Confirmar que NÃO há queries raw com interpolação de strings
- Todas as queries devem usar SQLAlchemy ORM ou bind parameters
- Verificar ordenação dinâmica (order_by com input do usuário)

### 2.5 Rate Limiting
- Endpoint de login deve ter rate limit (ex: 5 tentativas por minuto por IP)
- SlowAPI já está importado — verificar se está configurado corretamente

### 2.6 CORS
- Verificar `CORS_ORIGINS` no config — em produção deve ser domínio específico, não wildcard

---

## BLOCO 3 — MELHORIAS PRÁTICAS

### 3.1 Tratamento de Erros
- Todo fetch no frontend deve ter try/catch com toast de erro amigável
- Erros 401 devem redirecionar para login automaticamente
- Erros 403 devem mostrar mensagem "Acesso negado: seu perfil não tem permissão"
- Erros 500 devem mostrar "Erro interno. Tente novamente."
- Backend: retornar mensagens em português, não exceções técnicas

### 3.2 Loading States
- Toda tela deve mostrar skeleton ou "Carregando..." enquanto os dados não chegam
- Botões de submit devem desabilitar durante o envio e mostrar "Salvando..."
- Tabelas devem mostrar estado de carregamento vs estado vazio

### 3.3 Empty States
- Quando não há registros, mostrar mensagem amigável com ação sugerida
  - Ex: "Nenhum orçamento encontrado. Clique em '+ Novo Orçamento' para começar."
  - Ex: "Nenhuma ficha técnica cadastrada. Crie sua primeira ficha."

### 3.4 Confirmações de Ações Destrutivas
- Exclusão: confirm() antes de deletar (já existe em alguns lugares, unificar)
- Aprovação: já tem modal com observações, ok
- Rejeição: confirm() antes de rejeitar
- Nova versão: confirmar que é isso mesmo

### 3.5 Feedback Visual
- Toast de sucesso após criar/editar/excluir (já existe em vários lugares)
- Toast de erro com mensagem clara
- Badges de status consistentes (cores, texto, posição)

### 3.6 Responsividade
- Testar em viewport 768px, 1024px, 1440px
- Tabelas com overflow-x: auto (já existe, verificar)
- Sidebar colapsável em mobile
- Forms em grid que colapsam para 1 coluna em telas menores

---

## BLOCO 4 — CONSISTÊNCIA E PADRONIZAÇÃO

### 4.1 Nomenclatura
- Models: PascalCase, singular (Cliente, Orcamento, Produto)
- Tabelas: snake_case, plural (clientes, orcamentos, produtos)
- Rotas API: kebab-case, plural (/api/v1/bd-rh, /api/v1/fichas-equipe)
- Funções Python: snake_case (listar_rh, criar_orcamento)
- Funções TypeScript: camelCase (listRH, createOrcamento)
- Componentes React: PascalCase (NovoModal, StatusBadge)

### 4.2 Formatação
- Python: Black + isort (verificar se todos os arquivos estão formatados)
- TypeScript: Prettier (verificar se config existe)
- Remover console.log e prints de debug

### 4.3 Tipagem
- TypeScript: evitar `any` — usar tipos explícitos onde possível
- Python: usar type hints em todas as funções públicas
- Pydantic: todos os schemas devem ter tipos explícitos

### 4.4 Comentários
- Remover comentários TODO obsoletos (mais de 30 dias)
- Manter docstrings descritivas nas funções públicas
- Comentários em português

---

## BLOCO 5 — FUNCIONAMENTO END-TO-END

### 5.1 Fluxo Completo
Testar mentalmente (ou via código) o fluxo completo sem quebras:

1. **Login** → redireciona para dashboard
2. **Dashboard** → mostra métricas, gráfico radar, orçamentos recentes
3. **BDs** → CRUD completo (criar, editar, excluir) em todos os 8 bancos
4. **Parâmetros** → gerenciar unidades, seguimentos, tipos, orçamentistas
5. **Produtos/Componentes** → criar com unidade, atribuir ficha técnica
6. **Fichas Técnicas** → criar equipe (adicionar cargos), criar produto (adicionar materiais), criar serviço (vincular recursos)
7. **Orçamentos** → criar, adicionar itens, calcular, aprovar, rejeitar, nova versão
8. **Proposta** → visualizar, exportar PDF
9. **BI Preços** → selecionar tipo/item, ver gráficos e tabela

### 5.2 Verificação de Rotas
- Listar TODAS as rotas registradas em `backend/main.py`
- Verificar se cada rota tem um router implementado
- Verificar se cada router tem os endpoints documentados

### 5.3 Verificação de Schemas vs Models
- Para cada model em `backend/models/`, verificar se existe schema correspondente em `backend/schemas/`
- Campos do schema devem corresponder aos campos do model
- Schemas de Create/Update/Read devem estar completos

### 5.4 Verificação da API do Frontend
- Para cada função em `frontend/app/lib/api.ts`, verificar se a rota backend existe
- Métodos HTTP devem corresponder (GET, POST, PUT, DELETE)
- Parâmetros de query string devem corresponder

---

## REGRAS DE EXECUÇÃO

1. NÃO delete os docs/ existentes
2. NÃO faça deploy
3. NÃO altere a lógica de negócio existente (motor BDI, fórmulas)
4. Commits em português, um por bloco lógico
5. Se encontrar algo que não consegue corrigir sem quebrar, documente em um arquivo `ISSUES.md`
6. Priorize correções que EVITAM quebras em vez de novas features
7. Ao final, crie um resumo do que foi feito e do que ficou pendente
