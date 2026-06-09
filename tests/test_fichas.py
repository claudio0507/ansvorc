"""Testes CRUD das fichas técnicas — Fase 1.3."""

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base, get_db
from backend.main import app
from backend.models.bd_models import BdEPI, BdFerramental, BdFrotas, BdMateriais, BdRH

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


# ── Fixtures de dados base ────────────────────────────────────────────────────


@pytest.fixture()
def db_session(setup_db):
    db = TestingSessionLocal()
    yield db
    db.close()


@pytest.fixture()
def rh_encarregado(db_session):
    rh = BdRH(
        codigo="RH-T01",
        cargo="Encarregado",
        categoria="OPERACIONAL",
        salario_base=Decimal("4500.00"),
        encargos_percentual=Decimal("0.7200"),
        horas_mes=Decimal("220.00"),
    )
    db_session.add(rh)
    db_session.commit()
    db_session.refresh(rh)
    return rh


@pytest.fixture()
def rh_auxiliar(db_session):
    rh = BdRH(
        codigo="RH-T02",
        cargo="Auxiliar",
        categoria="OPERACIONAL",
        salario_base=Decimal("2200.00"),
        encargos_percentual=Decimal("0.7200"),
        horas_mes=Decimal("220.00"),
    )
    db_session.add(rh)
    db_session.commit()
    db_session.refresh(rh)
    return rh


@pytest.fixture()
def epi_capacete(db_session):
    epi = BdEPI(
        codigo="EPI-T01",
        descricao="Capacete",
        unidade_medida="un",
        custo_unitario=Decimal("35.00"),
        vida_util_dias=365,
    )
    db_session.add(epi)
    db_session.commit()
    db_session.refresh(epi)
    return epi


@pytest.fixture()
def ferramental_furadeira(db_session):
    ferr = BdFerramental(
        codigo="FER-T01",
        descricao="Furadeira",
        unidade_medida="un",
        custo_unitario=Decimal("480.00"),
        vida_util_dias=1095,
    )
    db_session.add(ferr)
    db_session.commit()
    db_session.refresh(ferr)
    return ferr


@pytest.fixture()
def frota_caminhao(db_session):
    frota = BdFrotas(
        codigo="FRT-T01",
        descricao="Caminhão",
        tipo="VEICULO_PESADO",
        custo_diaria=Decimal("1200.00"),
    )
    db_session.add(frota)
    db_session.commit()
    db_session.refresh(frota)
    return frota


@pytest.fixture()
def material_chapa(db_session):
    mat = BdMateriais(
        codigo="MAT-T01",
        descricao="Chapa galvanizada",
        categoria="PLACA",
        unidade_medida="un",
        custo_unitario=Decimal("185.00"),
    )
    db_session.add(mat)
    db_session.commit()
    db_session.refresh(mat)
    return mat


@pytest.fixture()
def material_pelicula(db_session):
    mat = BdMateriais(
        codigo="MAT-T02",
        descricao="Película refletiva",
        categoria="PELICULA",
        unidade_medida="m²",
        custo_unitario=Decimal("120.00"),
    )
    db_session.add(mat)
    db_session.commit()
    db_session.refresh(mat)
    return mat


# ── Fichas de Equipe ─────────────────────────────────────────────────────────


