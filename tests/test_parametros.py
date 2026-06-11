"""Testes de parametrização — unidades_medida, seguimentos, tipos de estrutura (BLOCO 3)."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base, get_db
from backend.main import app

engine_test = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)


@pytest.fixture()
def client(setup_db, sponsor_headers):
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, headers=sponsor_headers) as c:
        yield c
    app.dependency_overrides.clear()


class TestUnidades:
    BASE = "/api/v1/unidades-medida"

    def test_crud_unidade(self, client):
        r = client.post(self.BASE, json={"sigla": "m²", "nome": "metro quadrado"})
        assert r.status_code == 201
        assert r.json()["nome"] == "Metro quadrado"  # capitalizado
        uid = r.json()["id"]
        assert len(client.get(self.BASE).json()) == 1
        assert client.put(f"{self.BASE}/{uid}", json={"nome": "M2"}).status_code == 200
        assert client.delete(f"{self.BASE}/{uid}").status_code == 204

    def test_sigla_unica(self, client):
        client.post(self.BASE, json={"sigla": "kg", "nome": "Quilo"})
        r = client.post(self.BASE, json={"sigla": "kg", "nome": "Outro"})
        assert r.status_code == 409


class TestSeguimentos:
    BASE = "/api/v1/parametros/seguimentos"

    def test_crud_e_uppercase(self, client):
        r = client.post(self.BASE, json={"nome": "eps"})
        assert r.status_code == 201
        assert r.json()["nome"] == "EPS"
        assert client.post(self.BASE, json={"nome": "EPS"}).status_code == 409


class TestTiposEstrutura:
    BASE = "/api/v1/parametros/tipos-estrutura"

    def test_crud(self, client):
        r = client.post(self.BASE, json={"nome": "Base_de_Apoio"})
        assert r.status_code == 201
        assert r.json()["nome"] == "Base_de_Apoio"
        assert len(client.get(self.BASE).json()) == 1
