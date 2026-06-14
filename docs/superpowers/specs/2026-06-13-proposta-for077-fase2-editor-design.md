# Proposta FOR-077 — Fase 2: Editor + aba Empresa

**Data:** 2026-06-13
**Branch alvo:** feat/melhorias-v2
**Depende de:** F1 (backend) ✅ — `GET /orcamentos/{id}/proposta`, `PATCH /orcamentos/{id}/itens/{item_id}`, `PUT /config` (19 campos), `montar_proposta` fallback.

## Objetivo

Construir o **editor de proposta comercial** (19 seções FOR-077, layout de cards empilhados + índice interno) acessado por orçamento, e **expandir a aba Empresa** dos Parâmetros para os 17 campos globais do ConfigSistema.

## Decisões travadas (brainstorm)

1. **Editor é rota separada** `/orcamentos/:id/proposta/editar` (arquivo `routes/proposta.editar.$id.tsx`). NÃO altera `proposta.tsx` (documento/PDF — fica para F3). Split limpo: editor (F2) vs documento (F3).
2. **Layout A** — coluna única de cards roláveis no tema Discord Dark + índice interno (coluna estreita à direita) que salta para a seção via scroll. A sidebar global do app (`_app.tsx`) NÃO é tocada.
3. **Auto-save onBlur** por campo (igual `orcamentos.$id.tsx`). Sem botão Salvar global. Toast só em erro. Campos do orçamento → `PUT /orcamentos/:id`; descrição-cliente do item → `PATCH /orcamentos/:id/itens/:item_id`.
4. **Acesso:** editor das 19 seções (por-orçamento) via botão "Editar Proposta" dentro de `orcamentos.$id.tsx`. Defaults globais do ConfigSistema (17 campos) via Parâmetros → aba Empresa.
5. **Itens (seção 7):** só `descricao_cliente` editável (borda de acento, PATCH onBlur); qtd/preço unit/total **read-only** (cálculo BDI). Se orçamento não calculado, aviso "Calcule o orçamento para ver os preços".
6. **Read-only de status:** quando `status ∉ {rascunho, reprovado}`, editor inteiro vira somente-leitura (campos viram texto), igual à regra do editor de itens.
7. **Sem testes de front** — o projeto não tem suíte de testes frontend (só backend em `tests/`). Validação: `npm run build` (typecheck) + verificação manual no browser. Não introduzir framework de teste novo (YAGNI).

## Entrega A — Editor (`proposta.editar.$id.tsx`)

### Fonte de dados
Um único request: `orcamentoApi.getProposta(id)` → `GET /orcamentos/:id/proposta`, devolve:
```
{ orcamento, cliente, config, itens, resolvidos, garantia_texto }
```
Estado local controlado por campo, inicializado de `orcamento`. Auto-save onBlur só dispara se o valor mudou.

### Layout
- Card de cabeçalho da página: voltar ao orçamento + número + status badge + link "Ver documento" (→ `/orcamentos/:id/proposta`).
- Grid `[1fr_180px]`: coluna esquerda = cards das seções; coluna direita = índice fixo (sticky) com as 19 seções, item ativo destacado em acento ao rolar (ou ao clicar).
- Cada seção é um `<SecaoCard titulo="N. Nome" badge="NOVO|EXISTENTE|SISTEMA">…children…</SecaoCard>` com `id="sec-N"` para o scroll.

### Componentes reutilizáveis (dentro do arquivo)
- `SecaoCard({ id, titulo, badge, children })` — card com título em acento + borda inferior (tema).
- `CampoTexto({ label, value, onSave, placeholder, readonly })` — input com auto-save onBlur.
- `CampoTextarea({ label, value, onSave, placeholder, readonly, rows })` — idem textarea.
- Read-only → renderiza o valor como texto (`.val`), não input.

### As 19 seções

| # | Seção | Campo(s) | Fonte | Editável |
|---|-------|----------|-------|----------|
| 1 | Cabeçalho | numero, versao, created_at, uf_execucao | orçamento (sistema) | ❌ |
| 2 | Destinatário | cliente.nome, cnpj_cpf, contato_nome | cliente | ❌ |
| 3 | Objeto | obra | orçamento | ✅ textarea |
| 4 | Declarações | texto_topo_proposta | orçamento (fallback `resolvidos.texto_topo_proposta`) | ✅ textarea |
| 5 | Escopo | escopo | orçamento | ✅ textarea |
| 6 | Modalidade | modalidade | orçamento (placeholder `resolvidos.modalidade` = "Preço Unitário") | ✅ input |
| 7 | Preço | itens[] | sistema | ✅ só `descricao_cliente` (PATCH); resto read-only |
| 8 | Prazo + Tributária | prazo_entrega; clausula_tributaria | orçamento (clausula fallback `resolvidos.clausula_tributaria`) | ✅ input + textarea |
| 9 | Faturamento | faturamento_direto | orçamento (placeholder `resolvidos.faturamento_direto`) | ✅ input |
| 10 | Medição | medicao_pagamento | orçamento | ✅ textarea |
| 11 | Dados Bancários | banco, agencia, conta_corrente | config | ❌ (link "→ editar em Parâmetros") |
| 12 | Representante | diretor_nome/funcao/email/cpf, cnpj, nome_empresa | config | ❌ (link) |
| 13 | Testemunha | testemunha_nome/email/cpf | orçamento | ✅ inputs |
| 14 | Reajustamento | reajustamento | orçamento (fallback `resolvidos.reajustamento`) | ✅ textarea |
| 15 | Garantia | garantia_retencao_pct, garantia_devolucao_dias | orçamento (fallback 5/60) | ✅ inputs + texto auto |
| 16 | As Built | entrega_as_built | orçamento (placeholder `resolvidos.entrega_as_built`) | ✅ input |
| 17 | Validade | validade_proposta | orçamento | ✅ input |
| 18 | Observação | texto_livre_proposta | orçamento | ✅ textarea |
| 19 | Contato Comercial | contato_comercial_nome/funcao/fone/email | config | ❌ (link) |

