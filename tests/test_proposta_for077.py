"""tests/test_proposta_for077.py — FOR-077 Fase 1 (backend gaps).

PATCH descrição de item (descricao_cliente), PUT /config completo,
endpoint GET /orcamentos/{id}/proposta com fallback ConfigSistema.
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
from backend.models.orcamento_models import Cliente, Orcamento, OrcamentoItem

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


def _criar_orcamento_com_item(db, *, status="rascunho", sufixo="1"):
    """Cria Cliente + Orcamento + 1 OrcamentoItem. Retorna (orc_id, item_id)."""
    c = Cliente(nome="Motiva Rodovias S.A.", cnpj_cpf="00.000.000/0001-91")
    db.add(c)
    db.flush()
    orc = Orcamento(
        numero=f"ORC-FOR077-{sufixo}",
        cliente_id=c.id,
        obra="Recapeamento SP-333",
        uf_execucao="SP",
        status=status,
    )
    db.add(orc)
    db.flush()
    item = OrcamentoItem(
        orcamento_id=orc.id,
        bloco="servicos",
        tipo_origem="manual",
        descricao="Fresagem (descrição interna de composição)",
        unidade="m2",
        quantidade=Decimal("100"),
        mod_fat="BDI-MAT+MO",
    )
    db.add(item)
    db.commit()
    return orc.id, item.id


class TestPatchDescricaoItem:
    def test_patch_grava_descricao_cliente(self, db_session):
        orc_id, item_id = _criar_orcamento_com_item(db_session)
        r = client.patch(
            f"/api/v1/orcamentos/{orc_id}/itens/{item_id}",
            json={"descricao": "Fresagem da pista existente"},
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["descricao_cliente"] == "Fresagem da pista existente"
        # composição preservada
        assert body["descricao"] == "Fresagem (descrição interna de composição)"

    def test_patch_campo_extra_retorna_422(self, db_session):
        orc_id, item_id = _criar_orcamento_com_item(db_session)
        r = client.patch(
            f"/api/v1/orcamentos/{orc_id}/itens/{item_id}",
            json={"descricao": "ok", "descricao_cliente": "tentativa direta"},
        )
        assert r.status_code == 422, r.text

    def test_patch_orcamento_congelado_retorna_403(self, db_session):
        orc_id, item_id = _criar_orcamento_com_item(db_session, status="aprovado")
        r = client.patch(
            f"/api/v1/orcamentos/{orc_id}/itens/{item_id}",
            json={"descricao": "nao deveria gravar"},
        )
        assert r.status_code == 403, r.text

    def test_patch_item_de_outro_orcamento_retorna_404(self, db_session):
        orc_id, item_id = _criar_orcamento_com_item(db_session)
        outro_orc_id, _ = _criar_orcamento_com_item(db_session, sufixo="2")
        # item_id pertence a orc_id, mas pedimos via outro_orc_id
        r = client.patch(
            f"/api/v1/orcamentos/{outro_orc_id}/itens/{item_id}",
            json={"descricao": "x"},
        )
        assert r.status_code == 404, r.text

    def test_patch_descricao_vazia_retorna_422(self, db_session):
        orc_id, item_id = _criar_orcamento_com_item(db_session)
        r = client.patch(
            f"/api/v1/orcamentos/{orc_id}/itens/{item_id}",
            json={"descricao": ""},
        )
        assert r.status_code == 422, r.text

    def test_patch_orcamento_inexistente_retorna_404(self):
        r = client.patch(
            "/api/v1/orcamentos/999999/itens/1",
            json={"descricao": "x"},
        )
        assert r.status_code == 404, r.text

    def test_patch_descricao_ausente_retorna_422(self, db_session):
        orc_id, item_id = _criar_orcamento_com_item(db_session)
        r = client.patch(
            f"/api/v1/orcamentos/{orc_id}/itens/{item_id}",
            json={},
        )
        assert r.status_code == 422, r.text


class TestPutConfigCompleto:
    def test_round_trip_campos_for077(self):
        payload = {
            "nome_empresa": "ALTA NOROESTE",
            "cnpj": "20.945.724/0001-15",
            "banco": "Bradesco",
            "agencia": "0110",
            "conta_corrente": "0287852-6",
            "diretor_cpf": "277.540.838-92",
            "contato_comercial_nome": "Milaini Carvalho Miranda",
            "contato_comercial_funcao": "Comercial",
            "contato_comercial_fone": "(18) 99683-6472",
            "contato_comercial_email": "comercial@altanoroeste.com.br",
            "garantia_retencao_padrao_pct": 5,
            "garantia_devolucao_padrao_dias": 60,
            "clausula_tributaria_padrao": "texto tributário",
            "reajustamento_padrao": "texto reajuste",
            "declaracoes_padrao": "linha1\nlinha2",
        }
        r = client.put("/api/v1/config", json=payload)
        assert r.status_code == 200, r.text
        d = client.get("/api/v1/config").json()
        assert d["cnpj"] == "20.945.724/0001-15"
        assert d["contato_comercial_email"] == "comercial@altanoroeste.com.br"
        assert str(d["garantia_retencao_padrao_pct"]) in ("5", "5.0", "5.00")
        assert d["garantia_devolucao_padrao_dias"] == 60
        assert d["declaracoes_padrao"] == "linha1\nlinha2"

    def test_limpar_campo_via_null(self):
        client.put("/api/v1/config", json={"banco": "Bradesco"})
        assert client.get("/api/v1/config").json()["banco"] == "Bradesco"
        # exclude_unset: enviar null limpa; omitir não toca
        client.put("/api/v1/config", json={"banco": None})
        assert client.get("/api/v1/config").json()["banco"] is None

    def test_omitir_campo_nao_apaga(self):
        client.put("/api/v1/config", json={"banco": "Bradesco", "agencia": "0110"})
        client.put("/api/v1/config", json={"agencia": "0220"})
        d = client.get("/api/v1/config").json()
        assert d["agencia"] == "0220"
        assert d["banco"] == "Bradesco"  # não foi tocado
