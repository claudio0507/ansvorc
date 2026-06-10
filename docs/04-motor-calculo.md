# Motor de Cálculo — BDI e Fator K

## Etapa 1: BDI Sombra (Itens Não Faturáveis)

Aplica-se a blocos `operacional` e `excepcionais`. Garante que custos indiretos paguem seus próprios impostos.

```
carga_recuperacao = despesas_adm + pis + cofins + issqn
custo_com_carga = custo_direto × (1 + carga_recuperacao)
```

### Impacto do REIDI

Se `beneficio_reidi = TRUE`: PIS = 0% e COFINS = 0%

---

## Etapa 2: BDI Completo (Itens Faturáveis)

```
BDI = [(1 + ADM) × (1 + CF) × (1 + Margem)] / [1 - (PIS + COFINS + ISSQN + ICMS)] - 1
```

### Matriz MOD FAT — Quais Impostos Aplicar

| MOD FAT | PIS | COFINS | ISSQN | ICMS |
|---|---|---|---|---|
| BDI-MO | Sim | Sim | Sim | Não |
| BDI-MAT+MO | Sim | Sim | Sim | Não |
| BDI+ICMS | Sim | Sim | Não | Sim |
| FAT DIR SIMP | Não | Não | Não | Não |

### Exemplo (BDI-MAT+MO, Margem 10%, PR, sem REIDI)

```
Numerador   = (1.13) × (1.015) × (1.10) = 1.261845
Denominador = 1 - (0.0065 + 0.03 + 0.035) = 0.9285
BDI = 35.89%
```

### Mesmo cenário com REIDI = SIM

```
Denominador = 1 - (0 + 0 + 0.035) = 0.965
BDI = 30.74%
Diferença: 5.15pp a menos no preço final
```

---

## Etapa 3: Fator K — Rateio Top-Down

Custos não faturáveis são distribuídos proporcionalmente sobre itens faturáveis.

```
1. Preço_Base_Faturável = Custo_Direto × (1 + BDI)
2. Peso(%) = Preço_Base_Item / Subtotal_Faturavel
3. Rateio = Peso(%) × Total_Diluir
4. Preço_Final = Preço_Base + Rateio
```

---

## Etapa 4: Margem Líquida Real

```
Lucro_Absoluto = Σ (custo_direto × (1 + ADM) × (1 + CF) × (margem/100))
Margem_Líquida(%) = Lucro_Absoluto / Total_Proposta × 100
```

---

## Regras de Segurança

1. Motor no backend — nunca client-side em produção
2. Snapshots imutáveis para auditoria
3. Testes obrigatórios: UF × REIDI × MOD FAT × Margem
4. Valores monetários: DECIMAL(12,4), nunca float
