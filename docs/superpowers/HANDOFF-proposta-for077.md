# Handoff — Proposta FOR-077 (retomar em nova sessão)

**Branch:** feat/melhorias-v2
**Data do handoff:** 2026-06-13

## Onde paramos

Tarefa: implementar o template de proposta comercial FOR-077 (ver `PROMPT_PROPOSTA.md` na raiz) + redesenhar o documento da proposta com visual moderno/corporativo/conciso + **garantir o PDF funcional**.

Decomposto em **3 fases sequenciais**, cada uma com ciclo spec → plan → execução (subagent-driven) → review → commit/push:

- **F1 — Backend gaps** ✅ CONCLUÍDA (subagent-driven, 11 commits fce0bff..44c3215, 179 testes verdes).
- **F2 — Editor** ← PRÓXIMA (tela `proposta.$id.tsx` + aba Empresa nos Parâmetros). A brainstormar.
- **F3 — Documento + PDF** (redesenhar `proposta.tsx` cliente + atualizar `export_pdf.py` WeasyPrint pro layout FOR-077; PDF funcional). A brainstormar.

## F1 — o que foi entregue

Plano: `docs/superpowers/plans/2026-06-13-proposta-for077-fase1-backend.md`. Tudo TDD, review spec+qualidade por task + review final (opus).

- PATCH `/api/v1/orcamentos/{id}/itens/{item_id}` → grava `descricao_cliente` (preserva `descricao`). Guards: 404 orç → 403 congelado → 404 item. Schema `OrcamentoItemDescricaoPatch` (extra=forbid, min_length=1).
- PUT `/api/v1/config` reescrito com `model_dump(exclude_unset=True)` → grava os 19 campos, limpa via null, rejeita `nome_empresa=null` (422), `extra=forbid` em ConfigSistemaUpdate.
- Helper puro `backend/services/proposta_fallback.py::montar_proposta(orc, config)` → precedência orç→config→literal; numéricos com `is not None` (0% honrado).
- GET `/api/v1/orcamentos/{id}/proposta` → orcamento/config/cliente/itens/resolvidos/garantia_texto. **Fonte única p/ F2 e F3.** Resolve literais mesmo sem config (stub). `garantia_texto` com pct normalizado.
- Seed FOR-077 em `backend/seeds.py::seed_extra` (valores verbatim do PROMPT_PROPOSTA).
- Testes: `tests/test_proposta_for077.py` (21 testes).

### Débitos deferidos do review final (cabem em F2/F3, não bloqueiam)

- GET /proposta retorna `dict` cru (sem `response_model`). Quando F2 consumir e o contrato estabilizar, criar `PropostaRead` tipado.
- `garantia_texto` é montado no router; se F3/PDF reconstruir a frase, mover p/ camada pura (`proposta_fallback`) p/ evitar drift.
- Sem teste de RBAC dedicado p/ /proposta (coberto pelo middleware testado em outro lugar).

## Próximo passo concreto

F2 (editor) → **`superpowers:brainstorming`** primeiro (decidir UX da tela `proposta.$id.tsx` por seções + aba Empresa em `parametros.tsx`), depois spec → writing-plans → subagent-driven. F2 consome o GET `/proposta` como fonte de dados.

## Decisões já travadas (não reabrir)

- Escopo: os 3 (editor + documento + PDF). PDF mantém **WeasyPrint**, só atualiza o HTML interno (`_build_html`) pro FOR-077.
- PUT /config usa `model_dump(exclude_unset=True)` (também corrige o bug "não dá pra limpar campo" apontado na revisão).
- PATCH de descrição grava **`descricao_cliente`** (não `descricao` — preserva composição).
- Fallback ConfigSistema exposto via **endpoint dedicado `GET /orcamentos/{id}/proposta`** (fonte única p/ F2 e F3).
- Sem Alembic/migrations. Motor BDI intocado. Sem cor nova (tema Discord Dark).

## Estado verificado do backend (F1 parte já existe)

- Model `Orcamento`: 13 campos FOR-077 **presentes** (escopo, modalidade, faturamento_direto, medicao_pagamento, clausula_tributaria, reajustamento, garantia_retencao_pct, garantia_devolucao_dias, entrega_as_built, testemunha_*).
- Model `ConfigSistema`: 13 campos **presentes** (cnpj, banco/agencia/conta_corrente, diretor_cpf, contato_comercial_*, *_padrao, declaracoes_padrao).
- Schemas Orcamento + ConfigSistema **expõem** os campos novos.
- **GAPS F1 (a fazer):** PATCH item ausente; PUT /config só grava nome+diretor (faltam 13 campos); seed NÃO populado com FOR-077; helper de fallback + endpoint /proposta ausentes.

## Gaps F2/F3 (depois)

- F2: `frontend/app/routes/proposta.$id.tsx` não existe (editor por seções); aba Empresa em `parametros.tsx` só tem nome+diretor (faltam 17 campos).
- F3: `proposta.tsx` (documento cliente) está no layout sub-projeto D, sem as 19 seções FOR-077; `export_pdf.py` (414 linhas, WeasyPrint) está no layout antigo.

## Pendências gerais do projeto (do code-review xhigh)

- Soft-delete: o dev parceiro já corrigiu (`ff0e6cb fix: soft-delete retorna 404 + filtro ativo=True`). ✅
- 2 testes que falhavam (test_deletar_bdi, test_deletar_ficha_equipe) devem estar verdes agora — confirmar com `py -m pytest`.
- Proposta v1 esconde linha de desconto mas subtrai no total (finding #2 da revisão) — ainda aberto; cabe na F3 ao redesenhar o documento.

## Artefatos versionados

- `PROMPT_PROPOSTA.md` — prompt original FOR-077 (6 tarefas, valores de seed nas linhas 96-109).
- `proposta-template-preview.html` — mockup das 19 seções (referência visual).
- `docs/08-template-proposta.md` — mapeamento dos campos.
- `docs/superpowers/specs/` e `docs/superpowers/plans/` — specs/plans de todas as fases (A,B,C,D + FOR-077 F1).

## PR aberto

PR #4 (`feat/melhorias-v2` → `main`) cobre A/B/C/D. O trabalho FOR-077 continua na mesma branch e entra no mesmo PR (ou um PR separado, decidir ao finalizar).
