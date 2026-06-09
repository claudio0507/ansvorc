"""CRUD tests para as 8 tabelas do Bloco 1 — SQLite em memória."""

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base, get_db
from backend.main import app

# ── Configuração do banco de testes ─────────────────────────────────────────

TEST_DATABASE_URL = "sqlite:///:memory:"

# StaticPool garante que todas as conexões compartilhem o mesmo banco em memória
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

    def test_criar_bdi(self, client):
        payload = {"modalidade": "BDI-MO", "adm_percentual": "0.1300"}
        resp = client.post(self.BASE, json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["id"] == 1
        assert data["modalidade"] == "BDI-MO"

    def test_listar_bdi_vazio(self, client):
        resp = client.get(self.BASE)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_listar_bdi_com_registro(self, client):
        client.post(self.BASE, json={"modalidade": "BDI+ICMS"})
        resp = client.get(self.BASE)
        assert len(resp.json()) == 1

    def test_obter_bdi_por_id(self, client):
        client.post(self.BASE, json={"modalidade": "FAT DIR SIMP"})
        resp = client.get(f"{self.BASE}/1")
        assert resp.status_code == 200
        assert resp.json()["modalidade"] == "FAT DIR SIMP"

    def test_obter_bdi_nao_encontrado(self, client):
        resp = client.get(f"{self.BASE}/999")
        assert resp.status_code == 404

    def test_atualizar_bdi(self, client):
        client.post(self.BASE, json={"modalidade": "BDI-MAT+MO"})
        resp = client.put(f"{self.BASE}/1", json={"descricao": "Atualizado"})
        assert resp.status_code == 200
        assert resp.json()["descricao"] == "Atualizado"

    def test_deletar_bdi(self, client):
        client.post(self.BASE, json={"modalidade": "BDI-MO"})
        resp = client.delete(f"{self.BASE}/1")
        assert resp.status_code == 204
        assert client.get(f"{self.BASE}/1").status_code == 404


# ── bd_RH ───────────────────────────────────────────────────────────────────

class TestBdRH:
    BASE = "/api/v1/bd-rh"

    RH_PAYLOAD = {
        "codigo": "RH-001",
        "cargo": "Encarregado Geral",
        "categoria": "OPERACIONAL",
        "salario_base": "4500.00",
        "encargos_percentual": "0.7200",
        "horas_mes": "220.00",
    }

    def test_criar_rh(self, client):
        resp = client.post(self.BASE, json=self.RH_PAYLOAD)
        assert resp.status_code == 201
        data = resp.json()
        assert data["cargo"] == "Encarregado Geral"
        assert data["codigo"] == "RH-001"

    def test_salario_base_decimal_preciso(self, client):
        resp = client.post(self.BASE, json=self.RH_PAYLOAD)
        assert resp.status_code == 201
        # Deve preservar exatidão decimal
        assert resp.json()["salario_base"] == "4500.0000"

    def test_salario_negativo_rejeitado(self, client):
        payload = {**self.RH_PAYLOAD, "salario_base": "-100.00"}
        resp = client.post(self.BASE, json=payload)
        assert resp.status_code == 422

    def test_listar_rh(self, client):
        client.post(self.BASE, json=self.RH_PAYLOAD)
        resp = client.get(self.BASE)
        assert len(resp.json()) == 1

    def test_atualizar_rh(self, client):
        client.post(self.BASE, json=self.RH_PAYLOAD)
        resp = client.put(f"{self.BASE}/1", json={"cargo": "Encarregado Sênior"})
        assert resp.status_code == 200
        assert resp.json()["cargo"] == "Encarregado Sênior"

    def test_deletar_rh(self, client):
        client.post(self.BASE, json=self.RH_PAYLOAD)
        assert client.delete(f"{self.BASE}/1").status_code == 204
        assert client.get(f"{self.BASE}/1").status_code == 404


# ── bd_EPI ──────────────────────────────────────────────────────────────────

class TestBdEPI:
    BASE = "/api/v1/bd-epi"

    EPI_PAYLOAD = {
        "codigo": "EPI-001",
        "descricao": "Capacete de segurança",
        "unidade_medida": "un",
        "custo_unitario": "35.00",
        "vida_util_dias": 365,
    }

    def test_criar_epi(self, client):
        resp = client.post(self.BASE, json=self.EPI_PAYLOAD)
        assert resp.status_code == 201
        assert resp.json()["codigo"] == "EPI-001"

    def test_vida_util_opcional(self, client):
        payload = {**self.EPI_PAYLOAD}
        del payload["vida_util_dias"]
        resp = client.post(self.BASE, json=payload)
        assert resp.status_code == 201
        assert resp.json()["vida_util_dias"] is None

    def test_crud_completo_epi(self, client):
        # CREATE
        post = client.post(self.BASE, json=self.EPI_PAYLOAD)
        id_ = post.json()["id"]
        # READ
        assert client.get(f"{self.BASE}/{id_}").status_code == 200
        # UPDATE
        put = client.put(f"{self.BASE}/{id_}", json={"custo_unitario": "40.00"})
        assert put.json()["custo_unitario"] == "40.0000"
        # DELETE
        assert client.delete(f"{self.BASE}/{id_}").status_code == 204


# ── bd_FERRAMENTAL ──────────────────────────────────────────────────────────

class TestBdFerramental:
    BASE = "/api/v1/bd-ferramental"

    PAYLOAD = {
        "codigo": "FER-001",
        "descricao": "Furadeira 850W",
        "unidade_medida": "un",
        "custo_unitario": "480.00",
        "vida_util_dias": 1095,
    }

    def test_criar_ferramental(self, client):
        resp = client.post(self.BASE, json=self.PAYLOAD)
        assert resp.status_code == 201
        assert resp.json()["descricao"] == "Furadeira 850W"

    def test_atualizar_ferramental(self, client):
        client.post(self.BASE, json=self.PAYLOAD)
        resp = client.put(f"{self.BASE}/1", json={"ativo": False})
        assert resp.json()["ativo"] is False

    def test_nao_encontrado(self, client):
        assert client.get(f"{self.BASE}/99").status_code == 404


# ── bd_FROTAS ───────────────────────────────────────────────────────────────

class TestBdFrotas:
    BASE = "/api/v1/bd-frotas"

    PAYLOAD = {
        "codigo": "FRT-001",
        "descricao": "Caminhão de sinalização",
        "tipo": "VEICULO_PESADO",
        "custo_diaria": "1200.00",
        "custo_km": "1.80",
    }

    def test_criar_frotas(self, client):
        resp = client.post(self.BASE, json=self.PAYLOAD)
        assert resp.status_code == 201
        assert resp.json()["tipo"] == "VEICULO_PESADO"

    def test_custo_km_opcional(self, client):
        payload = {k: v for k, v in self.PAYLOAD.items() if k != "custo_km"}
        payload["codigo"] = "FRT-002"
        resp = client.post(self.BASE, json=payload)
        assert resp.status_code == 201
        assert resp.json()["custo_km"] is None

    def test_atualizar_tipo(self, client):
        client.post(self.BASE, json=self.PAYLOAD)
        resp = client.put(f"{self.BASE}/1", json={"tipo": "EQUIPAMENTO"})
        assert resp.json()["tipo"] == "EQUIPAMENTO"


# ── bd_MATERIAIS ─────────────────────────────────────────────────────────────

class TestBdMateriais:
    BASE = "/api/v1/bd-materiais"

    PAYLOAD = {
        "codigo": "MAT-001",
        "descricao": "Chapa de aço galvanizada R-1",
        "categoria": "PLACA",
        "unidade_medida": "un",
        "custo_unitario": "185.00",
        "icms_incide": True,
    }

    def test_criar_material(self, client):
        resp = client.post(self.BASE, json=self.PAYLOAD)
        assert resp.status_code == 201
        assert resp.json()["icms_incide"] is True

    def test_icms_padrao_verdadeiro(self, client):
        payload = {**self.PAYLOAD}
        del payload["icms_incide"]
        resp = client.post(self.BASE, json=payload)
        assert resp.json()["icms_incide"] is True

    def test_listar_materiais(self, client):
        client.post(self.BASE, json=self.PAYLOAD)
        assert len(client.get(self.BASE).json()) == 1


# ── bd_ESTRUTURA_OPERACIONAL ─────────────────────────────────────────────────

class TestBdEstrutura:
    BASE = "/api/v1/bd-estrutura"

    PAYLOAD = {
        "codigo": "EST-001",
        "descricao": "Alojamento Passo Fundo",
        "tipo": "ALOJAMENTO",
        "unidade_medida": "Mês",
        "custo_unitario": "57000.00",
    }

    def test_criar_estrutura(self, client):
        resp = client.post(self.BASE, json=self.PAYLOAD)
        assert resp.status_code == 201
        assert resp.json()["tipo"] == "ALOJAMENTO"

    def test_custo_grande_decimal(self, client):
        resp = client.post(self.BASE, json=self.PAYLOAD)
        assert Decimal(resp.json()["custo_unitario"]) == Decimal("57000.0000")

    def test_deletar_estrutura(self, client):
        client.post(self.BASE, json=self.PAYLOAD)
        assert client.delete(f"{self.BASE}/1").status_code == 204


# ── bd_DESPESAS ──────────────────────────────────────────────────────────────

class TestBdDespesas:
    BASE = "/api/v1/bd-despesas"

    PAYLOAD_PERCENTUAL = {
        "codigo": "DEP-001",
        "descricao": "Despesas Administrativas",
        "tipo": "ADMINISTRATIVA",
        "percentual": "0.1300",
    }

    PAYLOAD_FIXO = {
        "codigo": "DEP-002",
        "descricao": "Taxa fixa de contrato",
        "tipo": "FINANCEIRA",
        "valor_fixo": "1500.00",
    }

    def test_criar_despesa_percentual(self, client):
        resp = client.post(self.BASE, json=self.PAYLOAD_PERCENTUAL)
        assert resp.status_code == 201
        assert resp.json()["percentual"] == "0.1300"
        assert resp.json()["valor_fixo"] is None

    def test_criar_despesa_valor_fixo(self, client):
        resp = client.post(self.BASE, json=self.PAYLOAD_FIXO)
        assert resp.status_code == 201
        assert resp.json()["valor_fixo"] == "1500.0000"
        assert resp.json()["percentual"] is None

    def test_listar_despesas(self, client):
        client.post(self.BASE, json=self.PAYLOAD_PERCENTUAL)
        client.post(self.BASE, json=self.PAYLOAD_FIXO)
        assert len(client.get(self.BASE).json()) == 2

    def test_atualizar_despesa(self, client):
        client.post(self.BASE, json=self.PAYLOAD_PERCENTUAL)
        resp = client.put(f"{self.BASE}/1", json={"percentual": "0.1500"})
        assert resp.json()["percentual"] == "0.1500"
