"""tests/test_status_transicoes.py — funil de 6 estados + freeze de itens.

Status agora é um funil de 6 estados; transições passam por
``PUT /api/v1/orcamentos/{id}`` com corpo ``{"status": "<novo>"}``.
O antigo ``POST /orcamentos/{id}/aprovar`` foi REMOVIDO.

Infra replicada de test_orcamentos.py (engine in-memory + client sponsor +
setup_db autouse), pois as fixtures de lá NÃO estão em conftest.
"""

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.auth import criar_token
from backend.database import Base, get_db
from backend.main import app
from backend.models.ficha_models import FichaServico
from backend.models.orcamento_models import Cliente

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


_TOKEN = criar_token(usuario_id=9999, papel="sponsor")
client = TestClient(app, headers={"Authorization": f"Bearer {_TOKEN}"})


@pytest.fixture(autouse=True)
def setup_db():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def db_session():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def cliente_id(db_session):
    c = Cliente(nome="Motiva Rodovias S.A.", cnpj_cpf="00.000.000/0001-91")
    db_session.add(c)
    db_session.commit()
    db_session.refresh(c)
    return c.id


@pytest.fixture
def ficha_servico_id(db_session):
    fs = FichaServico(
        codigo="FS-001",
        nome="Implantação de placas",
        seguimento="VERTICAL",
        produtividade_dia=Decimal("10"),
        unidade="un",
        custo_unitario=Decimal("409.32"),
        possui_ficha=True,
    )
    db_session.add(fs)
    db_session.commit()
    db_session.refresh(fs)
    return fs.id


@pytest.fixture
def orcamento_id(cliente_id):
    resp = client.post(
        "/api/v1/orcamentos",
        json={"numero": "PROP-001", "cliente_id": cliente_id, "uf_execucao": "PR"},
    )
    assert resp.status_code == 201
    return resp.json()["id"]


def _set_status(orc_id, novo):
    return client.put(f"/api/v1/orcamentos/{orc_id}", json={"status": novo})


class TestTransicoes:
    def test_rascunho_para_enviado_ok(self, orcamento_id):
        r = _set_status(orcamento_id, "enviado")
        assert r.status_code == 200
        assert r.json()["status"] == "enviado"

    def test_rascunho_para_fechado_invalido(self, orcamento_id):
        r = _set_status(orcamento_id, "fechado")
        assert r.status_code == 422

    def test_enviado_para_perdida_ok(self, orcamento_id):
        _set_status(orcamento_id, "enviado")
        r = _set_status(orcamento_id, "perdida")
        assert r.status_code == 200

    def test_perdida_e_terminal(self, orcamento_id):
        _set_status(orcamento_id, "enviado")
        _set_status(orcamento_id, "perdida")
        r = _set_status(orcamento_id, "rascunho")
        assert r.status_code == 422

    def test_reprovado_reabre_para_rascunho(self, orcamento_id):
        _set_status(orcamento_id, "enviado")
        _set_status(orcamento_id, "reprovado")
        r = _set_status(orcamento_id, "rascunho")
        assert r.status_code == 200

    def test_freeze_bloqueia_item_em_enviado(self, orcamento_id, ficha_servico_id):
        _set_status(orcamento_id, "enviado")
        r = client.post(
            f"/api/v1/orcamentos/{orcamento_id}/itens",
            json={
                "bloco": "servicos",
                "ficha_servico_id": ficha_servico_id,
                "descricao": "X",
                "unidade": "un",
                "quantidade": "1",
                "mod_fat": "BDI-MO",
                "margem_lucro": "10",
            },
        )
        assert r.status_code == 403
