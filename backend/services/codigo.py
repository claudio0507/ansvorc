"""Geração de código automático sequencial por tipo (BLOCO 3.1, escopo docs/02).

Aplica-se a entidades que o schema canônico prevê com código: fichas, produtos,
componentes e orçamento. BDs simples NÃO usam código (decisão: docs/02 vence).

Formato: PREFIXO + "-" + sequencial 4 dígitos (ex: CMP-0001, PRD-0002).
Orçamento usa ano: ORC-2026-0001.
"""

import re
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session


def gerar_codigo(db: Session, modelo, prefixo: str, *, com_ano: bool = False) -> str:
    """Próximo código sequencial p/ o modelo, baseado no maior sequencial existente.

    Lê todos os códigos com o prefixo e incrementa o maior sufixo numérico.
    """
    base = prefixo
    if com_ano:
        ano = datetime.now(timezone.utc).year
        base = f"{prefixo}-{ano}"

    like = f"{base}-%"
    codigos = db.query(modelo.codigo).filter(modelo.codigo.like(like)).all()
    maior = 0
    pat = re.compile(rf"^{re.escape(base)}-(\d+)$")
    for (c,) in codigos:
        m = pat.match(c or "")
        if m:
            maior = max(maior, int(m.group(1)))
    return f"{base}-{maior + 1:04d}"
