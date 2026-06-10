# AGENTS.md — Instruções para Agentes de Desenvolvimento

## Regra de Ouro

> **Leia a documentação antes de escrever qualquer código.**
> Toda decisão de arquitetura, schema, fórmula de cálculo e fluxo de tela está documentada em `docs/`.

## Ordem Obrigatória de Leitura

1. `docs/01-visao-geral.md` — Produto, papéis, arquitetura
2. `docs/02-schema-banco-dados.md` — Schema completo (NÃO crie tabelas fora deste spec)
3. `docs/03-fichas-tecnicas.md` — Lógica das fichas e fórmulas
4. `docs/04-motor-calculo.md` — Motor BDI e Fator K
5. `docs/05-ux-telas.md` — Wireframes e design system
6. `docs/06-plano-fases.md` — Roadmap

## Especificação é Lei

Os documentos em `docs/` SÃO a especificação. O código DEVE ser implementado conforme eles.
Se houver divergência entre docs e código, O DOCUMENTO está certo.

## Convenções

- Backend: FastAPI + SQLAlchemy + Pydantic v2
- Frontend: HTML/CSS/JS vanilla ou React (conforme implementado)
- Decimais: SEMPRE Decimal do Python, NUNCA float
- Campos monetários: DECIMAL(12,4)
- Commits em português
- NÃO deletar docs existentes
- NÃO fazer deploy sem aprovação
