"""
seeds_prod.py — Seed de produção com senhas fortes.

Uso:
    python -m backend.seeds_prod

Respeita variáveis de ambiente:
    ADMIN_EMAIL     (default: admin@altanoroeste.com.br)
    ADMIN_PASSWORD  (obrigatória em produção)
    PARAM_EMAIL     (default: param@altanoroeste.com.br)
    PARAM_PASSWORD  (obrigatória em produção)
    ORC_EMAIL       (default: orc@altanoroeste.com.br)
    ORC_PASSWORD    (obrigatória em produção)
"""

import os
import secrets
import sys

from backend.auth import hash_senha
from backend.database import Base, SessionLocal, engine
from backend.models.bd_models import BdBDI
from backend.models.usuario_models import Usuario
from backend.seeds import (
    seed_bdi,
    seed_despesas,
    seed_epi,
    seed_estrutura,
    seed_ferramental,
    seed_frotas,
    seed_materiais,
    seed_rh,
)


def _senha_ou_gerada(env_var: str, label: str) -> str:
    val = os.getenv(env_var, "")
    if val:
        return val
    gerada = secrets.token_urlsafe(16)
    # Avisa sem expor a senha no stdout — senha escrita apenas no arquivo de credenciais
    print(f"[seeds_prod] AVISO: {env_var} não definida. Senha gerada para {label}.")
    return gerada


def _salvar_credenciais(credenciais: dict[str, str]) -> None:
    """Grava credenciais geradas em arquivo restrito (chmod 600) fora do stdout."""
    cred_path = os.path.join(os.path.dirname(__file__), "..", "credenciais_iniciais.txt")
    cred_path = os.path.abspath(cred_path)
    with open(cred_path, "w", encoding="utf-8") as f:
        f.write("Credenciais iniciais — altere imediatamente após o primeiro login.\n\n")
        for email, senha in credenciais.items():
            f.write(f"{email}  →  {senha}\n")
    # Restringe leitura ao dono do processo (equivalente a chmod 600)
    try:
        import stat

        os.chmod(cred_path, stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass  # Windows não suporta chmod POSIX; aceita como está
    print(f"[seeds_prod] Credenciais gravadas em: {cred_path}")
    print("[seeds_prod] IMPORTANTE: altere as senhas e remova o arquivo após o primeiro login.")


def seed_usuarios_prod(db):
    admin_email = os.getenv("ADMIN_EMAIL", "admin@altanoroeste.com.br")
    param_email = os.getenv("PARAM_EMAIL", "param@altanoroeste.com.br")
    orc_email = os.getenv("ORC_EMAIL", "orc@altanoroeste.com.br")

    admin_pw = _senha_ou_gerada("ADMIN_PASSWORD", admin_email)
    param_pw = _senha_ou_gerada("PARAM_PASSWORD", param_email)
    orc_pw = _senha_ou_gerada("ORC_PASSWORD", orc_email)

    usuarios = [
        Usuario(
            nome="Administrador",
            email=admin_email,
            senha_hash=hash_senha(admin_pw),
            papel="gestor_bd",
        ),
        Usuario(
            nome="Parametrizador",
            email=param_email,
            senha_hash=hash_senha(param_pw),
            papel="parametrizador",
        ),
        Usuario(
            nome="Orçamentista",
            email=orc_email,
            senha_hash=hash_senha(orc_pw),
            papel="orcamentista",
        ),
    ]
    db.add_all(usuarios)
    return {admin_email: admin_pw, param_email: param_pw, orc_email: orc_pw}


def run():
    # Importa todos os modelos para garantir que create_all os enxerga
    from backend.models import bd_models, orcamento_models, usuario_models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(BdBDI).count() > 0:
            print("[seeds_prod] Seed já executado anteriormente. Abortando.")
            return

        seed_bdi(db)
        seed_rh(db)
        seed_epi(db)
        seed_ferramental(db)
        seed_frotas(db)
        seed_materiais(db)
        seed_estrutura(db)
        seed_despesas(db)
        credenciais = seed_usuarios_prod(db)

        db.commit()
        print("[seeds_prod] Seed de produção concluído.")
        _salvar_credenciais(credenciais)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
