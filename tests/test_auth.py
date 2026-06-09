"""
Testes Fase 3 — Autenticação JWT + RBAC

Cobre:
  - Registro de usuário (sempre nasce como orcamentista)
  - Criação de usuário admin com papel arbitrário
  - Login correto → access_token + refresh_token
  - Login com senha errada → 401
  - Token inválido → 401
  - Token expirado → 401
  - GET /auth/me com token válido
  - POST /auth/refresh → novo access_token
  - RBAC: orcamentista tentando /bd-rh → 403
  - RBAC: gestor_bd acessando /bd-rh → 200
  - RBAC: parametrizador acessando /fichas-equipe → 200
  - Rota protegida sem token → 401
  - Registro com e-mail duplicado → 409
  - Registro com senha curta/fraca → 422
  - Registro com papel no body → papel ignorado (nasce orcamentista)
"""

from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.config import settings
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

# Senhas fortes para atender à nova política (≥10 chars, maiúscula + número)
_SENHA_FORTE = "Sinalys2024!"

_ADMIN_REG = {
    "nome": "Admin",
    "email": "admin@test.com",
    "senha": _SENHA_FORTE,
    "papel": "gestor_bd",
}
_ORC_REG = {
    "nome": "Orc",
    "email": "orc@test.com",
    "senha": _SENHA_FORTE,
    "papel": "orcamentista",
}
_PARAM_REG = {
    "nome": "Param",
    "email": "param@test.com",
    "senha": _SENHA_FORTE,
    "papel": "parametrizador",
}


def _criar_usuario_admin(payload: dict, token_admin: str) -> dict:
    """Cria usuário com papel arbitrário via endpoint admin."""
    r = client.post(
        "/api/v1/auth/usuarios",
        json=payload,
        headers={"Authorization": f"Bearer {token_admin}"},
    )
    assert r.status_code == 201, r.text
    return r.json()


