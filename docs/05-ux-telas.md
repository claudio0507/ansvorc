# UX — Telas e Fluxos

## Design System

| Elemento | Especificação |
|---|---|
| **Tipografia** | SF Pro Display (cabeçalhos), SF Pro Text (dados) |
| **Cor Primária** | Vermelho Alta Noroeste `#c32a30` |
| **Background** | Escala de cinza Apple (`#f8fafc` → `#0f172a`) |
| **Bordas** | Arredondadas 8px |
| **Sidebar** | Translúcida com efeito Glassmorphism/Vibrancy |
| **Ícones** | Font Awesome 6 |
| **Estilo geral** | Inspirado no macOS |

---

## Segmentação (obrigatório)

O sistema é orientado por 4 seguimentos: **EPS, VERTICAL, HORIZONTAL, APOIO**.
Produtos, serviços e equipes são subgrupos desses seguimentos.

---

## Tela 1: Login

Redirecionamento por papel:
- `gestor_bd` → Tela de Bancos de Dados
- `parametrizador` → Tela de Fichas Técnicas
- `orcamentista` → Tela de Orçamentos

---

## Tela 2: Bancos de Dados (Gestor de BD)

Abas: [BDI] [RH] [EPI] [Ferramental] [Frotas] [Materiais] [Estrutura] [Despesas]

Cada aba: grid editável inline, botão "+" para novo, filtro por seguimento/UF.

**BDI:** Grid com filtro por UF. Campos: Modalidade, ICMS, COFINS, PIS, ISSQN, CST Finan, IRPJ, CSLL, Desp ADM.

---

## Tela 3: Fichas Técnicas (Parametrizador)

Abas: [Equipes] [Produtos] [Serviços]

### Editor de Ficha de Equipe
- Select seguimento → grid de cargos com QTD (inteiro)
- Lookups automáticos: MO, EPI, Refeição, Hospedagem
- Custo-dia total no rodapé

### Editor de Ficha de Produto (BOM)
- Select materiais ou sub-produtos → grid com QTD
- Custo total no rodapé

### Editor de Ficha de Serviço
- Select seguimento → filtra recursos do mesmo seguimento
- Vincula: Equipe + Frota + Ferramental + Produto (opcional)
- Produtividade/dia
- Custo unitário calculado: (equipe+frota+ferr)/prod + material

---

## Tela 4: Orçamentos (Orçamentista)

### Seletores em cascata
- Bloco: [Serviços] [Produtos] [Est. Operacional]
- Serviços: seguimento → ficha → MOD FAT
- Produtos: produto direto → MOD FAT (ORÇÁVEL DIRETAMENTE)
- Operacional: item → BDI Sombra aplicado automaticamente

### Regras
- **Unidades bloqueadas:** readonly, definidas no cadastro original
- **Custos automáticos:** calculados da ficha, sem digitação manual
- **Quantidades:** inteiros para pessoas, decimais para materiais
- **Campos de texto:** primeira letra maiúscula automática

### Grid de Itens
Agrupados horizontalmente por bloco:
```
┌── 1. SERVIÇOS ────────────────────────────┐
├── 2. PRODUTOS ────────────────────────────┤
├── 3. ESTRUTURA OPERACIONAL ───────────────┤
├── 4. CUSTOS EXCEPCIONAIS ─────────────────┤
```
Cada bloco = tabela separada com cabeçalho colorido.

### Painel Financeiro
- Apenas "Margem Líquida Real" (verde) e "Total da Proposta" (primária #c32a30) com cor
- Demais textos neutros

### Desconto
- Campo desconto % sobre o total
- Rateado proporcionalmente em todas as linhas

### Versionamento
- Aprovar → snapshot
- Reabrir → nova versão, original preservado

---

## Tela 5: Clientes (CRM)

CRUD simples com busca.

---

## UI/UX Rules

- **Badges:** MAIÚSCULAS. Dark: fundo cinza escuro + texto branco. Light: contraste proporcional.
- **Tema light:** fundo atrás dos cards = cinza claro (#f1f5f9)
- **Responsividade:** perfeito a 100% zoom. Tabelas com overflow-x: auto. Grid colapsa 1 coluna < 768px.
