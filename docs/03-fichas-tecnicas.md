# Fichas Técnicas — Estrutura e Lógica

## Visão Geral

As fichas técnicas transformam insumos brutos (RH, materiais, frotas) em unidades orçamentárias reutilizáveis.

```
FICHA EQUIPE ────────────┐
(quem faz, quanto custa) │
                         ├──► FICHA SERVIÇO ──► ORÇAMENTO (bloco Serviços)
FICHA PRODUTO ──────────┘     (execução)       E
(o que é usado)                │                ├──► ORÇAMENTO (bloco Produtos)
                               │                │     (produtos avulsos, SEM serviço)
                               └────────────────┘
```

---

## Tipo 1: Ficha de Equipe

### Estrutura

| SEGUIMENTO | BD-RH | QTD | CUSTO MO | BD-EPI | EPC | REFEIÇÃO | HOSPEDAGEM | CUSTO-DIA |
|---|---|---|---|---|---|---|---|---|

### Lógica

1. Seleciona um **seguimento** (EPS, HORIZONTAL, VERTICAL, APOIO)
2. Adiciona cargos da tabela `bd_RH` com quantidade de pessoas
3. Lookups automáticos:
   - Custo MO = `bd_RH.custo_diario` do cargo
   - Custo EPI = `bd_EPI.custo_diario` do cargo
   - Refeição = `bd_DESPESAS.refeicao[seguimento]`
   - Hospedagem = `bd_DESPESAS.hospedagem[seguimento]`
4. **Custo-dia total** = Σ (custo_mo + custo_epi + refeição + hospedagem) × quantidade

### Exemplos de Equipes

**EPS:** 1 Encarregado, 1 Operador Bate Estaca, 1 Motorista, 3 Auxiliares
**HORIZONTAL:** 1 Encarregado, 1 Operador Pintura, 1 Motorista, 2 Auxiliares
**VERTICAL:** 1 Encarregado, 1 Motorista, 2 Auxiliares
**APOIO:** 1 Motorista, 1 Auxiliar

---

## Tipo 2: Ficha de Produto

### Estrutura (BOM)

| PRODUTO | MATERIAL | QUANTIDADE | UND | CUSTO UNITÁRIO | CUSTO TOTAL |
|---|---|---|---|---|---|

### Lógica

1. Define o produto (nome, código, unidade)
2. Adiciona componentes: materiais diretos OU sub-produtos (BOM recursivo)
3. **Custo total** = Σ (quantidade × custo_unitario)

### Exemplo: Placa de Sinalização Vertical

| Componente | QTD | UND | Custo Unit | Custo Total |
|---|---|---|---|---|
| Chapa de Aço 1,00 | 1 | UND | 25.50 | 25.50 |
| Cantoneira Modulada | 2 | UND | 10.00 | 20.00 |
| Película | 3 | UND | 90.50 | 271.50 |
| Fixação 1 | 4 | UND | 2.50 | 10.00 |
| **Total** | | | | **327.00** |

### Regras
- **Flag `possui_ficha`:** Produto sem ficha não pode ser usado em orçamento
- **BOM Recursivo:** Um produto pode conter outros produtos
- **Proteção contra ciclo:** Backend valida ausência de referência circular

---

## Tipo 3: Ficha de Serviço

### Estrutura

| SERVIÇO | SEGUIMENTO | PRODUTIVIDADE /DIA | UNIDADE | FICHA-EQUIPE | FICHA-FROTA | BD-FERRAMENTAL | MATERIAL | CUSTO UNITÁRIO |
|---|---|---|---|---|---|---|---|---|

### Fórmula

```
custo_unitario = (equipe.custo_dia_total + frota.custo_diario + ferramental.custo_diario) / produtividade_dia + produto.custo_total
```

### Exemplos

| Serviço | Seg | Prod/dia | Equipe | Frota | Ferr | Mat | Custo/m² |
|---|---|---|---|---|---|---|---|
| Pintura à base d'água | HORIZONTAL | 700 | 2662.74 | 735.34 | 35.90 | 8.13 | 13.04 |
| Defensa Maleável | EPS | 200 | 3085.74 | 1368.54 | 271.05 | 0 | 23.63 |
| Placas Solo c/ 2 suportes | VERTICAL | 20 | 2163.27 | 1032.56 | 24.56 | 0 | 161.02 |

---

## Fluxo de Atualização em Cascata

```
bd_RH (alteração de salário)
  → fichas_equipe_itens.custo_mo (recalculado)
    → fichas_equipe.custo_dia_total (recalculado)
      → fichas_servico.custo_unitario (recalculado)
```

**Orçamentos aprovados (snapshot) NÃO são afetados.**
