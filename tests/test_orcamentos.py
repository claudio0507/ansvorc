"""
tests/test_orcamentos.py — CRUD orçamentos + endpoint /calcular.

Padrão: SQLite in-memory com StaticPool, dependency_overrides[get_db].
Todos os valores Decimal; sem float.
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
from backend.models.bd_models import BdBDI
from backend.models.ficha_models import FichaProduto, FichaServico
from backend.models.orcamento_models import Cliente, Orcamento, OrcamentoItem

# ── Engine in-memory compartilhado ────────────────────────────────────────────

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
    # Garante que ESTE engine está ativo para cada teste, independente da ordem
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)
    app.dependency_overrides.pop(get_db, None)


# ── Fixtures de dados base ────────────────────────────────────────────────────


@pytest.fixture
def db_session():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def cliente_id(db_session):
    c = Cliente(razao_social="Motiva Rodovias S.A.", uf_sede="PR")
    db_session.add(c)
    db_session.commit()
    db_session.refresh(c)
    return c.id


@pytest.fixture
def bdi_rows(db_session):
    """Registros bd_BDI para todos os MOD FAT."""
    rows = [
        BdBDI(
            modalidade="BDI-MAT+MO",
            adm_percentual=Decimal("0.1300"),
            custo_financeiro_percentual=Decimal("0.0150"),
            pis_cofins_percentual=Decimal("0.0365"),
            issqn_pr_percentual=Decimal("0.0350"),
            issqn_sp_percentual=Decimal("0.0500"),
            icms_percentual=Decimal("0.0000"),
            ativo=True,
        ),
        BdBDI(
            modalidade="BDI+ICMS",
            adm_percentual=Decimal("0.1300"),
            custo_financeiro_percentual=Decimal("0.0150"),
            pis_cofins_percentual=Decimal("0.0925"),
            issqn_pr_percentual=Decimal("0.0350"),
            issqn_sp_percentual=Decimal("0.0500"),
            icms_percentual=Decimal("0.1200"),
            ativo=True,
        ),
        BdBDI(
            modalidade="BDI-MO",
            adm_percentual=Decimal("0.1300"),
            custo_financeiro_percentual=Decimal("0.0150"),
            pis_cofins_percentual=Decimal("0.0365"),
            issqn_pr_percentual=Decimal("0.0350"),
            issqn_sp_percentual=Decimal("0.0500"),
            icms_percentual=Decimal("0.0000"),
            ativo=True,
        ),
        BdBDI(
            modalidade="FAT DIR SIMP",
            adm_percentual=Decimal("0.1300"),
            custo_financeiro_percentual=Decimal("0.0150"),
            pis_cofins_percentual=Decimal("0.0365"),
            issqn_pr_percentual=Decimal("0.0350"),
            issqn_sp_percentual=Decimal("0.0500"),
            icms_percentual=Decimal("0.0000"),
            ativo=True,
        ),
    ]
    for r in rows:
        db_session.add(r)
    db_session.commit()


@pytest.fixture
def ficha_servico_id(db_session):
    fs = FichaServico(
        codigo="FS-001",
        nome="Implantação de placas",
        tipo_servico="VERTICAL",
        unidade_medida="un",
        producao_diaria=Decimal("10"),
    )
    db_session.add(fs)
    db_session.commit()
    db_session.refresh(fs)
    return fs.id


@pytest.fixture
def ficha_produto_id(db_session):
    fp = FichaProduto(
        codigo="FP-001",
        nome="Chapa galvanizada R-1",
        unidade_medida="un",
    )
    db_session.add(fp)
    db_session.commit()
    db_session.refresh(fp)
    return fp.id


@pytest.fixture
def orcamento_id(cliente_id):
    resp = client.post(
        "/api/v1/orcamentos",
        json={
            "numero_proposta": "PROP-001",
            "cliente_id": cliente_id,
            "uf_execucao": "PR",
            "beneficio_reidi": False,
        },
    )
    assert resp.status_code == 201
    return resp.json()["id"]


# ── Clientes ──────────────────────────────────────────────────────────────────


class TestClientes:

    def test_criar_cliente(self):
        resp = client.post(
            "/api/v1/clientes",
            json={
                "razao_social": "Alta Noroeste S.A.",
                "cnpj": "00.000.000/0001-91",
                "uf_sede": "PR",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["razao_social"] == "Alta Noroeste S.A."

    def test_listar_clientes(self, cliente_id):
        resp = client.get("/api/v1/clientes")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_obter_cliente_nao_encontrado(self):
        resp = client.get("/api/v1/clientes/9999")
        assert resp.status_code == 404


# ── CRUD Orçamentos ───────────────────────────────────────────────────────────


class TestOrcamentosCRUD:

    def test_criar_orcamento(self, cliente_id):
        resp = client.post(
            "/api/v1/orcamentos",
            json={
                "numero_proposta": "PROP-CRUD-01",
                "cliente_id": cliente_id,
                "uf_execucao": "PR",
                "beneficio_reidi": False,
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "rascunho"
        assert data["uf_execucao"] == "PR"
        assert data["beneficio_reidi"] is False

    def test_listar_orcamentos(self, orcamento_id):
        resp = client.get("/api/v1/orcamentos")
        assert resp.status_code == 200
        assert any(o["id"] == orcamento_id for o in resp.json())

    def test_atualizar_orcamento_rascunho(self, orcamento_id):
        resp = client.put(
            f"/api/v1/orcamentos/{orcamento_id}",
            json={
                "uf_execucao": "SP",
                "beneficio_reidi": True,
            },
        )
        assert resp.status_code == 200
        assert resp.json()["uf_execucao"] == "SP"
        assert resp.json()["beneficio_reidi"] is True

    def test_excluir_orcamento_rascunho(self, cliente_id):
        resp = client.post(
            "/api/v1/orcamentos",
            json={
                "numero_proposta": "PROP-DEL",
                "cliente_id": cliente_id,
                "uf_execucao": "PR",
            },
        )
        oid = resp.json()["id"]
        resp = client.delete(f"/api/v1/orcamentos/{oid}")
        assert resp.status_code == 204

    def test_criar_orcamento_cliente_inexistente(self):
        resp = client.post(
            "/api/v1/orcamentos",
            json={
                "numero_proposta": "PROP-X",
                "cliente_id": 99999,
                "uf_execucao": "PR",
            },
        )
        assert resp.status_code == 404


# ── Itens ─────────────────────────────────────────────────────────────────────


class TestOrcamentoItens:

    def test_adicionar_item_servico(self, orcamento_id, ficha_servico_id):
        resp = client.post(
            f"/api/v1/orcamentos/{orcamento_id}/itens",
            json={
                "bloco": "servicos",
                "ficha_servico_id": ficha_servico_id,
                "descricao": "Implantação de placas R-1",
                "unidade_medida": "un",
                "quantidade": "100",
                "mod_fat": "BDI-MAT+MO",
                "margem_percentual": "0.10",
                "custo_direto_unitario": "409.32",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["bloco"] == "servicos"
        assert resp.json()["ficha_servico_id"] == ficha_servico_id

    def test_adicionar_item_produto(self, orcamento_id, ficha_produto_id):
        resp = client.post(
            f"/api/v1/orcamentos/{orcamento_id}/itens",
            json={
                "bloco": "produtos",
                "ficha_produto_id": ficha_produto_id,
                "descricao": "Chapa galvanizada R-1",
                "unidade_medida": "un",
                "quantidade": "50",
                "mod_fat": "BDI+ICMS",
                "margem_percentual": "0.12",
                "custo_direto_unitario": "185.00",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["bloco"] == "produtos"

    def test_adicionar_item_operacional(self, orcamento_id):
        resp = client.post(
            f"/api/v1/orcamentos/{orcamento_id}/itens",
            json={
                "bloco": "operacional",
                "descricao": "Alojamento Passo Fundo",
                "unidade_medida": "Mês",
                "quantidade": "1",
                "mod_fat": "-",
                "margem_percentual": "0",
                "custo_direto_unitario": "57000.00",
            },
        )
        assert resp.status_code == 201

    def test_rejeitar_ficha_servico_e_produto_simultaneos(
        self, orcamento_id, ficha_servico_id, ficha_produto_id
    ):
        resp = client.post(
            f"/api/v1/orcamentos/{orcamento_id}/itens",
            json={
                "bloco": "servicos",
                "ficha_servico_id": ficha_servico_id,
                "ficha_produto_id": ficha_produto_id,
                "descricao": "Inválido",
                "unidade_medida": "un",
                "quantidade": "1",
                "mod_fat": "BDI-MO",
                "margem_percentual": "0.10",
                "custo_direto_unitario": "100",
            },
        )
        assert resp.status_code == 422

    def test_listar_itens(self, orcamento_id, ficha_servico_id):
        client.post(
            f"/api/v1/orcamentos/{orcamento_id}/itens",
            json={
                "bloco": "servicos",
                "ficha_servico_id": ficha_servico_id,
                "descricao": "Serviço X",
                "unidade_medida": "m²",
                "quantidade": "10",
                "mod_fat": "BDI-MAT+MO",
                "margem_percentual": "0.10",
                "custo_direto_unitario": "38.50",
            },
        )
        resp = client.get(f"/api/v1/orcamentos/{orcamento_id}/itens")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_remover_item(self, orcamento_id, ficha_servico_id):
        r = client.post(
            f"/api/v1/orcamentos/{orcamento_id}/itens",
            json={
                "bloco": "servicos",
                "ficha_servico_id": ficha_servico_id,
                "descricao": "Serviço para deletar",
                "unidade_medida": "un",
                "quantidade": "5",
                "mod_fat": "BDI-MAT+MO",
                "margem_percentual": "0.10",
                "custo_direto_unitario": "100",
            },
        )
        item_id = r.json()["id"]
        resp = client.delete(f"/api/v1/orcamentos/{orcamento_id}/itens/{item_id}")
        assert resp.status_code == 204


# ── Guard: orçamento aprovado ─────────────────────────────────────────────────


class TestGuardAprovado:

    def _aprovar(self, orcamento_id):
        """Força o status para 'aprovado' via PUT seguindo a máquina de estados."""
        r1 = client.put(
            f"/api/v1/orcamentos/{orcamento_id}", json={"status": "enviado"}
        )
        assert r1.status_code == 200, r1.json()
        r2 = client.put(
            f"/api/v1/orcamentos/{orcamento_id}", json={"status": "aprovado"}
        )
        assert r2.status_code == 200, r2.json()
        assert r2.json()["status"] == "aprovado"

    def test_nao_pode_editar_item_de_orcamento_aprovado(
        self, orcamento_id, ficha_servico_id
    ):
        r = client.post(
            f"/api/v1/orcamentos/{orcamento_id}/itens",
            json={
                "bloco": "servicos",
                "ficha_servico_id": ficha_servico_id,
                "descricao": "Serviço",
                "unidade_medida": "un",
                "quantidade": "10",
                "mod_fat": "BDI-MAT+MO",
                "margem_percentual": "0.10",
                "custo_direto_unitario": "200",
            },
        )
        item_id = r.json()["id"]
        self._aprovar(orcamento_id)

        resp = client.put(
            f"/api/v1/orcamentos/{orcamento_id}/itens/{item_id}",
            json={"quantidade": "99"},
        )
        assert resp.status_code == 403

    def test_nao_pode_adicionar_item_em_orcamento_aprovado(
        self, orcamento_id, ficha_servico_id
    ):
        self._aprovar(orcamento_id)
        resp = client.post(
            f"/api/v1/orcamentos/{orcamento_id}/itens",
            json={
                "bloco": "servicos",
                "ficha_servico_id": ficha_servico_id,
                "descricao": "Novo item proibido",
                "unidade_medida": "un",
                "quantidade": "1",
                "mod_fat": "BDI-MAT+MO",
                "margem_percentual": "0.10",
                "custo_direto_unitario": "100",
            },
        )
        assert resp.status_code == 403

    def test_nao_pode_deletar_item_de_orcamento_aprovado(
        self, orcamento_id, ficha_servico_id
    ):
        r = client.post(
            f"/api/v1/orcamentos/{orcamento_id}/itens",
            json={
                "bloco": "servicos",
                "ficha_servico_id": ficha_servico_id,
                "descricao": "Serviço",
                "unidade_medida": "un",
                "quantidade": "10",
                "mod_fat": "BDI-MAT+MO",
                "margem_percentual": "0.10",
                "custo_direto_unitario": "200",
            },
        )
        item_id = r.json()["id"]
        self._aprovar(orcamento_id)

        resp = client.delete(f"/api/v1/orcamentos/{orcamento_id}/itens/{item_id}")
        assert resp.status_code == 403

    def test_nao_pode_atualizar_orcamento_aprovado(self, orcamento_id):
        self._aprovar(orcamento_id)
        resp = client.put(
            f"/api/v1/orcamentos/{orcamento_id}", json={"uf_execucao": "SP"}
        )
        assert resp.status_code == 403

    def test_nao_pode_excluir_orcamento_aprovado(self, orcamento_id):
        self._aprovar(orcamento_id)
        resp = client.delete(f"/api/v1/orcamentos/{orcamento_id}")
        assert resp.status_code == 403


# ── Endpoint /calcular ────────────────────────────────────────────────────────


class TestCalcular:

    def _adicionar_item(
        self,
        orcamento_id,
        bloco,
        mod_fat,
        margem,
        custo,
        qty=100,
        ficha_servico_id=None,
        ficha_produto_id=None,
        descricao="Item",
    ):
        payload = {
            "bloco": bloco,
            "descricao": descricao,
            "unidade_medida": "un",
            "quantidade": str(qty),
            "mod_fat": mod_fat,
            "margem_percentual": str(margem),
            "custo_direto_unitario": str(custo),
        }
        if ficha_servico_id:
            payload["ficha_servico_id"] = ficha_servico_id
        if ficha_produto_id:
            payload["ficha_produto_id"] = ficha_produto_id
        r = client.post(f"/api/v1/orcamentos/{orcamento_id}/itens", json=payload)
        assert r.status_code == 201, r.text
        return r.json()["id"]

    def test_calcular_bdi_mat_mo_pr_sem_reidi(
        self, orcamento_id, bdi_rows, ficha_servico_id
    ):
        """BDI-MAT+MO, PR, sem REIDI, margem 10% → BDI ≈ 35.88%"""
        self._adicionar_item(
            orcamento_id,
            "servicos",
            "BDI-MAT+MO",
            "0.10",
            "409.32",
            qty=100,
            ficha_servico_id=ficha_servico_id,
        )
        resp = client.post(f"/api/v1/orcamentos/{orcamento_id}/calcular")
        assert resp.status_code == 200
        data = resp.json()

        item = data["itens"][0]
        bdi_pct = Decimal(str(item["bdi_taxa"])) * 100
        assert abs(bdi_pct - Decimal("35.88")) < Decimal("0.01")

    def test_calcular_bdi_mat_mo_pr_com_reidi(
        self, cliente_id, bdi_rows, ficha_servico_id
    ):
        """BDI-MAT+MO, PR, com REIDI, margem 10% → BDI ≈ 30.74%"""
        resp = client.post(
            "/api/v1/orcamentos",
            json={
                "numero_proposta": "PROP-REIDI",
                "cliente_id": cliente_id,
                "uf_execucao": "PR",
                "beneficio_reidi": True,
            },
        )
        orc_id = resp.json()["id"]

        self._adicionar_item(
            orc_id,
            "servicos",
            "BDI-MAT+MO",
            "0.10",
            "409.32",
            qty=100,
            ficha_servico_id=ficha_servico_id,
        )
        resp = client.post(f"/api/v1/orcamentos/{orc_id}/calcular")
        assert resp.status_code == 200
        data = resp.json()
        assert data["beneficio_reidi"] is True

        item = data["itens"][0]
        bdi_pct = Decimal(str(item["bdi_taxa"])) * 100
        assert abs(bdi_pct - Decimal("30.74")) < Decimal("0.01")

    def test_calcular_com_fator_k(
        self, orcamento_id, bdi_rows, ficha_servico_id, ficha_produto_id
    ):
        """Fator K: 1 item operacional diluído em 3 faturáveis."""
        self._adicionar_item(
            orcamento_id,
            "servicos",
            "BDI-MAT+MO",
            "0.10",
            "409.32",
            qty=100,
            ficha_servico_id=ficha_servico_id,
            descricao="Serviço A",
        )
        self._adicionar_item(
            orcamento_id,
            "servicos",
            "BDI-MAT+MO",
            "0.12",
            "158.90",
            qty=45,
            ficha_servico_id=ficha_servico_id,
            descricao="Serviço B",
        )
        self._adicionar_item(
            orcamento_id,
            "produtos",
            "BDI+ICMS",
            "0.10",
            "185.00",
            qty=20,
            ficha_produto_id=ficha_produto_id,
            descricao="Produto C",
        )
        self._adicionar_item(
            orcamento_id,
            "operacional",
            "-",
            "0",
            "57000.00",
            qty=1,
            descricao="Alojamento",
        )

        resp = client.post(f"/api/v1/orcamentos/{orcamento_id}/calcular")
        assert resp.status_code == 200
        data = resp.json()

        # Total proposta deve ser maior que subtotal faturável
        subtotal = Decimal(str(data["subtotal_faturavel"]))
        total_nf = Decimal(str(data["total_nao_faturavel"]))
        total = Decimal(str(data["total_proposta"]))
        assert total > subtotal
        assert total_nf > Decimal("0")
        assert abs(total - (subtotal + total_nf)) < Decimal("0.01")

        # Fator K deve ser > 0
        fk = Decimal(str(data["fator_k_percentual"]))
        assert fk > Decimal("0")

        # Itens faturáveis devem ter peso_rateio e rateio_absorvido
        fat_itens = [i for i in data["itens"] if i["bloco"] in ("servicos", "produtos")]
        for fi in fat_itens:
            assert Decimal(str(fi["rateio_absorvido"])) >= Decimal("0")
            assert Decimal(str(fi["peso_rateio"])) > Decimal("0")

        # Soma dos pesos deve ser ~100%
        soma_pesos = sum(Decimal(str(fi["peso_rateio"])) for fi in fat_itens)
        assert abs(soma_pesos - Decimal("100")) < Decimal("0.10")

    def test_calcular_sem_itens_retorna_422(self, orcamento_id):
        resp = client.post(f"/api/v1/orcamentos/{orcamento_id}/calcular")
        assert resp.status_code == 422

    def test_calcular_atualiza_totais_no_orcamento(
        self, orcamento_id, bdi_rows, ficha_servico_id
    ):
        self._adicionar_item(
            orcamento_id,
            "servicos",
            "BDI-MAT+MO",
            "0.10",
            "100.00",
            qty=10,
            ficha_servico_id=ficha_servico_id,
        )
        client.post(f"/api/v1/orcamentos/{orcamento_id}/calcular")

        resp = client.get(f"/api/v1/orcamentos/{orcamento_id}")
        data = resp.json()
        assert Decimal(str(data["total_proposta"])) > Decimal("0")
        assert Decimal(str(data["total_custo_direto"])) > Decimal("0")
        assert Decimal(str(data["margem_liquida_real"])) > Decimal("0")
