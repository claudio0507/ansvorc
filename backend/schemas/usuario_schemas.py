import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from backend.models.usuario_models import PAPEIS_VALIDOS

_RE_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class UsuarioCreate(BaseModel):
    nome: str
    email: str
    senha: str
    # papel não aceito no auto-registro — sempre nasce como orcamentista

    @field_validator("email")
    @classmethod
    def valida_email(cls, v: str) -> str:
        if not _RE_EMAIL.match(v):
            raise ValueError("E-mail inválido.")
        return v.lower().strip()

    @field_validator("senha")
    @classmethod
    def valida_senha(cls, v: str) -> str:
        if len(v) < 10:
            raise ValueError("Senha deve ter no mínimo 10 caracteres.")
        if not re.search(r"[A-Z]", v) or not re.search(r"[0-9]", v):
            raise ValueError("Senha deve conter letras maiúsculas e números.")
        return v


class UsuarioAdminCreate(BaseModel):
    """Schema exclusivo para criação de usuários por administradores (com papel)."""

    nome: str
    email: str
    senha: str
    papel: str = "orcamentista"

    @field_validator("email")
    @classmethod
    def valida_email(cls, v: str) -> str:
        if not _RE_EMAIL.match(v):
            raise ValueError("E-mail inválido.")
        return v.lower().strip()

    @field_validator("papel")
    @classmethod
    def valida_papel(cls, v: str) -> str:
        if v not in PAPEIS_VALIDOS:
            raise ValueError(f"Papel inválido. Opções: {PAPEIS_VALIDOS}")
        return v

    @field_validator("senha")
    @classmethod
    def valida_senha(cls, v: str) -> str:
        if len(v) < 10:
            raise ValueError("Senha deve ter no mínimo 10 caracteres.")
        if not re.search(r"[A-Z]", v) or not re.search(r"[0-9]", v):
            raise ValueError("Senha deve conter letras maiúsculas e números.")
        return v


class UsuarioRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    email: str
    papel: str
    ativo: bool
    criado_em: datetime


class UsuarioLogin(BaseModel):
    email: str
    senha: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    papel: str
    usuario_id: int
    nome: str
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class PapelUpdate(BaseModel):
    papel: str

    @field_validator("papel")
    @classmethod
    def valida_papel(cls, v: str) -> str:
        if v not in PAPEIS_VALIDOS:
            raise ValueError(f"Papel inválido. Opções: {PAPEIS_VALIDOS}")
        return v