### Fallback nos campos com `*_padrao` (seções 4, 8, 14, 15)
Input mostra o valor do orçamento se houver. Se vazio, mostra `resolvidos.<campo>` como **placeholder/cinza** com nota "usando padrão da empresa — edite para sobrescrever". Salvar grava no orçamento (vira valor próprio). Para 15 (garantia), placeholders 5/60.

### Garantia (seção 15) — texto automático
Ao salvar pct/dias, recalcula o texto localmente para feedback imediato:
`Retenção de {pct}%, com devolução em {dias} dias após o termo de encerramento.`
(pct normalizado: 5 não 5.00). Backend é fonte de verdade no próximo load (`garantia_texto`).

### Botão de acesso (em `orcamentos.$id.tsx`)
Ao lado do botão "Proposta" (que abre o documento), adicionar "Editar Proposta" → `Link to={/orcamentos/${orcId}/proposta/editar}`.

### Erros
- Load falha → tela de erro + "Voltar ao orçamento" (padrão de `orcamentos.$id.tsx`).
- Save falha → `toast.error(msg)`, mantém valor digitado (não reverte).
- 403 (congelado) já refletido pelo read-only de status; se vier 403 mesmo assim, toast.

## Entrega B — Aba Empresa expandida (`parametros.tsx`)

Expandir o componente `EmpresaConfig` de 4 → 17 campos, organizados em cards:
- **Dados da Empresa:** nome_empresa, cnpj, logo (upload já existe)
- **Representante Legal:** diretor_nome, diretor_funcao, diretor_cpf, diretor_telefone, diretor_email
- **Contato Comercial:** contato_comercial_nome, contato_comercial_funcao, contato_comercial_fone, contato_comercial_email
- **Dados Bancários:** banco, agencia, conta_corrente
- **Textos Padrão:** declaracoes_padrao, clausula_tributaria_padrao, reajustamento_padrao (textareas), garantia_retencao_padrao_pct, garantia_devolucao_padrao_dias (inputs)

Salva via `configApi.update()` (`PUT /config` aceita os 19 campos desde a F1). Manter o upload de logo intacto.

**Save:** um único botão "Salvar" no topo da aba que envia o objeto completo de uma vez (config é singleton, sem concorrência; mais simples que onBlur aqui — diferente do editor de proposta, que é onBlur). Monta o payload com todos os 17 campos editáveis; converte string vazia → `null` para permitir limpar (a F1 grava o `null`), **exceto `nome_empresa`** que é obrigatório (NOT NULL; se vazio, bloqueia o save com toast e não envia). `garantia_retencao_padrao_pct`/`_dias` vazios → `null`; números válidos → número.

## Camada de API (`lib/api.ts`)

Adicionar em `orcamentoApi`:
```ts
getProposta: (id: number) => api.get<any>(`/orcamentos/${id}/proposta`),
patchDescricaoItem: (id: number, iid: number, descricao: string) =>
  api.patch<any>(`/orcamentos/${id}/itens/${iid}`, { descricao }),
```
`configApi.get`/`update` já existem.

## Arquivos tocados

- `frontend/app/routes/proposta.editar.$id.tsx` (novo)
- `frontend/app/routes.ts` (registra a rota)
- `frontend/app/routes/orcamentos.$id.tsx` (botão "Editar Proposta")
- `frontend/app/routes/parametros.tsx` (EmpresaConfig 4→17 campos)
- `frontend/app/lib/api.ts` (getProposta, patchDescricaoItem)

## Fora de escopo (F3)

- Redesenho do documento `proposta.tsx` para as 19 seções FOR-077.
- `export_pdf.py` (WeasyPrint) para o layout FOR-077.
- Finding #2 da revisão (proposta v1 esconde desconto mas subtrai) — cabe em F3.

## Tema (não criar cor nova)

Discord Dark existente: bg #111214, surface #1e1f22, card #2b2d31, elevated #313338, input #383a40, border #3f4147, accent #c32a30, fg #e3e5e8, muted #b5bac1, dimmed #80848e, success #23a55a. Fonte gg sans. Usar os tokens Tailwind do projeto (`bg-card`, `text-primary`, `border`, etc.), não hex direto.
