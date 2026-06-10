"""Validators reutilizáveis de padronização de texto (docs/05 §UI rules + prompt 3.3).

- Texto livre (nome/descrição): trim + primeira letra maiúscula.
- Código: trim + uppercase + apenas [A-Z0-9-].
"""

import re

_CODIGO_RE = re.compile(r"[^A-Z0-9-]")


def normalizar_texto(v: str | None) -> str | None:
    """Trim + capitaliza a primeira letra (preserva o restante)."""
    if v is None:
        return None
    v = v.strip()
    if not v:
        return v
    return v[0].upper() + v[1:]


def normalizar_codigo(v: str | None) -> str | None:
    """Trim + uppercase + remove tudo que não for A-Z, 0-9 ou hífen."""
    if v is None:
        return None
    v = v.strip().upper()
    return _CODIGO_RE.sub("", v)


def normalizar_seguimento(v: str | None) -> str | None:
    """Seguimento sempre em uppercase (EPS, HORIZONTAL, VERTICAL, APOIO…)."""
    if v is None:
        return None
    return v.strip().upper()


def normalizar_uf(v: str | None) -> str | None:
    """UF sempre 2 letras uppercase."""
    if v is None:
        return None
    return v.strip().upper()
