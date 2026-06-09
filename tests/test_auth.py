"""
Testes Fase 3 — Autenticação JWT + RBAC

Cobre:
  - Registro de usuário
  - Login correto → token
  - Login com senha errada → 401
  - Token inválido → 401
  - Token expirado → 401
  - get /auth/me com token válido
  - RBAC: orcamentista tentando /bd-rh → 403
  - RBAC: gestor_bd acessando /bd-rh → 200
  - RBAC: parametrizador acessando /fichas-equipe → 200
  - Rota protegida sem token → 401
  - Registro com e-mail duplicado → 409
  - Registro com senha curta → 422
  - Papel inválido no registro → 422
"""

from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base, get_db
from backend.main import app

# ── DB de teste em memória ────────────────────────────────────────────────────

engine_test = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)
    app.dependency_overrides.pop(get_db, None)


client = TestClient(app, raise_server_exceptions=False)

# ── helpers ───────────────────────────────────────────────────────────────────

_ADMIN = {"nome": "Admin", "email": "admin@test.com", "senha": "admin123", "papel": "gestor_bd"}
_ORC   = {"nome": "Orc",   "email": "orc@test.com",   "senha": "orc123",   "papel": "orcamentista"}
_PARAM = {"nome": "Param", "email": "param@test.com", "senha": "param123", "papel": "parametrizador"}


def registrar(payload: dict) -> dict:
    r = client.post("/api/v1/auth/registro", json=payload)
    assert r.status_code == 201, r.text
    return r.json()


def logar(email: str, senha: str) -> str:
    r = client.post("/api/v1/auth/login", json={"email": email, "senha": senha})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ══════════════════════════════════════════════════════════════════════════════
#   REGISTRO
# ══════════════════════════════════════════════════════════════════════════════

class TestRegistro:
    def test_registro_ok(self):
        r = client.post("/api/v1/auth/registro", json=_ADMIN)
        assert r.status_code == 201
        data = r.json()
        assert data["email"] == _ADMIN["email"]
        assert data["papel"] == "gestor_bd"
        assert "senha_hash" not in data

    def test_registro_email_duplicado(self):
        registrar(_ADMIN)
        r = client.post("/api/v1/auth/registro", json=_ADMIN)
        assert r.status_code == 409

    def test_registro_senha_curta(self):
        payload = {**_ADMIN, "email": "x@x.com", "senha": "123"}
        r = client.post("/api/v1/auth/registro", json=payload)
        assert r.status_code == 422

    def test_registro_papel_invalido(self):
        payload = {**_ADMIN, "email": "y@y.com", "papel": "hacker"}
        r = client.post("/api/v1/auth/registro", json=payload)
        assert r.status_code == 422

    def test_registro_email_invalido(self):
        payload = {**_ADMIN, "email": "nao-e-email"}
        r = client.post("/api/v1/auth/registro", json=payload)
        assert r.status_code == 422


# ══════════════════════════════════════════════════════════════════════════════
#   LOGIN
# ══════════════════════════════════════════════════════════════════════════════

class TestLogin:
    def test_login_ok_retorna_token_e_papel(self):
        registrar(_ADMIN)
        r = client.post("/api/v1/auth/login", json={"email": _ADMIN["email"], "senha": _ADMIN["senha"]})
        assert r.status_code == 200
        data = r.json()
        assert data["token_type"] == "bearer"
        assert data["papel"] == "gestor_bd"
        assert len(data["access_token"]) > 20

    def test_login_senha_errada_401(self):
        registrar(_ADMIN)
        r = client.post("/api/v1/auth/login", json={"email": _ADMIN["email"], "senha": "errada"})
        assert r.status_code == 401

    def test_login_email_inexistente_401(self):
        r = client.post("/api/v1/auth/login", json={"email": "ninguem@x.com", "senha": "qualquer"})
        assert r.status_code == 401


# ══════════════════════════════════════════════════════════════════════════════
#   AUTENTICAÇÃO DE ROTA
# ══════════════════════════════════════════════════════════════════════════════

class TestAutenticacao:
    def test_sem_token_retorna_401(self):
        r = client.get("/api/v1/bd-rh")
        assert r.status_code == 401

    def test_token_invalido_retorna_401(self):
        r = client.get("/api/v1/bd-rh", headers={"Authorization": "Bearer token.lixo.aqui"})
        assert r.status_code == 401

    def test_token_expirado_retorna_401(self):
        from backend.config import settings
        payload = {
            "sub":   "1",
            "papel": "gestor_bd",
            "exp":   datetime.now(timezone.utc) - timedelta(seconds=1),
        }
        token_expirado = jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
        r = client.get("/api/v1/bd-rh", headers={"Authorization": f"Bearer {token_expirado}"})
        assert r.status_code == 401

    def test_me_com_token_valido(self):
        registrar(_ADMIN)
        token = logar(_ADMIN["email"], _ADMIN["senha"])
        r = client.get("/api/v1/auth/me", headers=headers(token))
        assert r.status_code == 200
        assert r.json()["email"] == _ADMIN["email"]

    def test_rota_saude_publica(self):
        r = client.get("/")
        assert r.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
#   RBAC
# ══════════════════════════════════════════════════════════════════════════════

class TestRBAC:
    def test_orcamentista_nao_acessa_bd_rh(self):
        registrar(_ORC)
        token = logar(_ORC["email"], _ORC["senha"])
        r = client.get("/api/v1/bd-rh", headers=headers(token))
        assert r.status_code == 403

    def test_gestor_bd_acessa_bd_rh(self):
        registrar(_ADMIN)
        token = logar(_ADMIN["email"], _ADMIN["senha"])
        r = client.get("/api/v1/bd-rh", headers=headers(token))
        assert r.status_code == 200

    def test_parametrizador_acessa_fichas_equipe(self):
        registrar(_PARAM)
        token = logar(_PARAM["email"], _PARAM["senha"])
        r = client.get("/api/v1/fichas-equipe", headers=headers(token))
        assert r.status_code == 200

    def test_orcamentista_nao_acessa_fichas(self):
        registrar(_ORC)
        token = logar(_ORC["email"], _ORC["senha"])
        r = client.get("/api/v1/fichas-equipe", headers=headers(token))
        assert r.status_code == 403

    def test_orcamentista_acessa_orcamentos(self):
        registrar(_ORC)
        token = logar(_ORC["email"], _ORC["senha"])
        r = client.get("/api/v1/orcamentos", headers=headers(token))
        assert r.status_code == 200

    def test_gestor_bd_nao_acessa_fichas(self):
        registrar(_ADMIN)
        token = logar(_ADMIN["email"], _ADMIN["senha"])
        r = client.get("/api/v1/fichas-equipe", headers=headers(token))
        assert r.status_code == 403

    def test_gestor_bd_nao_acessa_orcamentos(self):
        registrar(_ADMIN)
        token = logar(_ADMIN["email"], _ADMIN["senha"])
        r = client.get("/api/v1/orcamentos", headers=headers(token))
        assert r.status_code == 403
