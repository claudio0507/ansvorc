"""CRUD tests para as 8 tabelas do Bloco 1 — alinhados ao spec docs/02."""

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base, get_db
from backend.main import app

TEST_DATABASE_URL = "sqlite:///:memory:"

engine_test = create_engine(
    TEST_DATABASE_URL,
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


# ── bd_BDI ──────────────────────────────────────────────────────────────────


class TestBdBDI:
    BASE = "/api/v1/bd-bdi"
    PAYLOAD = {
        "modalidade": "BDI-MO",
        "uf": "PR",
        "pis": "0.0065",
        "cofins": "0.0300",
        "issqn": "0.0350",
    }

    def test_criar_bdi(self, client):
        resp = client.post(self.BASE, json=self.PAYLOAD)
        assert resp.status_code == 201
        data = resp.json()
        assert data["modalidade"] == "BDI-MO"
        assert data["uf"] == "PR"
        assert data["despesas_adm"] == "0.1300"  # default
        assert data["custo_financeiro"] == "0.0150"  # default

    def test_uf_normalizada_uppercase(self, client):
        resp = client.post(self.BASE, json={**self.PAYLOAD, "uf": "sp"})
        assert resp.status_code == 201
        assert resp.json()["uf"] == "SP"

    def test_unique_modalidade_uf(self, client):
        client.post(self.BASE, json=self.PAYLOAD)
        # Mesma (modalidade, uf) → viola UNIQUE
        resp = client.post(self.BASE, json=self.PAYLOAD)
        assert resp.status_code in (400, 409, 500)  # integridade

    def test_filtro_por_uf(self, client):
        client.post(self.BASE, json={**self.PAYLOAD, "uf": "PR"})
        client.post(self.BASE, json={**self.PAYLOAD, "uf": "SP"})
        resp = client.get(f"{self.BASE}?uf=PR")
        assert resp.status_code == 200
        dados = resp.json()
        assert len(dados) == 1 and dados[0]["uf"] == "PR"

    def test_listar_bdi_vazio(self, client):
        assert client.get(self.BASE).json() == []

    def test_obter_e_404(self, client):
        client.post(self.BASE, json=self.PAYLOAD)
        assert client.get(f"{self.BASE}/1").status_code == 200
        assert client.get(f"{self.BASE}/999").status_code == 404

    def test_atualizar_bdi(self, client):
        client.post(self.BASE, json=self.PAYLOAD)
        resp = client.put(f"{self.BASE}/1", json={"icms": "0.1200"})
        assert resp.status_code == 200
        assert resp.json()["icms"] == "0.1200"

    def test_deletar_bdi(self, client):
        client.post(self.BASE, json=self.PAYLOAD)
        assert client.delete(f"{self.BASE}/1").status_code == 204
        assert client.get(f"{self.BASE}/1").status_code == 404


# ── bd_RH ───────────────────────────────────────────────────────────────────


class TestBdRH:
    BASE = "/api/v1/bd-rh"
    PAYLOAD = {"cargo": "Encarregado", "custo_diario": "327.27"}

    def test_criar_rh(self, client):
        resp = client.post(self.BASE, json=self.PAYLOAD)
        assert resp.status_code == 201
        assert resp.json()["cargo"] == "Encarregado"

    def test_custo_decimal_preciso(self, client):
        resp = client.post(self.BASE, json=self.PAYLOAD)
        assert resp.json()["custo_diario"] == "327.2700"

    def test_cargo_capitalizado(self, client):
        resp = client.post(self.BASE, json={"cargo": "auxiliar", "custo_diario": "200"})
        assert resp.json()["cargo"] == "Auxiliar"

    def test_custo_negativo_rejeitado(self, client):
        resp = client.post(self.BASE, json={"cargo": "X", "custo_diario": "-100.00"})
        assert resp.status_code == 422

    def test_atualizar_e_deletar(self, client):
        client.post(self.BASE, json=self.PAYLOAD)
        assert (
            client.put(f"{self.BASE}/1", json={"cargo": "Encarregado Sênior"}).json()[
                "cargo"
            ]
            == "Encarregado Sênior"
        )
        assert client.delete(f"{self.BASE}/1").status_code == 204


# ── bd_EPI ──────────────────────────────────────────────────────────────────


class TestBdEPI:
    BASE = "/api/v1/bd-epi"
    PAYLOAD = {"item": "Kit EPI Encarregado", "custo_diario": "3.50"}

    def test_crud_completo_epi(self, client):
        post = client.post(self.BASE, json=self.PAYLOAD)
        assert post.status_code == 201
        assert post.json()["item"] == "Kit EPI Encarregado"
        id_ = post.json()["id"]
        assert client.get(f"{self.BASE}/{id_}").status_code == 200
        put = client.put(f"{self.BASE}/{id_}", json={"custo_diario": "4.00"})
        assert put.json()["custo_diario"] == "4.0000"
        assert client.delete(f"{self.BASE}/{id_}").status_code == 204


# ── bd_FERRAMENTAL (por seguimento) ─────────────────────────────────────────


class TestBdFerramental:
    BASE = "/api/v1/bd-ferramental"
    PAYLOAD = {"seguimento": "EPS", "custo_diario": "271.05"}

    def test_criar_ferramental(self, client):
        resp = client.post(self.BASE, json=self.PAYLOAD)
        assert resp.status_code == 201
        assert resp.json()["seguimento"] == "EPS"

    def test_seguimento_uppercase(self, client):
        resp = client.post(
            self.BASE, json={"seguimento": "horizontal", "custo_diario": "35.90"}
        )
        assert resp.json()["seguimento"] == "HORIZONTAL"

    def test_filtro_seguimento(self, client):
        client.post(self.BASE, json={"seguimento": "EPS", "custo_diario": "271.05"})
        client.post(self.BASE, json={"seguimento": "VERTICAL", "custo_diario": "24.56"})
        resp = client.get(f"{self.BASE}?seguimento=EPS")
        assert len(resp.json()) == 1


# ── bd_FROTAS (por seguimento) ──────────────────────────────────────────────


class TestBdFrotas:
    BASE = "/api/v1/bd-frotas"
    PAYLOAD = {"seguimento": "EPS", "custo_diario": "1368.54"}

    def test_criar_frotas(self, client):
        resp = client.post(self.BASE, json=self.PAYLOAD)
        assert resp.status_code == 201
        assert resp.json()["seguimento"] == "EPS"

    def test_filtro_seguimento(self, client):
        client.post(self.BASE, json={"seguimento": "EPS", "custo_diario": "1368.54"})
        client.post(self.BASE, json={"seguimento": "APOIO", "custo_diario": "280.00"})
        assert len(client.get(f"{self.BASE}?seguimento=APOIO").json()) == 1


# ── bd_MATERIAIS ─────────────────────────────────────────────────────────────


class TestBdMateriais:
    BASE = "/api/v1/bd-materiais"
    PAYLOAD = {
        "material": "Chapa de Aço 1,00",
        "unidade": "und",
        "destinacao": "FABRICA",
        "valor_unitario": "25.50",
    }

    def test_criar_material(self, client):
        resp = client.post(self.BASE, json=self.PAYLOAD)
        assert resp.status_code == 201
        assert resp.json()["destinacao"] == "FABRICA"
        assert resp.json()["valor_unitario"] == "25.5000"

    def test_destinacao_opcional(self, client):
        payload = {k: v for k, v in self.PAYLOAD.items() if k != "destinacao"}
        resp = client.post(self.BASE, json=payload)
        assert resp.status_code == 201
        assert resp.json()["destinacao"] is None


# ── bd_ESTRUTURA_OPERACIONAL ─────────────────────────────────────────────────


class TestBdEstrutura:
    BASE = "/api/v1/bd-estrutura"
    PAYLOAD = {
        "item": "Base de Apoio Operacional",
        "unidade": "Mês",
        "tipo": "Base_de_Apoio",
        "valor_unitario": "57000.00",
    }

    def test_criar_estrutura(self, client):
        resp = client.post(self.BASE, json=self.PAYLOAD)
        assert resp.status_code == 201
        assert resp.json()["tipo"] == "Base_de_Apoio"

    def test_valor_grande_decimal(self, client):
        resp = client.post(self.BASE, json=self.PAYLOAD)
        assert Decimal(resp.json()["valor_unitario"]) == Decimal("57000.0000")


# ── bd_DESPESAS (por seguimento) ────────────────────────────────────────────


class TestBdDespesas:
    BASE = "/api/v1/bd-despesas"
    PAYLOAD = {
        "seguimento": "EPS",
        "epc": "15.00",
        "refeicao": "35.00",
        "hospedagem": "50.00",
    }

    def test_criar_despesa(self, client):
        resp = client.post(self.BASE, json=self.PAYLOAD)
        assert resp.status_code == 201
        d = resp.json()
        assert d["seguimento"] == "EPS"
        assert d["refeicao"] == "35.0000"
        assert d["hospedagem"] == "50.0000"

    def test_filtro_seguimento(self, client):
        client.post(self.BASE, json=self.PAYLOAD)
        client.post(self.BASE, json={**self.PAYLOAD, "seguimento": "APOIO"})
        assert len(client.get(f"{self.BASE}?seguimento=APOIO").json()) == 1

    def test_atualizar_despesa(self, client):
        client.post(self.BASE, json=self.PAYLOAD)
        resp = client.put(f"{self.BASE}/1", json={"refeicao": "40.00"})
        assert resp.json()["refeicao"] == "40.0000"
