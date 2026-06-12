# Sub-projeto D — Orçamento + Proposta

**Data:** 2026-06-12
**Branch alvo:** feat/melhorias-v2
**Contexto:** Último dos 4 sub-projetos da demanda v2 (A=status ✅, C=dashboard ✅, B=prazos/notificações ✅, D=orçamento+proposta). Depende de A (status/freeze) e BLOCO 2 (config, orçamentista, proposta base já existente).

## Objetivo

1. Editor de orçamento: Enter aciona Calcular; valores calculados "fixam" ao revisitar; preço unitário reflete desconto.
2. Backend: diretor comercial no ConfigSistema; garantir unidade do Produto em itens de produto.
3. Proposta comercial: cabeçalho/rodapé redesenhados, descrições e textos livres editáveis (sem alterar a composição), QR WhatsApp do orçamentista.

## Decisões travadas (brainstorm + mockup aprovado)

- Layout da proposta aprovado via mockup: cabeçalho 3-colunas (logo esq / "PROPOSTA COMERCIAL" centro / nome+versão+data dir); rodapé opção A (Aprovado por/diretor esq; Elaborado por/orçamentista + QR dir).
- Diretor comercial: 4 campos no `ConfigSistema` (singleton).
- QR WhatsApp: lib frontend `qrcode.react`, a partir de `wa.me/<telefone limpo>`, QR puro sem ícone.
- Descrições editáveis na proposta gravam `descricao_cliente` (não tocam `descricao`/composição).
- Trava de edição da proposta: status do orçamento (editável em rascunho/reprovado; trava de Enviado pra cima).
- Unidade: garantir Produto manda em itens de produto; serviço mantém ficha.
- Fixar valores: reconstruir o resumo dos itens persistidos no reload (frontend).
- Manter "Desenvolvido por Viaxis Tech HUB" no rodapé inferior.
- PDF (`gerar_pdf_proposta`): FORA DE ESCOPO — só a tela agora; PDF fica divergente como pendência (D2 futuro).
- Motor de cálculo/BDI: intocado.

## Seção 1 — Editor (frontend only)

`frontend/app/routes/orcamentos.$id.tsx`.

- **Enter→Calcular:** nos inputs editáveis (quantidade, margem, desconto), `onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); calcular() } }}`. Só quando não-readonly.
- **Fixar valores:** os preços já persistem (backend commita no `/calcular`) e voltam no `listItens`. Hoje `carregar()` faz `setResultado(null)` → o painel de resumo some até recalcular. Ajuste: criar `resumoDeItens(itens, orc)` que deriva o mesmo shape do retorno de `calcular()` (subtotal, desconto total, total líquido, margem) somando os campos persistidos dos itens (`preco_venda_total`, `desconto_rateado`), e popular `resultado` no carregar a partir disso. Valores fixam visualmente ao revisitar/atualizar.
- **Preço unitário dinâmico:** a coluna de preço unitário do editor usa `preco_venda_unitario_final` (pós-desconto) — já existe no item; garantir que é esse o exibido, atualizado ao recalcular.

Sem mudança de backend (motor intocado).

## Seção 2 — Backend: diretor + unidade

### Diretor comercial
`backend/models/extra_models.py` — em `ConfigSistema`:
```python
diretor_nome: Mapped[str | None] = mapped_column(String(200), nullable=True)
diretor_funcao: Mapped[str | None] = mapped_column(String(100), nullable=True)
diretor_telefone: Mapped[str | None] = mapped_column(String(30), nullable=True)
diretor_email: Mapped[str | None] = mapped_column(String(150), nullable=True)
```
`backend/schemas/extra_schemas.py` — `ConfigSistemaRead` e `ConfigSistemaUpdate` ganham os 4 campos (todos opcionais).
`backend/routers/extra_routers.py` — `PUT /config` (hoje só seta `nome_empresa`): estender para setar os campos do diretor quando presentes no payload.

### Unidade do Produto
`backend/routers/orcamento_routers.py` — `_custo_e_unidade_da_ficha`: o ramo `produto_id` já usa `prod.unidade` (via `unidade_id`→`UnidadeMedida.sigla`). Ajustar o ramo `ficha_produto` para também preferir a unidade do cadastro Produto quando houver Produto vinculado com `unidade_id`; serviço (`ficha_servico`) mantém `f.unidade`. Ajuste cirúrgico, sem tocar no cálculo de custo.

## Seção 3 — Proposta (frontend)

`frontend/app/routes/proposta.tsx`. Novo campo backend `texto_topo_proposta`.

### Backend para a proposta
- `backend/models/orcamento_models.py` — `texto_topo_proposta: Mapped[str | None] = mapped_column(Text, nullable=True)`.
- `backend/schemas/orcamento_schemas.py` — `texto_topo_proposta` em `OrcamentoUpdate` e `OrcamentoRead`.

### Cabeçalho (3 colunas)
- Esquerda: logo PNG (`config.logo_path`). REMOVER "orcOS" + nome empresa.
- Centro: "PROPOSTA COMERCIAL".
- Direita: nome da proposta (obra) + "Proposta {numero} · v{versao}" + "Emissão: {data}".

### Rodapé (opção A)
- Esquerda: "Aprovado por" + `config.diretor_nome/funcao/telefone/email`.
- Direita: "Elaborado por" + orçamentista + QR WhatsApp.
- Manter "Desenvolvido por Viaxis Tech HUB" embaixo.

### Edição inline (só status rascunho/reprovado)
- Descrições de item editáveis → `orcamentoApi.updateItem(orcId, itemId, { descricao_cliente })`.
- Texto topo (entre cabeçalho e itens) → novo `texto_topo_proposta`, salvo via `orcamentoApi.update`.
- Texto rodapé (entre total e rodapé) → reusa `texto_livre_proposta` existente.
- Preço unitário, quantidade, preço total, subtotal, total: NUNCA editáveis.
- `editavel = ["rascunho","reprovado"].includes(orc.status)`; quando não-editável, render read-only. Toast ao salvar.

### QR WhatsApp
- Dep frontend `qrcode.react`. Componente `<QRCodeSVG value={`https://wa.me/${tel}`} size={60} />` onde `tel` = dígitos do telefone do orçamentista com prefixo 55. QR puro, sem logo/ícone. Não renderizar se sem telefone.

## Seção 4 — Deps, testes

- Dep nova: `qrcode.react` (frontend).
- Testes backend (pytest): `PUT /config` persiste campos do diretor; resolver de unidade usa Produto pra item de produto (produto_id e ficha_produto com Produto vinculado); `texto_topo_proposta` round-trip via PUT/GET orçamento.
- Frontend: sem typecheck no sandbox (sem node_modules) — validar por review/grep (QR import, sem cor nova, edição gravando os campos certos).

## Arquivos tocados

**Backend:** `models/extra_models.py`, `models/orcamento_models.py`, `schemas/extra_schemas.py`, `schemas/orcamento_schemas.py`, `routers/extra_routers.py`, `routers/orcamento_routers.py`, `tests/` (config + unidade + texto_topo).
**Frontend:** `package.json` (qrcode.react), `routes/proposta.tsx`, `routes/orcamentos.$id.tsx`, `routes/parametros.tsx`.

## Fora de escopo

- Atualizar `gerar_pdf_proposta` (PDF) ao novo layout — pendência D2. A tela e o PDF divergirão até lá.
- Motor de cálculo/BDI/fórmulas — intocado.
- Múltiplos diretores; aprovação eletrônica/assinatura.
