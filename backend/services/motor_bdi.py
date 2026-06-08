"""
motor_bdi.py — Motor de cálculo BDI do Sinalys.

Todas as funções são PURAS (sem side effects, sem I/O, sem ORM).
Inputs e outputs são exclusivamente Decimal.

Constantes fiscais (PIS, COFINS, ISSQN, ICMS) nunca são hardcodadas
nos chamadores — são consultadas no bd_BDI e passadas como parâmetro.

Valores padrão documentados (referência, não normativo):
  ADM (despesas administrativas) = 13%
  CF  (custo financeiro)         = 1.5%
  PIS                            = 0.65%
  COFINS                         = 3.00%
  ISSQN PR                       = 3.50%
  ISSQN SP                       = 5.00%
  ICMS                           = 12.00% (quando BDI+ICMS)
  PIS+COFINS acumulado simples   = 3.65%
  PIS+COFINS acumulado BDI+ICMS  = 9.25% (regime cumulativo diferenciado)
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import TypedDict

# ── Constantes de referência (NÃO usar em produção — consultar bd_BDI) ────────

PIS_PADRAO      = Decimal("0.0065")
COFINS_PADRAO   = Decimal("0.0300")
ISSQN_PR        = Decimal("0.0350")
ISSQN_SP        = Decimal("0.0500")
ICMS_PADRAO     = Decimal("0.1200")
ADM_PADRAO      = Decimal("0.1300")
CF_PADRAO       = Decimal("0.0150")

# PIS+COFINS acumulado no regime BDI+ICMS/FAT DIR SIMP (base de cálculo diferente)
PIS_COFINS_REGIME_CUMULATIVO = Decimal("0.0925")
PIS_COFINS_REGIME_NORMAL     = Decimal("0.0365")


# ── Helpers internos ──────────────────────────────────────────────────────────

def _q4(v: Decimal) -> Decimal:
    """Arredonda para 4 casas decimais (ROUND_HALF_UP)."""
    return v.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def _q6(v: Decimal) -> Decimal:
    """Arredonda para 6 casas decimais — precisão intermediária."""
    return v.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)


# ── API pública ───────────────────────────────────────────────────────────────

def calcular_bdi_sombra(
    custo_direto: Decimal,
    despesas_adm: Decimal,
    pis: Decimal,
    cofins: Decimal,
    issqn: Decimal,
    icms: Decimal = Decimal("0"),
) -> Decimal:
    """
    BDI Sombra — carga de recuperação tributária para blocos não faturáveis
    (Estrutura Operacional e Custos Excepcionais).

    Fórmula: custo_direto × (1 + ADM + PIS + COFINS + ISSQN [+ ICMS])

    Retorna o custo total "carregado" (não o percentual do BDI).
    """
    carga = despesas_adm + pis + cofins + issqn + icms
    return _q4(custo_direto * (Decimal("1") + carga))


def calcular_bdi_completo(
    despesas_adm: Decimal,
    custo_financeiro: Decimal,
    margem: Decimal,
    pis: Decimal,
    cofins: Decimal,
    issqn: Decimal,
    icms: Decimal = Decimal("0"),
) -> Decimal:
    """
    BDI completo para itens faturáveis (serviços e produtos).

    Fórmula: [(1+ADM)×(1+CF)×(1+M)] / [1-(PIS+COFINS+ISSQN[+ICMS])] - 1

    Retorna o BDI como fração decimal (ex: 0.3589 para 35.89%).

    Raises:
        ValueError: se (PIS+COFINS+ISSQN+ICMS) >= 1 (denominador ≤ 0).
    """
    numerador   = (Decimal("1") + despesas_adm) * (Decimal("1") + custo_financeiro) * (Decimal("1") + margem)
    impostos    = pis + cofins + issqn + icms
    denominador = Decimal("1") - impostos

    if denominador <= Decimal("0"):
        raise ValueError(
            f"Soma de impostos ({impostos}) >= 1: denominador inválido."
        )

    return _q6(numerador / denominador - Decimal("1"))


def aplicar_reidi(impostos: dict) -> dict:
    """
    Aplica o benefício REIDI: zera PIS e COFINS.

    Recebe e retorna dicionário com chaves: pis, cofins e quaisquer outras.
    Não modifica o dict original (retorna cópia).
    """
    resultado = dict(impostos)
    resultado["pis"]    = Decimal("0")
    resultado["cofins"] = Decimal("0")
    return resultado


def aplicar_mod_fat(mod_fat: str, impostos: dict) -> dict:
    """
    Aplica a máscara fiscal conforme a Modalidade de Faturamento (MOD FAT).

    Modalidades suportadas:
      BDI-MO        → icms = 0  (ISSQN ativo, sem ICMS)
      BDI-MAT+MO    → icms = 0  (ISSQN ativo, sem ICMS)
      BDI+ICMS      → issqn = 0 (ICMS ativo, sem ISSQN)
      FAT DIR SIMP  → todos os impostos = 0 (BDI = margem pura)

    Recebe e retorna dicionário (cópia). Não modifica o original.

    Raises:
        ValueError: MOD FAT desconhecida.
    """
    resultado = dict(impostos)

    if mod_fat in ("BDI-MO", "BDI-MAT+MO"):
        resultado["icms"] = Decimal("0")

    elif mod_fat == "BDI+ICMS":
        resultado["issqn"] = Decimal("0")

    elif mod_fat == "FAT DIR SIMP":
        resultado["pis"]    = Decimal("0")
        resultado["cofins"] = Decimal("0")
        resultado["issqn"]  = Decimal("0")
        resultado["icms"]   = Decimal("0")

    else:
        raise ValueError(
            f"MOD FAT desconhecida: '{mod_fat}'. "
            "Esperado: BDI-MO | BDI-MAT+MO | BDI+ICMS | FAT DIR SIMP"
        )

    return resultado


class ItemFaturavel(TypedDict):
    """Representa um item faturável para o cálculo do Fator K."""
    id: int | str
    custo_direto: Decimal
    preco_base_total: Decimal       # custo_direto × (1 + BDI) × quantidade


class ResultadoFatorK(TypedDict):
    id: int | str
    peso_percentual: Decimal        # participação % no subtotal faturável
    rateio: Decimal                 # R$ absorvido do bloco não faturável
    preco_final: Decimal            # preco_base_total + rateio


def calcular_fator_k(
    itens_faturaveis: list[ItemFaturavel],
    total_diluir_nao_faturavel: Decimal,
) -> list[ResultadoFatorK]:
    """
    Distribui `total_diluir_nao_faturavel` proporcionalmente ao peso
    de cada item faturável no subtotal faturável (Fator K Top-Down).

    O Fator K (k) = total_não_faturável / subtotal_faturável.

    Retorna lista com peso_percentual, rateio e preco_final por item.
    Lista vazia ou subtotal_faturável = 0 retorna itens sem rateio.
    """
    subtotal_faturavel = sum(
        (i["preco_base_total"] for i in itens_faturaveis),
        Decimal("0"),
    )

    resultado: list[ResultadoFatorK] = []

    if subtotal_faturavel == Decimal("0") or not itens_faturaveis:
        for item in itens_faturaveis:
            resultado.append(ResultadoFatorK(
                id=item["id"],
                peso_percentual=Decimal("0"),
                rateio=Decimal("0"),
                preco_final=item["preco_base_total"],
            ))
        return resultado

    total_proposta = subtotal_faturavel + total_diluir_nao_faturavel

    for item in itens_faturaveis:
        peso = _q6(item["preco_base_total"] / subtotal_faturavel)
        if total_diluir_nao_faturavel == Decimal("0"):
            preco_final = item["preco_base_total"]
            rateio = Decimal("0")
        else:
            preco_final = _q4(peso * total_proposta)
            rateio = max(_q4(preco_final - item["preco_base_total"]), Decimal("0"))
        resultado.append(ResultadoFatorK(
            id=item["id"],
            peso_percentual=_q4(peso * Decimal("100")),
            rateio=rateio,
            preco_final=preco_final,
        ))

    return resultado


def margem_liquida_real(
    itens_faturaveis: list[dict],
    total_proposta: Decimal,
) -> Decimal:
    """
    Calcula a Margem Líquida Real sobre o total da proposta.

    Para cada item faturável, o lucro absoluto é:
        lucro = custo_direto_total × (1 + ADM) × (1 + CF) × margem

    onde custo_direto_total = custo_direto_unitario × quantidade.

    Cada item deve ter: custo_direto (Decimal), quantidade (Decimal),
    margem (Decimal, fração ex: 0.10), despesas_adm (Decimal), custo_financeiro (Decimal).

    Retorna a margem líquida real como fração decimal (ex: 0.0842 para 8.42%).
    Retorna 0 se total_proposta = 0.
    """
    if total_proposta == Decimal("0"):
        return Decimal("0")

    lucro_total = sum(
        (
            item["custo_direto"] * item["quantidade"]
            * (Decimal("1") + item["despesas_adm"])
            * (Decimal("1") + item["custo_financeiro"])
            * item["margem"]
        )
        for item in itens_faturaveis
    )

    return _q6(lucro_total / total_proposta)
