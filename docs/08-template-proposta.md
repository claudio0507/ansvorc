# Template de Proposta Comercial

Estrutura derivada do FOR 077 (modelo atual), adaptada ao sistema orcOS.

## Layout da Proposta

```
┌─────────────────────────────────────────────────────┐
│  LOGO + NOME EMPRESA           N° Proposta: XXX_XX │
│  (ConfigSistema.nome_empresa)    Versão: XX         │
│                                  Data: DD/MM/AAAA   │
├─────────────────────────────────────────────────────┤
│                                                     │
│  [Cidade], [data por extenso]                      │
│                                                     │
│  À [Cliente.nome]                                  │
│                                                     │
│  [obra] — título do objeto                          │
│                                                     │
│  [texto_topo_proposta] — texto livre de abertura    │
│  (declarações, preâmbulo legal)                     │
│                                                     │
├─────────────────────────────────────────────────────┤
│  OBJETO                                            │
│  [obra] + [escopo]                                 │
│                                                     │
│  ESCOPO                                            │
│  [escopo — descrição detalhada]                    │
│                                                     │
│  MODALIDADE                                        │
│  [modalidade] — ex: Preço Unitário, Preço Global   │
│                                                     │
├─────────────────────────────────────────────────────┤
│  PREÇO                                             │
│  ┌─────────────────────────────────────────────┐   │
│  │ ITENS DA PLANILHA (serviços + produtos)     │   │
│  │ Por seguimento: EPS | HORIZONTAL | VERTICAL│   │
│  │ + Estrutura Operacional                      │   │
│  │ + Itens Excepcionais                         │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  Sem REIDI:  R$ X.XXX.XXX,XX (extenso)            │
│  Com REIDI:   R$ X.XXX.XXX,XX  (se aplicável)     │
│                                                     │
│  Alíquotas consideradas:                            │
│  ┌──────────────┬──────────┐                        │
│  │ ISS          │ X%       │                        │
│  │ PIS (c/REIDI)│ X%      │                        │
│  │ COFINS(c/REIDI)│ X%    │                        │
│  └──────────────┴──────────┘                        │
│                                                     │
├─────────────────────────────────────────────────────┤
│  PRAZO                                             │
│  [prazo_entrega]                                    │
│  [clausula_tributaria — texto sobre IBS/CBS]       │
│                                                     │
│  FATURAMENTO DIRETO                                │
│  [faturamento_direto — texto ou "Não aplicável"]   │
│                                                     │
│  MEDIÇÃO E PAGAMENTO                               │
│  [medicao_pagamento]                                │
│                                                     │
│  DADOS BANCÁRIOS                                   │
│  Banco: [banco]  Agência: [agencia]                │
│  Conta: [conta_corrente]                           │
│                                                     │
│  REPRESENTANTE LEGAL                               │
│  [diretor_nome] — [diretor_funcao]                 │
│  [diretor_email] — CPF [diretor_cpf]               │
│                                                     │
│  TESTEMUNHA                                        │
│  [testemunha_nome] — [testemunha_email]             │
│  CPF [testemunha_cpf]                              │
│                                                     │
├─────────────────────────────────────────────────────┤
│  REAJUSTAMENTO                                     │
│  [reajustamento]                                    │
│                                                     │
│  GARANTIA CONTRATUAL                               │
│  Retenção de [garantia_retencao_pct]% com          │
│  devolução em [garantia_devolucao_dias] dias.      │
│                                                     │
│  ENTREGA DE AS BUILT                               │
│  [entrega_as_built]                                 │
│                                                     │
│  VALIDADE DA PROPOSTA                              │
│  [validade_proposta]                                │
│                                                     │
│  OBSERVAÇÃO                                        │
│  [texto_livre_proposta]                             │
│                                                     │
├─────────────────────────────────────────────────────┤
│  CONTATO COMERCIAL                                 │
│  [contato_comercial_nome]                           │
│  Fone: [contato_comercial_fone]                    │
│  E-mail: [contato_comercial_email]                  │
│                                                     │
│  _______________________________                   │
│  [contato_comercial_nome]                           │
│  [contato_comercial_funcao]                        │
│                                                     │
│  [QR Code WhatsApp]                                │
└─────────────────────────────────────────────────────┘
```

