"""FOR-077 — resolução de fallback dos campos da proposta.

Precedência por campo: valor do Orçamento → padrão do ConfigSistema → literal.
Lógica pura (sem DB) para ser reusada por F2 (editor) e F3 (documento/PDF).
"""

from decimal import Decimal


def montar_proposta(orc, config) -> dict:
    """Resolve cada campo da proposta com fallback do ConfigSistema + defaults literais.

    `orc` e `config` são objetos com os atributos lidos abaixo (models ou stubs).
    """

    def fb(valor, padrao, literal=""):
        if valor not in (None, ""):
            return valor
        if padrao not in (None, ""):
            return padrao
        return literal

    def fb_num(valor, padrao, literal):
        # Para campos numéricos: 0 é um valor válido (ex.: 0% de retenção),
        # então usamos `is not None` em vez de `or` em ambos os níveis.
        if valor is not None:
            return valor
        if padrao is not None:
            return padrao
        return literal

    return {
        "texto_topo_proposta": fb(orc.texto_topo_proposta, config.declaracoes_padrao),
        "clausula_tributaria": fb(
            orc.clausula_tributaria, config.clausula_tributaria_padrao
        ),
        "reajustamento": fb(orc.reajustamento, config.reajustamento_padrao),
        "garantia_retencao_pct": fb_num(
            orc.garantia_retencao_pct,
            config.garantia_retencao_padrao_pct,
            Decimal("5"),
        ),
        "garantia_devolucao_dias": fb_num(
            orc.garantia_devolucao_dias,
            config.garantia_devolucao_padrao_dias,
            60,
        ),
        "faturamento_direto": fb(orc.faturamento_direto, None, "Não aplicável."),
        "entrega_as_built": fb(orc.entrega_as_built, None, "Não aplicável."),
        "modalidade": fb(orc.modalidade, None, "Preço Unitário"),
    }
