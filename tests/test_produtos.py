"""Testes de Produtos, Componentes e atribuição de fichas (BLOCO 4)."""

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


class TestComponentes:
    BASE = "/api/v1/componentes"

    def test_codigo_auto_sequencial(self, client):
        a = client.post(self.BASE, json={"nome": "chapa base"})
        b = client.post(self.BASE, json={"nome": "outra"})
        assert a.json()["codigo"] == "CMP-0001"
        assert b.json()["codigo"] == "CMP-0002"
        assert a.json()["possui_ficha_tecnica"] is False
        assert a.json()["nome"] == "Chapa base"  # capitalizado

    def test_crud(self, client):
        id_ = client.post(self.BASE, json={"nome": "x"}).json()["id"]
        assert client.get(f"{self.BASE}/{id_}").status_code == 200
        assert (
            client.put(f"{self.BASE}/{id_}", json={"setor": "Fábrica"}).json()["setor"]
            == "Fábrica"
        )
        assert client.delete(f"{self.BASE}/{id_}").status_code == 204


class TestProdutos:
    BASE = "/api/v1/produtos"

    def test_codigo_auto(self, client):
        r = client.post(self.BASE, json={"nome": "placa r1"})
        assert r.json()["codigo"] == "PRD-0001"


class TestAtribuicaoFicha:
    def test_atribuir_marca_flag(self, client):
        comp = client.post("/api/v1/componentes", json={"nome": "c"}).json()
        fs = client.post(
            "/api/v1/fichas-servico",
            json={
                "codigo": "sv1",
                "nome": "x",
                "seguimento": "EPS",
                "produtividade_dia": "10",
                "unidade": "m²",
            },
        ).json()
        r = client.post(
            "/api/v1/item-fichas",
            json={"componente_id": comp["id"], "ficha_servico_id": fs["id"]},
        )
        assert r.status_code == 201
        atual = client.get(f"/api/v1/componentes/{comp['id']}").json()
        assert atual["possui_ficha_tecnica"] is True

    def test_sem_item_rejeitado(self, client):
        fs = client.post(
            "/api/v1/fichas-servico",
            json={
                "codigo": "sv2",
                "nome": "x",
                "seguimento": "EPS",
                "produtividade_dia": "10",
                "unidade": "m²",
            },
        ).json()
        r = client.post("/api/v1/item-fichas", json={"ficha_servico_id": fs["id"]})
        assert r.status_code == 422

    def test_sem_ficha_rejeitado(self, client):
        comp = client.post("/api/v1/componentes", json={"nome": "c"}).json()
        r = client.post("/api/v1/item-fichas", json={"componente_id": comp["id"]})
        assert r.status_code == 422
