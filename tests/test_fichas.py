"""Testes das fichas técnicas — alinhados ao spec docs/02 + docs/03.

Equipe: cargos (bd_RH) + EPI + refeição/hospedagem por seguimento (lookup automático).
Produto: BOM recursivo. Serviço: equipe + frota + ferramental simultâneos.
"""

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base, get_db
from backend.main import app
from backend.models.bd_models import (
    BdDespesas,
    BdEPI,
    BdFerramental,
    BdFrotas,
    BdMateriais,
    BdRH,
)

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


@pytest.fixture()
def db_session(setup_db):
    db = TestingSessionLocal()
    yield db
    db.close()


@pytest.fixture()
def base_eps(db_session):
    """Insumos do seguimento EPS p/ os lookups de equipe/serviço."""
    rh = BdRH(cargo="Encarregado", custo_diario=Decimal("327.27"))
    aux = BdRH(cargo="Auxiliar", custo_diario=Decimal("200.00"))
    epi = BdEPI(item="Kit EPI", custo_diario=Decimal("3.50"))
    desp = BdDespesas(
        seguimento="EPS",
        epc=Decimal("15"),
        refeicao=Decimal("35.00"),
        hospedagem=Decimal("50.00"),
    )
    frota = BdFrotas(seguimento="EPS", custo_diario=Decimal("1368.54"))
    ferr = BdFerramental(seguimento="EPS", custo_diario=Decimal("271.05"))
    db_session.add_all([rh, aux, epi, desp, frota, ferr])
    db_session.commit()
    for o in (rh, aux, epi, frota, ferr):
        db_session.refresh(o)
    return {
        "rh": rh,
        "aux": aux,
        "epi": epi,
        "frota": frota,
        "ferr": ferr,
    }


@pytest.fixture()
def materiais(db_session):
    chapa = BdMateriais(
        material="Chapa de Aço", unidade="und", valor_unitario=Decimal("25.50")
    )
    pelicula = BdMateriais(
        material="Película", unidade="und", valor_unitario=Decimal("90.50")
    )
    db_session.add_all([chapa, pelicula])
    db_session.commit()
    db_session.refresh(chapa)
    db_session.refresh(pelicula)
    return {"chapa": chapa, "pelicula": pelicula}


# ── Fichas de Equipe ─────────────────────────────────────────────────────────


