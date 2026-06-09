"""
conftest.py — fixtures compartilhados entre todas as suites de teste.

Fornece `auth_token` (papel sponsor, acesso total) para os testes que
precisam de autenticação após a Fase 3.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.auth import criar_token, hash_senha
from backend.database import Base, get_db
from backend.main import app
from backend.models.usuario_models import Usuario


def _make_engine():
    return create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


@pytest.fixture(scope="session")
def sponsor_token():
    """Token JWT de um usuário sponsor para usar nos testes de integração."""
    return criar_token(usuario_id=9999, papel="sponsor")


@pytest.fixture(scope="session")
def sponsor_headers(sponsor_token):
    return {"Authorization": f"Bearer {sponsor_token}"}
