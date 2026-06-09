"""
Funções de autenticação: bcrypt + JWT (PyJWT).

Token payload: {"sub": str(usuario_id), "papel": papel, "exp": timestamp}
"""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import get_db
from backend.models.usuario_models import Usuario

# ── Hashing de senha (bcrypt direto, sem passlib) ─────────────────────────────


def hash_senha(senha: str) -> str:
    return bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()


def verificar_senha(senha: str, hash_: str) -> bool:
    return bcrypt.checkpw(senha.encode(), hash_.encode())


# ── JWT ───────────────────────────────────────────────────────────────────────

_ALGORITMO = "HS256"
_EXPIRACAO_HORAS = 24


def criar_token(usuario_id: int, papel: str) -> str:
    payload = {
        "sub": str(usuario_id),
        "papel": papel,
        "exp": datetime.now(timezone.utc) + timedelta(hours=_EXPIRACAO_HORAS),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=_ALGORITMO)


def verificar_token(token: str) -> dict:
    """Retorna o payload decodificado ou levanta HTTPException 401."""
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[_ALGORITMO])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido.",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── Dependency: usuário autenticado ──────────────────────────────────────────

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> Usuario:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais não fornecidas.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verificar_token(credentials.credentials)
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: campo 'sub' ausente.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    usuario_id = int(sub)

    usuario = db.get(Usuario, usuario_id)
    if not usuario or not usuario.ativo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado ou inativo.",
        )
    return usuario


# ── Factories de Depends por papel ───────────────────────────────────────────


def requer_papel(*papeis: str):
    """
    Retorna uma dependência FastAPI que verifica se o usuário tem um dos papéis.

    Uso:
        @router.get("/...", dependencies=[Depends(requer_papel("gestor_bd"))])
    ou como parâmetro:
        def endpoint(u: Usuario = Depends(requer_papel("gestor_bd", "sponsor"))):
    """

    def _dep(usuario: Usuario = Depends(get_current_user)) -> Usuario:
        if usuario.papel not in papeis:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso negado. Requer papel: {papeis}.",
            )
        return usuario

    return _dep