class TestFichaEquipe:
    BASE = "/api/v1/fichas-equipe"

    def test_criar_ficha_equipe(self, client):
        resp = client.post(self.BASE, json={"codigo": "eq-001", "seguimento": "eps"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["codigo"] == "EQ-001"  # normalizado
        assert data["seguimento"] == "EPS"
        assert data["custo_dia_total"] == "0.0000"
        assert data["itens"] == []

    def test_filtro_seguimento(self, client):
        client.post(self.BASE, json={"codigo": "EQ-1", "seguimento": "EPS"})
        client.post(self.BASE, json={"codigo": "EQ-2", "seguimento": "VERTICAL"})
        assert len(client.get(f"{self.BASE}?seguimento=EPS").json()) == 1

    def test_item_lookup_e_custo_dia_linha(self, client, base_eps):
        fid = client.post(
            self.BASE, json={"codigo": "EQ-001", "seguimento": "EPS"}
        ).json()["id"]
        resp = client.post(
            f"{self.BASE}/{fid}/itens",
            json={
                "rh_id": base_eps["rh"].id,
                "epi_id": base_eps["epi"].id,
                "quantidade": 2,
            },
        )
        assert resp.status_code == 201
        d = resp.json()
        # (327.27 + 3.50 + 35 + 50) × 2 = 831.54
        assert Decimal(d["custo_dia_linha"]) == Decimal("831.5400")
        assert Decimal(d["custo_mo"]) == Decimal("327.2700")
        assert Decimal(d["refeicao"]) == Decimal("35.0000")
        assert Decimal(d["hospedagem"]) == Decimal("50.0000")

    def test_custo_dia_total_soma_itens(self, client, base_eps):
        fid = client.post(
            self.BASE, json={"codigo": "EQ-001", "seguimento": "EPS"}
        ).json()["id"]
        client.post(
            f"{self.BASE}/{fid}/itens",
            json={"rh_id": base_eps["rh"].id, "quantidade": 1},
        )
        client.post(
            f"{self.BASE}/{fid}/itens",
            json={"rh_id": base_eps["aux"].id, "quantidade": 3},
        )
        ficha = client.get(f"{self.BASE}/{fid}").json()
        # enc: (327.27+0+35+50)×1 = 412.27 ; aux: (200+0+35+50)×3 = 855.00
        assert Decimal(ficha["custo_dia_total"]) == Decimal("1267.2700")
        assert len(ficha["itens"]) == 2

    def test_item_sem_epi_ok(self, client, base_eps):
        fid = client.post(
            self.BASE, json={"codigo": "EQ-001", "seguimento": "EPS"}
        ).json()["id"]
        resp = client.post(
            f"{self.BASE}/{fid}/itens",
            json={"rh_id": base_eps["rh"].id, "quantidade": 1},
        )
        assert resp.status_code == 201
        assert Decimal(resp.json()["custo_epi"]) == Decimal("0.0000")

    def test_quantidade_inteira(self, client, base_eps):
        fid = client.post(
            self.BASE, json={"codigo": "EQ-001", "seguimento": "EPS"}
        ).json()["id"]
        # quantidade decimal deve ser rejeitada (pessoas = inteiro)
        resp = client.post(
            f"{self.BASE}/{fid}/itens",
            json={"rh_id": base_eps["rh"].id, "quantidade": 1.5},
        )
        assert resp.status_code == 422

    def test_remover_item_recalcula(self, client, base_eps):
        fid = client.post(
            self.BASE, json={"codigo": "EQ-001", "seguimento": "EPS"}
        ).json()["id"]
        item_id = client.post(
            f"{self.BASE}/{fid}/itens",
            json={"rh_id": base_eps["rh"].id, "quantidade": 1},
        ).json()["id"]
        client.delete(f"{self.BASE}/{fid}/itens/{item_id}")
        assert Decimal(
            client.get(f"{self.BASE}/{fid}").json()["custo_dia_total"]
        ) == Decimal("0.0000")

    def test_deletar_ficha_equipe(self, client):
        client.post(self.BASE, json={"codigo": "EQ-001", "seguimento": "EPS"})
        assert client.delete(f"{self.BASE}/1").status_code == 204
        assert client.get(f"{self.BASE}/1").status_code == 404


# ── Fichas de Produto (BOM) ───────────────────────────────────────────────────


class TestFichaProduto:
    BASE = "/api/v1/fichas-produto"

    def test_criar_ficha_produto(self, client):
        resp = client.post(
            self.BASE,
            json={"codigo": "prod-001", "nome": "placa r-1", "unidade": "und"},
        )
        assert resp.status_code == 201
        d = resp.json()
        assert d["codigo"] == "PROD-001"
        assert d["nome"] == "Placa r-1"
        assert d["possui_ficha"] is True
        assert d["custo_total"] == "0.0000"

    def test_adicionar_material_e_custo_total(self, client, materiais):
        fid = client.post(
            self.BASE, json={"codigo": "PROD-001", "nome": "Placa", "unidade": "und"}
        ).json()["id"]
        resp = client.post(
            f"{self.BASE}/{fid}/itens",
            json={"material_id": materiais["chapa"].id, "quantidade": "2"},
        )
        assert resp.status_code == 201
        d = resp.json()
        assert Decimal(d["custo_unitario"]) == Decimal("25.5000")
        assert Decimal(d["custo_total_linha"]) == Decimal("51.0000")
        assert d["unidade"] == "und"  # herdado do material
        ficha = client.get(f"{self.BASE}/{fid}").json()
        assert Decimal(ficha["custo_total"]) == Decimal("51.0000")

    def test_bom_aninhado(self, client, materiais):
        pai = client.post(
            self.BASE, json={"codigo": "PROD-PAI", "nome": "Montada", "unidade": "und"}
        ).json()["id"]
        filho = client.post(
            self.BASE, json={"codigo": "PROD-FILHO", "nome": "Sub", "unidade": "und"}
        ).json()["id"]
        client.post(
            f"{self.BASE}/{filho}/itens",
            json={"material_id": materiais["chapa"].id, "quantidade": "1"},
        )
        client.post(
            f"{self.BASE}/{filho}/itens",
            json={"material_id": materiais["pelicula"].id, "quantidade": "3"},
        )
        # custo do filho = 25.50 + 271.50 = 297.00
        resp = client.post(
            f"{self.BASE}/{pai}/itens",
            json={"componente_filho_id": filho, "quantidade": "1"},
        )
        assert resp.status_code == 201
        assert Decimal(resp.json()["custo_unitario"]) == Decimal("297.0000")

    def test_item_sem_fk_rejeitado(self, client):
        client.post(self.BASE, json={"codigo": "P1", "nome": "P", "unidade": "und"})
        assert (
            client.post(f"{self.BASE}/1/itens", json={"quantidade": "1"}).status_code
            == 422
        )

    def test_item_ambos_fk_rejeitado(self, client, materiais):
        client.post(self.BASE, json={"codigo": "P1", "nome": "P", "unidade": "und"})
        client.post(self.BASE, json={"codigo": "P2", "nome": "Sub", "unidade": "und"})
        resp = client.post(
            f"{self.BASE}/1/itens",
            json={
                "material_id": materiais["chapa"].id,
                "componente_filho_id": 2,
                "quantidade": "1",
            },
        )
        assert resp.status_code == 422

    def test_ciclo_bom_self_reference(self, client):
        client.post(self.BASE, json={"codigo": "P1", "nome": "P", "unidade": "und"})
        resp = client.post(
            f"{self.BASE}/1/itens", json={"componente_filho_id": 1, "quantidade": "1"}
        )
        assert resp.status_code == 422

    def test_ciclo_bom_indireto(self, client):
        for c in ("A", "B", "C"):
            client.post(self.BASE, json={"codigo": c, "nome": c, "unidade": "und"})
        client.post(
            f"{self.BASE}/1/itens", json={"componente_filho_id": 2, "quantidade": "1"}
        )
        client.post(
            f"{self.BASE}/2/itens", json={"componente_filho_id": 3, "quantidade": "1"}
        )
        resp = client.post(
            f"{self.BASE}/3/itens", json={"componente_filho_id": 1, "quantidade": "1"}
        )
        assert resp.status_code == 422
        assert (
            "circular" in resp.json()["detail"].lower()
            or "ciclo" in resp.json()["detail"].lower()
        )


# ── Fichas de Serviço ─────────────────────────────────────────────────────────


class TestFichaServico:
    BASE = "/api/v1/fichas-servico"
    BASE_EQ = "/api/v1/fichas-equipe"

    PAYLOAD = {
        "codigo": "sv-001",
        "nome": "pintura",
        "seguimento": "eps",
        "produtividade_dia": "200",
        "unidade": "m²",
    }

    def test_criar_ficha_servico(self, client):
        resp = client.post(self.BASE, json=self.PAYLOAD)
        assert resp.status_code == 201
        d = resp.json()
        assert d["codigo"] == "SV-001"
        assert d["seguimento"] == "EPS"
        assert d["possui_ficha"] is True

    def test_produtividade_zero_rejeitada(self, client):
        resp = client.post(self.BASE, json={**self.PAYLOAD, "produtividade_dia": "0"})
        assert resp.status_code == 422

    def test_filtro_seguimento(self, client):
        client.post(self.BASE, json=self.PAYLOAD)
        client.post(
            self.BASE, json={**self.PAYLOAD, "codigo": "SV-2", "seguimento": "VERTICAL"}
        )
        assert len(client.get(f"{self.BASE}?seguimento=EPS").json()) == 1

    def test_recurso_simultaneo_e_custo(self, client, base_eps):
        # Equipe com 1 encarregado (custo_dia = 412.27)
        eid = client.post(
            self.BASE_EQ, json={"codigo": "EQ-001", "seguimento": "EPS"}
        ).json()["id"]
        client.post(
            f"{self.BASE_EQ}/{eid}/itens",
            json={"rh_id": base_eps["rh"].id, "quantidade": 1},
        )
        sid = client.post(self.BASE, json=self.PAYLOAD).json()["id"]
        resp = client.post(
            f"{self.BASE}/{sid}/recursos",
            json={
                "ficha_equipe_id": eid,
                "frota_id": base_eps["frota"].id,
                "ferramental_id": base_eps["ferr"].id,
            },
        )
        assert resp.status_code == 201
        # (412.27 + 1368.54 + 271.05) / 200 = 10.2593
        servico = client.get(f"{self.BASE}/{sid}").json()
        assert Decimal(servico["custo_unitario"]) == Decimal("10.2593")

    def test_recurso_fk_inexistente_rejeitado(self, client, base_eps):
        sid = client.post(self.BASE, json=self.PAYLOAD).json()["id"]
        resp = client.post(
            f"{self.BASE}/{sid}/recursos",
            json={
                "ficha_equipe_id": 999,
                "frota_id": base_eps["frota"].id,
                "ferramental_id": base_eps["ferr"].id,
            },
        )
        assert resp.status_code == 422

    def test_recurso_incompleto_rejeitado(self, client, base_eps):
        sid = client.post(self.BASE, json=self.PAYLOAD).json()["id"]
        # falta ferramental_id (obrigatório no schema)
        resp = client.post(
            f"{self.BASE}/{sid}/recursos",
            json={"ficha_equipe_id": 1, "frota_id": base_eps["frota"].id},
        )
        assert resp.status_code == 422

    def test_remover_recurso_recalcula(self, client, base_eps):
        eid = client.post(
            self.BASE_EQ, json={"codigo": "EQ-001", "seguimento": "EPS"}
        ).json()["id"]
        client.post(
            f"{self.BASE_EQ}/{eid}/itens",
            json={"rh_id": base_eps["rh"].id, "quantidade": 1},
        )
        sid = client.post(self.BASE, json=self.PAYLOAD).json()["id"]
        rid = client.post(
            f"{self.BASE}/{sid}/recursos",
            json={
                "ficha_equipe_id": eid,
                "frota_id": base_eps["frota"].id,
                "ferramental_id": base_eps["ferr"].id,
            },
        ).json()["id"]
        client.delete(f"{self.BASE}/{sid}/recursos/{rid}")
        assert Decimal(
            client.get(f"{self.BASE}/{sid}").json()["custo_unitario"]
        ) == Decimal("0.0000")

    def test_deletar_ficha_servico(self, client):
        client.post(self.BASE, json=self.PAYLOAD)
        assert client.delete(f"{self.BASE}/1").status_code == 204
