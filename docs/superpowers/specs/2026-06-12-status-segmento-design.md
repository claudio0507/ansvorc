# Sub-projeto A — Status + Segmento + data_limite

**Data:** 2026-06-12
**Branch alvo:** feat/melhorias-v2
**Contexto:** Primeiro de 4 sub-projetos decompostos da demanda v2 (A=status, B=prazos/notificações, C=dashboard, D=orçamento+proposta). A é fundacional: C e B dependem dos novos status.

## Objetivo

Evoluir o status do orçamento de 3 estados lineares para um funil de 6 estados com re-edição; adicionar segmentos multi-valor (classificação) ao cabeçalho do orçamento; adicionar a coluna `data_limite` no cadastro. Calendário, notificações, gráficos e métricas por status ficam para C/B.

## Decisões travadas (brainstorm)

- Máquina: **funil linear com re-edição**.
- Congelamento de itens: **ao Enviar** (Enviado/Aprovado/Perdida/Fechado congelam; Rascunho/Reprovado editam).
- Segmento: **só classificação**, não restringe itens. Persistência em **tabela de junção**.
- Migração de dados: **DB descartável** — sem migration, só atualizar seed.
- `data_limite`: **coluna entra agora** (campo + cadastro). Calendário/alertas em B.
- Status no banco: **slug minúsculo**; label no front.
- Cores: **NENHUMA cor nova**. Reusar variantes já existentes em `status-badge.tsx` (`secondary | warning | success | destructive`).

## Seção 1 — Máquina de status

Banco guarda slug minúsculo. Default `rascunho`.

| slug | label | terminal | congela itens |
|------|-------|----------|---------------|
| rascunho | Rascunho | não | não (editável) |
| enviado | Enviado | não | SIM |
| aprovado | Aprovado | não | SIM |
| reprovado | Reprovado | não | não (reabre) |
| perdida | Perdida | SIM | SIM |
| fechado | Fechado | SIM | SIM |

Transições (substitui `_TRANSICOES_STATUS` em `backend/routers/orcamento_routers.py`):

```python
_TRANSICOES_STATUS = {
    "rascunho":  {"enviado"},
    "enviado":   {"aprovado", "reprovado", "perdida"},
    "aprovado":  {"fechado", "perdida"},
    "reprovado": {"rascunho"},
    "perdida":   frozenset(),
    "fechado":   frozenset(),
}
```

Congelamento: `_pode_editar_itens(orc)` → `True` só para `rascunho`/`reprovado`. Substitui o check `orc.status != "rascunho"` (orcamento_routers.py:62). Observações internas passam a ser **opcionais**. O endpoint legado `/aprovar` é descontinuado em favor do PATCH de status genérico (orcamento_routers.py:213); `aprovado_em` continua preenchido na transição para `aprovado`. `flag_aprovacao` de item (aprovação por linha) permanece intacto — conceito distinto.

## Seção 2 — Multi-segmento

Novo model em `backend/models/extra_models.py`:

```python
class OrcamentoSegmento(Base):
    __tablename__ = "orcamento_segmentos"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    orcamento_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orcamentos.id", ondelete="CASCADE"), nullable=False
    )
    seguimento: Mapped[str] = mapped_column(String(50), nullable=False)
    __table_args__ = (UniqueConstraint("orcamento_id", "seguimento"),)
```

- Valores vêm de `ParametroSeguimento`. Validação **leve**: cada segmento enviado deve existir em `parametros_seguimentos` no POST/PUT; caso contrário 422. Evita lixo no dashboard.
- Papel: só classificação. Não restringe itens. Filtro de catálogo por seguimento no modal continua independente.
- CRUD: definido no cadastro/edição do orçamento. PUT substitui em bloco (delete-orphan + re-insert do array). UNIQUE evita duplicata.

Relationship em `Orcamento`:

```python
segmentos: Mapped[list["OrcamentoSegmento"]] = relationship(
    cascade="all, delete-orphan", lazy="selectin"
)
```

`selectin` evita N+1 ao listar.

Schema:
- `OrcamentoCreate`/`OrcamentoUpdate`: `segmentos: list[str] = []`
- `OrcamentoRead`: `segmentos: list[str]` (serializado de `[s.seguimento for s in orc.segmentos]`)

## Seção 3 — data_limite + UI

Coluna em `Orcamento`:

```python
data_limite: Mapped[date | None] = mapped_column(Date, nullable=True)
```

Só o campo + cadastro aqui. Calendário/alertas D-1/D-0 → sub-projeto B.

Schema: `OrcamentoCreate/Update` ganham `data_limite: date | None = None`; `OrcamentoRead` expõe.

Frontend:
- `routes/orcamentos.novo.tsx` — form: input `date` (Data-limite) + multi-select de Segmentos (de `parametroApi`).
- `routes/orcamentos.$id.tsx` — editor: dropdown de status com 6 labels substitui botões Aprovar/Rejeitar; desabilita transições inválidas; bloqueia edição de itens quando não-editável.
- `lib/api.ts` — `orcamentoApi.create/update` passam campos novos; sem rota nova (reusa PATCH de status).
- `components/status-badge.tsx` — estender `STATUS_MAP` para 6 estados **reusando variantes existentes**, sem cor nova:
  - rascunho → secondary, enviado → warning, aprovado → success, reprovado → destructive, perdida → secondary, fechado → success
  - (mapeamento monocromático coerente com Discord Dark; ajustável na revisão sem introduzir token novo)

Seed: `seeds.py` cria orçamentos exemplo com status novos válidos. Sem migration (DB descartável).

## Testes

- Novo `tests/test_status_transicoes.py`: cada aresta válida aceita (200/PATCH), cada inválida rejeitada (422), freeze de itens nos estados congelados, reabertura reprovado→rascunho.
- Estender `tests/test_orcamentos.py`: segmentos (add, replace em bloco, dedupe via UNIQUE, rejeição de segmento inexistente), `data_limite` round-trip.

## Fora de escopo (vai para C/B/D)

Calendário no dashboard, sino de notificação, motor de alerta D-1/D-0, gráfico de status (Shadcn Charts), métricas Total Orçado (Enviado) / Margem Líquida (Fechado), redesenho da proposta, Enter→Calcular, unidade do Produto, preço unitário dinâmico.

## Arquivos tocados

- `backend/models/extra_models.py` (novo model OrcamentoSegmento)
- `backend/models/orcamento_models.py` (data_limite, relationship segmentos)
- `backend/schemas/orcamento_schemas.py` (segmentos, data_limite em Create/Update/Read)
- `backend/routers/orcamento_routers.py` (transições, _pode_editar_itens, persistência de segmentos)
- `backend/seeds.py` / `backend/seeds_prod.py` (status novos + segmentos exemplo)
- `frontend/app/routes/orcamentos.novo.tsx`, `orcamentos.$id.tsx`
- `frontend/app/lib/api.ts`
- `frontend/app/components/status-badge.tsx`
- `tests/test_status_transicoes.py` (novo), `tests/test_orcamentos.py`
