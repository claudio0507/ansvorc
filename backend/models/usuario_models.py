from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base

PAPEIS_VALIDOS = ("gestor_bd", "parametrizador", "orcamentista", "sponsor")


class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = (
        CheckConstraint(
            "papel IN ('gestor_bd','parametrizador','orcamentista','sponsor')",
            name="ck_usuarios_papel",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(
        String(200), unique=True, nullable=False, index=True
    )
    senha_hash: Mapped[str] = mapped_column(String(300), nullable=False)
    papel: Mapped[str] = mapped_column(
        String(30), nullable=False, default="orcamentista"
    )
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