## Campos da Proposta — Mapeamento

### Campos existentes no Model Orcamento

| Campo no Model | Tópico na Proposta | Preenchimento |
|---|---|---|
| `numero` | N° da Proposta | Automático (149_26) |
| `versao` | Versão | Automático |
| `created_at` | Data | Automático |
| `uf_execucao` | Cidade/UF | Orçamentista |
| `obra` | OBJETO / Título | Orçamentista |
| `cliente.nome` | "À [Cliente]" | Cadastro |
| `beneficio_reidi` | Cálculo REIDI | Toggle |
| `total_proposta` | PREÇO total | Calculado |
| `prazo_entrega` | PRAZO | Orçamentista |
| `validade_proposta` | VALIDADE | Orçamentista |
| `tipo_frete` | FATURAMENTO DIRETO | Orçamentista |
| `condicoes_pagamento` | MEDIÇÃO E PAGAMENTO | Orçamentista |
| `texto_topo_proposta` | Declarações/preâmbulo | Orçamentista |
| `texto_livre_proposta` | OBSERVAÇÃO | Orçamentista |
| `orcamentista_id` → nome/função | CONTATO COMERCIAL | Cadastro |
| `desconto_percentual` | Desconto no total | Orçamentista |
| `segmentos` | Agrupamento na planilha | Orçamentista |

### Campos NOVOS necessários (Orcamento)

| Campo | Tipo | Tópico | Default |
|---|---|---|---|
| `escopo` | `Text` | ESCOPO | null |
| `modalidade` | `String(50)` | MODALIDADE | "Preço Unitário" |
| `faturamento_direto` | `String(300)` | FATURAMENTO DIRETO | "Não aplicável." |
| `medicao_pagamento` | `Text` | MEDIÇÃO E PAGAMENTO | null |
| `clausula_tributaria` | `Text` | Clausula IBS/CBS | null (texto fixo sobre reforma tributária) |
| `reajustamento` | `Text` | REAJUSTAMENTO | null (texto padrão sobre IPCA/IGPM) |
| `garantia_retencao_pct` | `Decimal(5,2)` | GARANTIA (%) | null (ex: 5) |
| `garantia_devolucao_dias` | `Integer` | GARANTIA (dias devolução) | null (ex: 60) |
| `entrega_as_built` | `String(300)` | ENTREGA AS BUILT | "Não aplicável." |
| `testemunha_nome` | `String(200)` | TESTEMUNHA nome | null |
| `testemunha_email` | `String(150)` | TESTEMUNHA e-mail | null |
| `testemunha_cpf` | `String(20)` | TESTEMUNHA CPF | null |

### Campos NOVOS necessários (ConfigSistema — dados empresa)

| Campo | Tipo | Tópico | Default |
|---|---|---|---|
| `cnpj` | `String(20)` | Declarações | null |
| `banco` | `String(100)` | DADOS BANCÁRIOS | null |
| `agencia` | `String(20)` | DADOS BANCÁRIOS | null |
| `conta_corrente` | `String(30)` | DADOS BANCÁRIOS | null |
| `diretor_cpf` | `String(20)` | REPRESENTANTE LEGAL | null |
| `contato_comercial_nome` | `String(200)` | CONTATO COMERCIAL | null |
| `contato_comercial_funcao` | `String(100)` | CONTATO COMERCIAL | null |
| `contato_comercial_fone` | `String(30)` | CONTATO COMERCIAL | null |
| `contato_comercial_email` | `String(150)` | CONTATO COMERCIAL | null |
| `clausula_tributaria_padrao` | `Text` | Clausula IBS/CBS padrão | null |
| `reajustamento_padrao` | `Text` | REAJUSTAMENTO padrão | null |
| `garantia_retencao_padrao_pct` | `Decimal(5,2)` | % retenção padrão | 5 |
| `garantia_devolucao_padrao_dias` | `Integer` | Dias devolução padrão | 60 |

### Seções com Texto Fixo (template padrão)

Estas seções têm texto padrão que pode ser editado por proposta:

1. **Declarações** → `texto_topo_proposta` (7 bullets legais)
2. **Clausula tributária** → texto sobre IBS/CBS (pode vir do Config ou ser editado)
3. **Reajustamento** → texto sobre IPCA/IGPM
4. **Garantia contratual** → montado a partir de `% retenção` + `dias devolução`

Texto padrão das declarações (para preencher no seed):
```
Que respeita integralmente as condições estabelecidas na TR.ENG.XXX.XXXX.XXXX.
Que possui conhecimento das Políticas de Meio Ambiente, corporativa sobre Mudanças Climáticas e de Responsabilidade Social.
Que possui conhecimento e que cumpre a legislação anticorrupção e, em especial a Lei 12.846/13.
Que executará os serviços de acordo com o projeto e suas modificações, ordem de serviço, e de acordo com as normas e especificações técnicas.
Que se obriga a dispor, para emprego imediato, de todos os recursos necessários para a execução dos serviços contratados, no prazo estipulado, sem custos adicionais.
Que tem pleno conhecimento das condições locais necessárias para a formação dos preços.
Que não possui em seu quadro de empregados, menor de 18 anos em trabalho noturno, insalubre ou perigoso, e, ainda, não possuir empregado menor de 16 anos.
Que a proponente não mantém qualquer relação ou vínculo de qualquer natureza com a Contratante ou empresas do mesmo Conglomerado econômico a qual pertence.
Que conhece o Código de Ética e Integridade, constantes nos documentos recebidos.
Se comprometer a estar instalado e pronto para o início dos serviços no prazo imposto no termo de referência.
Que em seu preço estão inclusas todas as despesas com a prestação dos serviços, equipamentos, mão-de-obra, tributos, encargos, impostos, lucro, e as demais despesas diretas e indiretas que possam recair sobre a presente prestação de serviços.
Que executará todos os serviços de acordo com o preço e o prazo, estipulados nesta carta.
Que tem pleno conhecimento sobre a retenção de X% das medições sobre o valor bruto da medição a título de caução.
```

## Regras de Renderização

1. **N° Proposta** → `{numero}_{versao:02d}` (ex: 149_26)
2. **Cidade/Data** → cidade da UF (`uf_execucao`) + data por extenso
3. **PREÇO extenso** → gerado automaticamente do `total_proposta`
4. **REIDI** → se `beneficio_reidi = true`, mostra PIS/COFINS zerados e valor com isenção
5. **Planilha** → itens agrupados por seguimento com colunas: Item | Descrição | Un | Qtd | Preço Unitário | Preço Total
6. **Alíquotas** → tabela automática do `bd_BDI` da UF
7. **Campos defaults** → se campo do orçamento é null, usa valor padrão do ConfigSistema

## Ordem dos Tópicos na Proposta

1. Cidade/Data + N° + Versão
2. À [Cliente]
3. [obra] — título
4. Declarações (`texto_topo_proposta`)
5. OBJETO (`obra` + `escopo`)
6. ESCOPO (`escopo`)
7. MODALIDADE (`modalidade`)
8. PREÇO (planilha + total + extenso + REIDI + alíquotas)
9. PRAZO (`prazo_entrega`) + clausula tributária
10. FATURAMENTO DIRETO (`faturamento_direto`)
11. MEDIÇÃO E PAGAMENTO (`medicao_pagamento`)
12. DADOS BANCÁRIOS (ConfigSistema → `banco`, `agencia`, `conta_corrente`)
13. REPRESENTANTE LEGAL (ConfigSistema → `diretor_*` + `diretor_cpf`)
14. TESTEMUNHA (`testemunha_*`)
15. REAJUSTAMENTO (`reajustamento`)
16. GARANTIA CONTRATUAL (`garantia_retencao_pct`% com devolução em `garantia_devolucao_dias` dias)
17. ENTREGA DE AS BUILT (`entrega_as_built`)
18. VALIDADE DA PROPOSTA (`validade_proposta`)
19. OBSERVAÇÃO (`texto_livre_proposta`)
20. CONTATO COMERCIAL (ConfigSistema → `contato_comercial_*`)
21. Assinatura + QR Code