class TestFichaEquipe:
    BASE = "/api/v1/fichas-equipe"

    def test_criar_ficha_equipe(self, client):
        payload = {
            "codigo": "EQ-001",
            "nome": "Equipe de Sinalização Vertical",
            "producao_diaria": "50.00",
            "unidade_producao": "un",
        }
        resp = client.post(self.BASE, json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["codigo"] == "EQ-001"
        assert data["possui_itens"] is False
        assert data["itens"] == []

    def test_listar_fichas_equipe_vazio(self, client):
        assert client.get(self.BASE).json() == []

    def test_obter_ficha_equipe(self, client):
        client.post(self.BASE, json={"codigo": "EQ-001", "nome": "Equipe SH"})
        resp = client.get(f"{self.BASE}/1")
        assert resp.status_code == 200
        assert resp.json()["nome"] == "Equipe SH"

    def test_nao_encontrado(self, client):
        assert client.get(f"{self.BASE}/999").status_code == 404

    def test_atualizar_ficha_equipe(self, client):
        client.post(self.BASE, json={"codigo": "EQ-001", "nome": "Equipe"})
        resp = client.put(f"{self.BASE}/1", json={"nome": "Equipe Atualizada"})
        assert resp.json()["nome"] == "Equipe Atualizada"

    def test_deletar_ficha_equipe(self, client):
        client.post(self.BASE, json={"codigo": "EQ-001", "nome": "Equipe"})
        assert client.delete(f"{self.BASE}/1").status_code == 204
        assert client.get(f"{self.BASE}/1").status_code == 404

    def test_adicionar_item_rh_lookup_automatico(self, client, rh_encarregado):
        client.post(self.BASE, json={"codigo": "EQ-001", "nome": "Equipe"})
        payload = {
            "tipo_recurso": "RH",
            "rh_id": rh_encarregado.id,
            "quantidade": "1.0",
        }
        resp = client.post(f"{self.BASE}/1/itens", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["tipo_recurso"] == "RH"
        # Custo = salario * (1+encargos) / horas_mes * 8
        # 4500 * 1.72 / 220 * 8 = 281.45...
        custo = Decimal(data["custo_unitario_gravado"])
        assert custo > Decimal("0")

    def test_adicionar_item_rh_seta_possui_itens(self, client, rh_encarregado):
        client.post(self.BASE, json={"codigo": "EQ-001", "nome": "Equipe"})
        client.post(
            f"{self.BASE}/1/itens",
            json={
                "tipo_recurso": "RH",
                "rh_id": rh_encarregado.id,
                "quantidade": "1.0",
            },
        )
        ficha = client.get(f"{self.BASE}/1").json()
        assert ficha["possui_itens"] is True
        assert len(ficha["itens"]) == 1

    def test_adicionar_item_epi_lookup_automatico(self, client, epi_capacete):
        client.post(self.BASE, json={"codigo": "EQ-001", "nome": "Equipe"})
        payload = {
            "tipo_recurso": "EPI",
            "epi_id": epi_capacete.id,
            "quantidade": "1.0",
        }
        resp = client.post(f"{self.BASE}/1/itens", json=payload)
        assert resp.status_code == 201
        # custo_diario = 35.00 / 365
        custo = Decimal(resp.json()["custo_unitario_gravado"])
        esperado = (Decimal("35.00") / Decimal("365")).quantize(Decimal("0.0001"))
        assert custo == esperado

    def test_adicionar_item_ferramental_lookup(self, client, ferramental_furadeira):
        client.post(self.BASE, json={"codigo": "EQ-001", "nome": "Equipe"})
        payload = {
            "tipo_recurso": "FERRAMENTAL",
            "ferramental_id": ferramental_furadeira.id,
            "quantidade": "1.0",
        }
        resp = client.post(f"{self.BASE}/1/itens", json=payload)
        assert resp.status_code == 201
        custo = Decimal(resp.json()["custo_unitario_gravado"])
        esperado = (Decimal("480.00") / Decimal("1095")).quantize(Decimal("0.0001"))
        assert custo == esperado

    def test_adicionar_item_tipo_invalido(self, client, rh_encarregado):
        client.post(self.BASE, json={"codigo": "EQ-001", "nome": "Equipe"})
        payload = {
            "tipo_recurso": "INVALIDO",
            "rh_id": rh_encarregado.id,
            "quantidade": "1.0",
        }
        resp = client.post(f"{self.BASE}/1/itens", json=payload)
        # Schema rejeita: tipo_recurso não corresponde ao FK
        assert resp.status_code == 422

    def test_item_sem_fk_rejeitado(self, client):
        client.post(self.BASE, json={"codigo": "EQ-001", "nome": "Equipe"})
        payload = {"tipo_recurso": "RH", "quantidade": "1.0"}
        resp = client.post(f"{self.BASE}/1/itens", json=payload)
        assert resp.status_code == 422

    def test_item_dois_fk_rejeitado(self, client, rh_encarregado, epi_capacete):
        client.post(self.BASE, json={"codigo": "EQ-001", "nome": "Equipe"})
        payload = {
            "tipo_recurso": "RH",
            "rh_id": rh_encarregado.id,
            "epi_id": epi_capacete.id,
            "quantidade": "1.0",
        }
        resp = client.post(f"{self.BASE}/1/itens", json=payload)
        assert resp.status_code == 422

    def test_multiplos_itens_na_equipe(self, client, rh_encarregado, rh_auxiliar):
        client.post(self.BASE, json={"codigo": "EQ-001", "nome": "Equipe"})
        client.post(
            f"{self.BASE}/1/itens",
            json={
                "tipo_recurso": "RH",
                "rh_id": rh_encarregado.id,
                "quantidade": "1.0",
            },
        )
        client.post(
            f"{self.BASE}/1/itens",
            json={"tipo_recurso": "RH", "rh_id": rh_auxiliar.id, "quantidade": "2.0"},
        )
        ficha = client.get(f"{self.BASE}/1").json()
        assert len(ficha["itens"]) == 2

    def test_remover_item_atualiza_flag(self, client, rh_encarregado):
        client.post(self.BASE, json={"codigo": "EQ-001", "nome": "Equipe"})
        r = client.post(
            f"{self.BASE}/1/itens",
            json={
                "tipo_recurso": "RH",
                "rh_id": rh_encarregado.id,
                "quantidade": "1.0",
            },
        )
        item_id = r.json()["id"]
        client.delete(f"{self.BASE}/1/itens/{item_id}")
        ficha = client.get(f"{self.BASE}/1").json()
        assert ficha["possui_itens"] is False


# ── Fichas de Produto (BOM) ───────────────────────────────────────────────────


class TestFichaProduto:
    BASE = "/api/v1/fichas-produto"

    def test_criar_ficha_produto(self, client):
        resp = client.post(
            self.BASE,
            json={
                "codigo": "PROD-001",
                "nome": "Placa R-1 0.60m",
                "unidade_medida": "un",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["possui_itens"] is False

    def test_adicionar_material(self, client, material_chapa):
        client.post(self.BASE, json={"codigo": "PROD-001", "nome": "Placa R-1"})
        resp = client.post(
            f"{self.BASE}/1/itens",
            json={"material_id": material_chapa.id, "quantidade": "1.0"},
        )
        assert resp.status_code == 201
        assert resp.json()["material_id"] == material_chapa.id
        assert Decimal(resp.json()["custo_unitario_gravado"]) == Decimal("185.0000")

    def test_adicionar_material_seta_possui_itens(self, client, material_chapa):
        client.post(self.BASE, json={"codigo": "PROD-001", "nome": "Placa R-1"})
        client.post(
            f"{self.BASE}/1/itens",
            json={"material_id": material_chapa.id, "quantidade": "1.0"},
        )
        assert client.get(f"{self.BASE}/1").json()["possui_itens"] is True

    def test_bom_aninhado_produto_filho(
        self, client, material_chapa, material_pelicula
    ):
        # Produto pai: placa montada
        client.post(self.BASE, json={"codigo": "PROD-PAI", "nome": "Placa Montada"})
        # Produto filho: chapa com película
        client.post(
            self.BASE, json={"codigo": "PROD-FILHO", "nome": "Chapa c/ Película"}
        )
        # Adiciona materiais ao filho (id=2)
        client.post(
            f"{self.BASE}/2/itens",
            json={"material_id": material_chapa.id, "quantidade": "1.0"},
        )
        client.post(
            f"{self.BASE}/2/itens",
            json={"material_id": material_pelicula.id, "quantidade": "0.36"},
        )
        # Adiciona filho ao pai
        resp = client.post(
            f"{self.BASE}/1/itens",
            json={"componente_filho_id": 2, "quantidade": "1.0"},
        )
        assert resp.status_code == 201
        assert resp.json()["componente_filho_id"] == 2

    def test_item_sem_fk_rejeitado(self, client):
        client.post(self.BASE, json={"codigo": "PROD-001", "nome": "Placa"})
        resp = client.post(f"{self.BASE}/1/itens", json={"quantidade": "1.0"})
        assert resp.status_code == 422

    def test_item_ambos_fk_rejeitado(self, client, material_chapa):
        client.post(self.BASE, json={"codigo": "PROD-001", "nome": "Placa"})
        client.post(self.BASE, json={"codigo": "PROD-002", "nome": "Sub"})
        resp = client.post(
            f"{self.BASE}/1/itens",
            json={
                "material_id": material_chapa.id,
                "componente_filho_id": 2,
                "quantidade": "1.0",
            },
        )
        assert resp.status_code == 422

    def test_ciclo_bom_self_reference(self, client):
        client.post(self.BASE, json={"codigo": "PROD-001", "nome": "Placa"})
        resp = client.post(
            f"{self.BASE}/1/itens",
            json={"componente_filho_id": 1, "quantidade": "1.0"},
        )
        assert resp.status_code == 422
        assert resp.status_code == 422

    def test_ciclo_bom_indireto(self, client, material_chapa):
        """A → B → C → A deve ser rejeitado ao tentar adicionar A como filho de C."""
        # Cria A, B, C
        client.post(self.BASE, json={"codigo": "A", "nome": "A"})  # id=1
        client.post(self.BASE, json={"codigo": "B", "nome": "B"})  # id=2
        client.post(self.BASE, json={"codigo": "C", "nome": "C"})  # id=3

        # A → B
        client.post(
            f"{self.BASE}/1/itens",
            json={"componente_filho_id": 2, "quantidade": "1.0"},
        )
        # B → C
        client.post(
            f"{self.BASE}/2/itens",
            json={"componente_filho_id": 3, "quantidade": "1.0"},
        )
        # C → A (deve rejeitar: criaria ciclo)
        resp = client.post(
            f"{self.BASE}/3/itens",
            json={"componente_filho_id": 1, "quantidade": "1.0"},
        )
        assert resp.status_code == 422
        assert (
            "circular" in resp.json()["detail"].lower()
            or "ciclo" in resp.json()["detail"].lower()
        )

    def test_deletar_ficha_produto(self, client):
        client.post(self.BASE, json={"codigo": "PROD-001", "nome": "Placa"})
        assert client.delete(f"{self.BASE}/1").status_code == 204
        assert client.get(f"{self.BASE}/1").status_code == 404


# ── Fichas de Serviço ─────────────────────────────────────────────────────────


class TestFichaServico:
    BASE = "/api/v1/fichas-servico"
    BASE_EQ = "/api/v1/fichas-equipe"
    BASE_PROD = "/api/v1/fichas-produto"

    SERVICO_PAYLOAD = {
        "codigo": "SV-001",
        "nome": "Implantação Placa R-1",
        "tipo_servico": "VERTICAL",
        "unidade_medida": "un",
        "producao_diaria": "50.00",
    }

    def test_criar_ficha_servico(self, client):
        resp = client.post(self.BASE, json=self.SERVICO_PAYLOAD)
        assert resp.status_code == 201
        data = resp.json()
        assert data["tipo_servico"] == "VERTICAL"
        assert data["possui_recursos"] is False

    def test_listar_fichas_servico(self, client):
        client.post(self.BASE, json=self.SERVICO_PAYLOAD)
        assert len(client.get(self.BASE).json()) == 1

    def test_atualizar_ficha_servico(self, client):
        client.post(self.BASE, json=self.SERVICO_PAYLOAD)
        resp = client.put(f"{self.BASE}/1", json={"tipo_servico": "HORIZONTAL"})
        assert resp.json()["tipo_servico"] == "HORIZONTAL"

    def test_vincular_equipe(self, client, rh_encarregado):
        # Cria equipe com um item
        client.post(self.BASE_EQ, json={"codigo": "EQ-001", "nome": "Equipe SV"})
        client.post(
            f"{self.BASE_EQ}/1/itens",
            json={
                "tipo_recurso": "RH",
                "rh_id": rh_encarregado.id,
                "quantidade": "1.0",
            },
        )
        # Cria serviço
        client.post(self.BASE, json=self.SERVICO_PAYLOAD)
        # Vincula equipe
        resp = client.post(
            f"{self.BASE}/1/recursos",
            json={"ficha_equipe_id": 1, "quantidade": "1.0"},
        )
        assert resp.status_code == 201
        assert resp.json()["ficha_equipe_id"] == 1
        # Custo gravado > 0 (vem dos itens da equipe)
        assert Decimal(resp.json()["custo_unitario_gravado"]) > Decimal("0")

    def test_vincular_frota(self, client, frota_caminhao):
        client.post(self.BASE, json=self.SERVICO_PAYLOAD)
        resp = client.post(
            f"{self.BASE}/1/recursos",
            json={"frota_id": frota_caminhao.id, "quantidade": "1.0"},
        )
        assert resp.status_code == 201
        assert Decimal(resp.json()["custo_unitario_gravado"]) == Decimal("1200.0000")

    def test_vincular_produto(self, client, material_chapa):
        client.post(self.BASE_PROD, json={"codigo": "PROD-001", "nome": "Placa R-1"})
        client.post(
            f"{self.BASE_PROD}/1/itens",
            json={"material_id": material_chapa.id, "quantidade": "1.0"},
        )
        client.post(self.BASE, json=self.SERVICO_PAYLOAD)
        resp = client.post(
            f"{self.BASE}/1/recursos",
            json={"ficha_produto_id": 1, "quantidade": "1.0"},
        )
        assert resp.status_code == 201

    def test_vincular_recurso_seta_possui_recursos(self, client, frota_caminhao):
        client.post(self.BASE, json=self.SERVICO_PAYLOAD)
        client.post(
            f"{self.BASE}/1/recursos",
            json={"frota_id": frota_caminhao.id, "quantidade": "1.0"},
        )
        assert client.get(f"{self.BASE}/1").json()["possui_recursos"] is True

    def test_recurso_sem_fk_rejeitado(self, client):
        client.post(self.BASE, json=self.SERVICO_PAYLOAD)
        resp = client.post(f"{self.BASE}/1/recursos", json={"quantidade": "1.0"})
        assert resp.status_code == 422

    def test_recurso_dois_fk_rejeitado(
        self, client, frota_caminhao, ferramental_furadeira
    ):
        client.post(self.BASE, json=self.SERVICO_PAYLOAD)
        resp = client.post(
            f"{self.BASE}/1/recursos",
            json={
                "frota_id": frota_caminhao.id,
                "ferramental_id": ferramental_furadeira.id,
                "quantidade": "1.0",
            },
        )
        assert resp.status_code == 422

    def test_remover_recurso_atualiza_flag(self, client, frota_caminhao):
        client.post(self.BASE, json=self.SERVICO_PAYLOAD)
        r = client.post(
            f"{self.BASE}/1/recursos",
            json={"frota_id": frota_caminhao.id, "quantidade": "1.0"},
        )
        recurso_id = r.json()["id"]
        client.delete(f"{self.BASE}/1/recursos/{recurso_id}")
        assert client.get(f"{self.BASE}/1").json()["possui_recursos"] is False

    def test_deletar_ficha_servico(self, client):
        client.post(self.BASE, json=self.SERVICO_PAYLOAD)
        assert client.delete(f"{self.BASE}/1").status_code == 204
        assert client.get(f"{self.BASE}/1").status_code == 404