def _bootstrap_admin() -> str:
    """Cria um admin diretamente no banco (seed) e faz login, retornando token."""
    from backend.auth import hash_senha
    from backend.models.usuario_models import Usuario

    db = TestingSession()
    try:
        admin = Usuario(
            nome="Admin Bootstrap",
            email="bootstrap@test.com",
            senha_hash=hash_senha(_SENHA_FORTE),
            papel="gestor_bd",
            ativo=True,
        )
        db.add(admin)
        db.commit()
    finally:
        db.close()

    r = client.post(
        "/api/v1/auth/login",
        json={"email": "bootstrap@test.com", "senha": _SENHA_FORTE},
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


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
    def test_registro_sempre_nasce_orcamentista(self):
        """Qualquer papel enviado no body é ignorado — usuário nasce como orcamentista."""
        payload = {**_ADMIN_REG, "email": "novo@test.com"}
        r = client.post("/api/v1/auth/registro", json=payload)
        assert r.status_code == 201
        assert r.json()["papel"] == "orcamentista"

    def test_registro_sem_papel_no_body(self):
        payload = {"nome": "Fulano", "email": "fulano@test.com", "senha": _SENHA_FORTE}
        r = client.post("/api/v1/auth/registro", json=payload)
        assert r.status_code == 201
        assert r.json()["papel"] == "orcamentista"

    def test_registro_email_duplicado(self):
        payload = {"nome": "A", "email": "dup@test.com", "senha": _SENHA_FORTE}
        client.post("/api/v1/auth/registro", json=payload)
        r = client.post("/api/v1/auth/registro", json=payload)
        assert r.status_code == 409

    def test_registro_senha_curta_422(self):
        payload = {"nome": "A", "email": "x@x.com", "senha": "abc"}
        r = client.post("/api/v1/auth/registro", json=payload)
        assert r.status_code == 422

    def test_registro_senha_sem_maiuscula_422(self):
        payload = {"nome": "A", "email": "x@x.com", "senha": "sinalys2024"}
        r = client.post("/api/v1/auth/registro", json=payload)
        assert r.status_code == 422

    def test_registro_senha_sem_numero_422(self):
        payload = {"nome": "A", "email": "x@x.com", "senha": "SinalysForte"}
        r = client.post("/api/v1/auth/registro", json=payload)
        assert r.status_code == 422

    def test_registro_email_invalido(self):
        payload = {"nome": "A", "email": "nao-e-email", "senha": _SENHA_FORTE}
        r = client.post("/api/v1/auth/registro", json=payload)
        assert r.status_code == 422


# ══════════════════════════════════════════════════════════════════════════════
#   CRIAÇÃO DE USUÁRIO ADMIN
# ══════════════════════════════════════════════════════════════════════════════


class TestCriarUsuarioAdmin:
    def test_admin_pode_criar_com_papel_arbitrario(self):
        token_admin = _bootstrap_admin()
        usuario = _criar_usuario_admin(_ADMIN_REG, token_admin)
        assert usuario["papel"] == "gestor_bd"

    def test_orcamentista_nao_pode_criar_usuario_admin(self):
        payload = {"nome": "A", "email": "a@test.com", "senha": _SENHA_FORTE}
        client.post("/api/v1/auth/registro", json=payload)
        token_orc = logar("a@test.com", _SENHA_FORTE)
        r = client.post(
            "/api/v1/auth/usuarios",
            json=_ADMIN_REG,
            headers=headers(token_orc),
        )
        assert r.status_code == 403

    def test_admin_pode_promover_papel(self):
        token_admin = _bootstrap_admin()
        payload = {"nome": "B", "email": "b@test.com", "senha": _SENHA_FORTE}
        r = client.post("/api/v1/auth/registro", json=payload)
        uid = r.json()["id"]
        r2 = client.patch(
            f"/api/v1/auth/usuarios/{uid}/papel",
            json={"papel": "parametrizador"},
            headers=headers(token_admin),
        )
        assert r2.status_code == 200
        assert r2.json()["papel"] == "parametrizador"


# ══════════════════════════════════════════════════════════════════════════════
#   LOGIN
# ══════════════════════════════════════════════════════════════════════════════


class TestLogin:
    def test_login_retorna_access_e_refresh_token(self):
        client.post(
            "/api/v1/auth/registro",
            json={"nome": "A", "email": "a@test.com", "senha": _SENHA_FORTE},
        )
        r = client.post(
            "/api/v1/auth/login",
            json={"email": "a@test.com", "senha": _SENHA_FORTE},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 20
        assert len(data["refresh_token"]) > 20
        assert data["expires_in"] == 900  # 15 min * 60

    def test_login_senha_errada_401(self):
        client.post(
            "/api/v1/auth/registro",
            json={"nome": "A", "email": "a@test.com", "senha": _SENHA_FORTE},
        )
        r = client.post(
            "/api/v1/auth/login",
            json={"email": "a@test.com", "senha": "errada"},
        )
        assert r.status_code == 401

    def test_login_email_inexistente_401(self):
        r = client.post(
            "/api/v1/auth/login",
            json={"email": "ninguem@x.com", "senha": "qualquer"},
        )
        assert r.status_code == 401


# ══════════════════════════════════════════════════════════════════════════════
#   AUTENTICAÇÃO DE ROTA
# ══════════════════════════════════════════════════════════════════════════════


class TestAutenticacao:
    def test_sem_token_retorna_401(self):
        r = client.get("/api/v1/bd-rh")
        assert r.status_code == 401

    def test_token_invalido_retorna_401(self):
        r = client.get(
            "/api/v1/bd-rh", headers={"Authorization": "Bearer token.lixo.aqui"}
        )
        assert r.status_code == 401

    def test_token_expirado_retorna_401(self):
        payload = {
            "sub": "1",
            "papel": "gestor_bd",
            "type": "access",
            "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
        }
        token_expirado = jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
        r = client.get(
            "/api/v1/bd-rh", headers={"Authorization": f"Bearer {token_expirado}"}
        )
        assert r.status_code == 401

    def test_refresh_token_nao_serve_como_access(self):
        """Refresh token rejeitado em rotas que exigem access token."""
        client.post(
            "/api/v1/auth/registro",
            json={"nome": "A", "email": "a@test.com", "senha": _SENHA_FORTE},
        )
        r = client.post(
            "/api/v1/auth/login",
            json={"email": "a@test.com", "senha": _SENHA_FORTE},
        )
        refresh = r.json()["refresh_token"]
        r2 = client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {refresh}"}
        )
        assert r2.status_code == 401

    def test_refresh_gera_novo_access_token(self):
        client.post(
            "/api/v1/auth/registro",
            json={"nome": "A", "email": "a@test.com", "senha": _SENHA_FORTE},
        )
        r = client.post(
            "/api/v1/auth/login",
            json={"email": "a@test.com", "senha": _SENHA_FORTE},
        )
        refresh = r.json()["refresh_token"]
        r2 = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
        assert r2.status_code == 200
        assert len(r2.json()["access_token"]) > 20

    def test_me_com_token_valido(self):
        token_admin = _bootstrap_admin()
        r = client.get("/api/v1/auth/me", headers=headers(token_admin))
        assert r.status_code == 200
        assert r.json()["email"] == "bootstrap@test.com"

    def test_rota_saude_publica(self):
        r = client.get("/")
        assert r.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
#   RBAC
# ══════════════════════════════════════════════════════════════════════════════


class TestRBAC:
    def _token_com_papel(self, papel: str, email: str) -> str:
        token_admin = _bootstrap_admin()
        _criar_usuario_admin(
            {"nome": "U", "email": email, "senha": _SENHA_FORTE, "papel": papel},
            token_admin,
        )
        return logar(email, _SENHA_FORTE)

    def test_orcamentista_nao_acessa_bd_rh(self):
        token = self._token_com_papel("orcamentista", "orc@test.com")
        r = client.get("/api/v1/bd-rh", headers=headers(token))
        assert r.status_code == 403

    def test_gestor_bd_acessa_bd_rh(self):
        token = self._token_com_papel("gestor_bd", "admin@test.com")
        r = client.get("/api/v1/bd-rh", headers=headers(token))
        assert r.status_code == 200

    def test_parametrizador_acessa_fichas_equipe(self):
        token = self._token_com_papel("parametrizador", "param@test.com")
        r = client.get("/api/v1/fichas-equipe", headers=headers(token))
        assert r.status_code == 200

    def test_orcamentista_nao_acessa_fichas(self):
        token = self._token_com_papel("orcamentista", "orc@test.com")
        r = client.get("/api/v1/fichas-equipe", headers=headers(token))
        assert r.status_code == 403

    def test_orcamentista_acessa_orcamentos(self):
        token = self._token_com_papel("orcamentista", "orc@test.com")
        r = client.get("/api/v1/orcamentos", headers=headers(token))
        assert r.status_code == 200

    def test_gestor_bd_nao_acessa_fichas(self):
        token = self._token_com_papel("gestor_bd", "admin@test.com")
        r = client.get("/api/v1/fichas-equipe", headers=headers(token))
        assert r.status_code == 403

    def test_gestor_bd_nao_acessa_orcamentos(self):
        token = self._token_com_papel("gestor_bd", "admin@test.com")
        r = client.get("/api/v1/orcamentos", headers=headers(token))
        assert r.status_code == 403
