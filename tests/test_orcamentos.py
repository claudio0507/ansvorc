"""tests/test_orcamentos.py — CRM + orçamentos + /calcular + desconto + versão.

Alinhado a docs/02 (schema) e docs/04 (motor). Custos de itens faturáveis vêm da
ficha (custo_unitario / custo_total). margem_lucro é percentual (10 = 10%).
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
from backend.models.bd_models import BdBDI, BdEstrutura
from backend.models.ficha_models import FichaProduto, FichaServico
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


def _bdi(modalidade, uf, *, pis, cofins, issqn, icms):
    return BdBDI(
        modalidade=modalidade,
        uf=uf,
        pis=pis,
        cofins=cofins,
        issqn=issqn,
        icms=icms,
        custo_financeiro=Decimal("0.0150"),
        despesas_adm=Decimal("0.1300"),
        ativo=True,
    )


@pytest.fixture
def bdi_rows(db_session):
    """bd_BDI para PR (todos os MOD FAT) — alíquotas discretas docs/04."""
    z = Decimal("0")
    pis, cof, iss = Decimal("0.0065"), Decimal("0.0300"), Decimal("0.0350")
    db_session.add_all(
        [
            _bdi("BDI-MAT+MO", "PR", pis=pis, cofins=cof, issqn=iss, icms=z),
            _bdi("BDI-MO", "PR", pis=pis, cofins=cof, issqn=iss, icms=z),
            _bdi("BDI+ICMS", "PR", pis=pis, cofins=cof, issqn=z, icms=Decimal("0.12")),
            _bdi("FAT DIR SIMP", "PR", pis=z, cofins=z, issqn=z, icms=z),
        ]
    )
    db_session.commit()


@pytest.fixture
def ficha_servico_id(db_session):
    """Serviço com custo_unitario=409.32 (usado nos testes de BDI)."""
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
def ficha_servico_b_id(db_session):
    fs = FichaServico(
        codigo="FS-002",
        nome="Pintura",
        seguimento="HORIZONTAL",
        produtividade_dia=Decimal("700"),
        unidade="m²",
        custo_unitario=Decimal("158.90"),
        possui_ficha=True,
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
        unidade="un",
        custo_total=Decimal("185.00"),
        possui_ficha=True,
    )
    db_session.add(fp)
    db_session.commit()
    db_session.refresh(fp)
    return fp.id


@pytest.fixture
def estrutura_aloj(db_session):
    e = BdEstrutura(
        item="Alojamento Passo Fundo",
        unidade="Mês",
        tipo="Moradia",
        valor_unitario=Decimal("57000.00"),
    )
    db_session.add(e)
    db_session.commit()


@pytest.fixture
def orcamento_id(cliente_id):
    resp = client.post(
        "/api/v1/orcamentos",
        json={"numero": "PROP-001", "cliente_id": cliente_id, "uf_execucao": "PR"},
    )
    assert resp.status_code == 201
    return resp.json()["id"]


# ── Clientes ──────────────────────────────────────────────────────────────────


class TestClientes:
    def test_criar_cliente(self):
        resp = client.post(
            "/api/v1/clientes",
            json={"nome": "alta noroeste s.a.", "cnpj_cpf": "00.000.000/0001-91"},
        )
        assert resp.status_code == 201
        assert resp.json()["nome"] == "Alta noroeste s.a."  # capitalizado

    def test_listar_clientes(self, cliente_id):
        assert len(client.get("/api/v1/clientes").json()) >= 1

    def test_obter_cliente_nao_encontrado(self):
        assert client.get("/api/v1/clientes/9999").status_code == 404


# ── CRUD Orçamentos ───────────────────────────────────────────────────────────


class TestOrcamentosCRUD:
    def test_criar_orcamento(self, cliente_id):
        resp = client.post(
            "/api/v1/orcamentos",
            json={
                "numero": "PROP-CRUD-01",
                "cliente_id": cliente_id,
                "uf_execucao": "PR",
            },
        )
        assert resp.status_code == 201
        d = resp.json()
        assert d["status"] == "rascunho"
        assert d["versao"] == 1
        assert d["desconto_percentual"] == "0.00"

    def test_atualizar_com_desconto(self, orcamento_id):
        resp = client.put(
            f"/api/v1/orcamentos/{orcamento_id}",
            json={"uf_execucao": "SP", "desconto_percentual": "5.00"},
        )
        assert resp.status_code == 200
        assert resp.json()["uf_execucao"] == "SP"
        assert resp.json()["desconto_percentual"] == "5.00"

    def test_busca_por_numero(self, orcamento_id):
        resp = client.get("/api/v1/orcamentos?busca=PROP-001")
        assert resp.status_code == 200
        assert any(o["id"] == orcamento_id for o in resp.json())

    def test_excluir_rascunho(self, cliente_id):
        oid = client.post(
            "/api/v1/orcamentos",
            json={"numero": "PROP-DEL", "cliente_id": cliente_id, "uf_execucao": "PR"},
        ).json()["id"]
        assert client.delete(f"/api/v1/orcamentos/{oid}").status_code == 204

    def test_cliente_inexistente(self):
        resp = client.post(
            "/api/v1/orcamentos",
            json={"numero": "PROP-X", "cliente_id": 99999, "uf_execucao": "PR"},
        )
        assert resp.status_code == 404


# ── Itens (custo automático da ficha) ─────────────────────────────────────────


class TestOrcamentoItens:
    def test_item_servico_puxa_custo_da_ficha(self, orcamento_id, ficha_servico_id):
        resp = client.post(
            f"/api/v1/orcamentos/{orcamento_id}/itens",
            json={
                "bloco": "servicos",
                "ficha_servico_id": ficha_servico_id,
                "descricao": "Implantação de placas",
                "unidade": "un",
                "quantidade": "100",
                "mod_fat": "BDI-MAT+MO",
                "margem_lucro": "10",
            },
        )
        assert resp.status_code == 201
        d = resp.json()
        assert d["tipo_origem"] == "servico"
        # custo veio da ficha (409.32), não digitado
        assert Decimal(d["custo_direto_unitario"]) == Decimal("409.3200")
        assert d["unidade"] == "un"  # da ficha

    def test_item_produto_puxa_custo_total(self, orcamento_id, ficha_produto_id):
        resp = client.post(
            f"/api/v1/orcamentos/{orcamento_id}/itens",
            json={
                "bloco": "produtos",
                "ficha_produto_id": ficha_produto_id,
                "descricao": "Chapa",
                "unidade": "un",
                "quantidade": "50",
                "mod_fat": "BDI+ICMS",
                "margem_lucro": "12",
            },
        )
        assert resp.status_code == 201
        assert Decimal(resp.json()["custo_direto_unitario"]) == Decimal("185.0000")

    def test_item_operacional_puxa_estrutura(self, orcamento_id, estrutura_aloj):
        resp = client.post(
            f"/api/v1/orcamentos/{orcamento_id}/itens",
            json={
                "bloco": "operacional",
                "descricao": "Alojamento Passo Fundo",
                "unidade": "Mês",
                "quantidade": "1",
                "mod_fat": "-",
                "margem_lucro": "0",
            },
        )
        assert resp.status_code == 201
        assert Decimal(resp.json()["custo_direto_unitario"]) == Decimal("57000.0000")

    def test_item_manual_usa_custo_digitado(self, orcamento_id):
        resp = client.post(
            f"/api/v1/orcamentos/{orcamento_id}/itens",
            json={
                "bloco": "excepcionais",
                "descricao": "Custo manual",
                "unidade": "vb",
                "quantidade": "1",
                "mod_fat": "-",
                "margem_lucro": "0",
                "custo_direto_unitario": "1234.56",
            },
        )
        assert resp.status_code == 201
        d = resp.json()
        assert Decimal(d["custo_direto_unitario"]) == Decimal("1234.5600")
        assert d["flag_aprovacao"] is True  # excepcional exige aprovação

    def test_servico_sem_ficha_bloqueado(self, orcamento_id, db_session):
        fs = FichaServico(
            codigo="FS-NF",
            nome="Sem ficha",
            seguimento="EPS",
            produtividade_dia=Decimal("1"),
            unidade="un",
            custo_unitario=Decimal("0"),
            possui_ficha=False,
        )
        db_session.add(fs)
        db_session.commit()
        db_session.refresh(fs)
        resp = client.post(
            f"/api/v1/orcamentos/{orcamento_id}/itens",
            json={
                "bloco": "servicos",
                "ficha_servico_id": fs.id,
                "descricao": "X",
                "unidade": "un",
                "quantidade": "1",
                "mod_fat": "BDI-MO",
                "margem_lucro": "10",
            },
        )
        assert resp.status_code == 422

    def test_rejeitar_servico_e_produto_juntos(
        self, orcamento_id, ficha_servico_id, ficha_produto_id
    ):
        resp = client.post(
            f"/api/v1/orcamentos/{orcamento_id}/itens",
            json={
                "bloco": "servicos",
                "ficha_servico_id": ficha_servico_id,
                "ficha_produto_id": ficha_produto_id,
                "descricao": "Inválido",
                "unidade": "un",
                "quantidade": "1",
                "mod_fat": "BDI-MO",
                "margem_lucro": "10",
            },
        )
        assert resp.status_code == 422


# ── Guard: orçamento aprovado ─────────────────────────────────────────────────


class TestGuardAprovado:
    def _aprovar(self, oid):
        assert (
            client.put(
                f"/api/v1/orcamentos/{oid}", json={"status": "enviado"}
            ).status_code
            == 200
        )
        r = client.put(f"/api/v1/orcamentos/{oid}", json={"status": "aprovado"})
        assert r.status_code == 200
        assert r.json()["status"] == "aprovado"
        assert r.json()["aprovado_em"] is not None

    def _add(self, oid, fs_id):
        return client.post(
            f"/api/v1/orcamentos/{oid}/itens",
            json={
                "bloco": "servicos",
                "ficha_servico_id": fs_id,
                "descricao": "Serviço",
                "unidade": "un",
                "quantidade": "10",
                "mod_fat": "BDI-MAT+MO",
                "margem_lucro": "10",
            },
        ).json()["id"]

    def test_nao_edita_item_aprovado(self, orcamento_id, ficha_servico_id):
        item_id = self._add(orcamento_id, ficha_servico_id)
        self._aprovar(orcamento_id)
        resp = client.put(
            f"/api/v1/orcamentos/{orcamento_id}/itens/{item_id}",
            json={"quantidade": "99"},
        )
        assert resp.status_code == 403

    def test_nao_adiciona_item_aprovado(self, orcamento_id, ficha_servico_id):
        self._aprovar(orcamento_id)
        resp = client.post(
            f"/api/v1/orcamentos/{orcamento_id}/itens",
            json={
                "bloco": "servicos",
                "ficha_servico_id": ficha_servico_id,
                "descricao": "X",
                "unidade": "un",
                "quantidade": "1",
                "mod_fat": "BDI-MAT+MO",
                "margem_lucro": "10",
            },
        )
        assert resp.status_code == 403

    def test_nao_exclui_aprovado(self, orcamento_id):
        self._aprovar(orcamento_id)
        assert client.delete(f"/api/v1/orcamentos/{orcamento_id}").status_code == 403


# ── Versionamento (reabrir) ───────────────────────────────────────────────────


class TestVersionamento:
    def test_reabrir_cria_nova_versao(self, orcamento_id, ficha_servico_id):
        client.post(
            f"/api/v1/orcamentos/{orcamento_id}/itens",
            json={
                "bloco": "servicos",
                "ficha_servico_id": ficha_servico_id,
                "descricao": "Serviço",
                "unidade": "un",
                "quantidade": "10",
                "mod_fat": "BDI-MAT+MO",
                "margem_lucro": "10",
            },
        )
        client.put(f"/api/v1/orcamentos/{orcamento_id}", json={"status": "enviado"})
        client.put(f"/api/v1/orcamentos/{orcamento_id}", json={"status": "aprovado"})

        resp = client.post(f"/api/v1/orcamentos/{orcamento_id}/reabrir")
        assert resp.status_code == 201
        nova = resp.json()
        assert nova["versao"] == 2
        assert nova["orcamento_origem_id"] == orcamento_id
        assert nova["status"] == "rascunho"
        # itens copiados
        itens = client.get(f"/api/v1/orcamentos/{nova['id']}/itens").json()
        assert len(itens) == 1
        # original permanece aprovado (imutável)
        orig = client.get(f"/api/v1/orcamentos/{orcamento_id}").json()
        assert orig["status"] == "aprovado"

    def test_reabrir_so_aprovado(self, orcamento_id):
        resp = client.post(f"/api/v1/orcamentos/{orcamento_id}/reabrir")
        assert resp.status_code == 422


# ── Endpoint /calcular ────────────────────────────────────────────────────────


class TestCalcular:
    def _add(
        self,
        oid,
        bloco,
        mod_fat,
        margem,
        qty,
        fs=None,
        fp=None,
        custo=None,
        desc="Item",
    ):
        payload = {
            "bloco": bloco,
            "descricao": desc,
            "unidade": "un",
            "quantidade": str(qty),
            "mod_fat": mod_fat,
            "margem_lucro": str(margem),
        }
        if fs:
            payload["ficha_servico_id"] = fs
        if fp:
            payload["ficha_produto_id"] = fp
        if custo is not None:
            payload["custo_direto_unitario"] = str(custo)
        r = client.post(f"/api/v1/orcamentos/{oid}/itens", json=payload)
        assert r.status_code == 201, r.text
        return r.json()["id"]

    def test_bdi_mat_mo_pr_sem_reidi(self, orcamento_id, bdi_rows, ficha_servico_id):
        """BDI-MAT+MO, PR, margem 10% → BDI ≈ 35.88% (docs/04)."""
        self._add(orcamento_id, "servicos", "BDI-MAT+MO", 10, 100, fs=ficha_servico_id)
        resp = client.post(f"/api/v1/orcamentos/{orcamento_id}/calcular")
        assert resp.status_code == 200
        item = resp.json()["itens"][0]
        bdi_pct = Decimal(str(item["bdi_aplicado"])) * 100
        assert abs(bdi_pct - Decimal("35.88")) < Decimal("0.05")

    def test_bdi_mat_mo_pr_com_reidi(self, cliente_id, bdi_rows, ficha_servico_id):
        """Com REIDI → BDI ≈ 30.74% (docs/04)."""
        oid = client.post(
            "/api/v1/orcamentos",
            json={
                "numero": "PROP-REIDI",
                "cliente_id": cliente_id,
                "uf_execucao": "PR",
                "beneficio_reidi": True,
            },
        ).json()["id"]
        self._add(oid, "servicos", "BDI-MAT+MO", 10, 100, fs=ficha_servico_id)
        resp = client.post(f"/api/v1/orcamentos/{oid}/calcular")
        assert resp.status_code == 200
        assert resp.json()["beneficio_reidi"] is True
        item = resp.json()["itens"][0]
        bdi_pct = Decimal(str(item["bdi_aplicado"])) * 100
        assert abs(bdi_pct - Decimal("30.74")) < Decimal("0.05")

    def test_fator_k(
        self,
        orcamento_id,
        bdi_rows,
        ficha_servico_id,
        ficha_servico_b_id,
        ficha_produto_id,
        estrutura_aloj,
    ):
        self._add(
            orcamento_id,
            "servicos",
            "BDI-MAT+MO",
            10,
            100,
            fs=ficha_servico_id,
            desc="A",
        )
        self._add(
            orcamento_id,
            "servicos",
            "BDI-MAT+MO",
            12,
            45,
            fs=ficha_servico_b_id,
            desc="B",
        )
        self._add(
            orcamento_id, "produtos", "BDI+ICMS", 10, 20, fp=ficha_produto_id, desc="C"
        )
        self._add(orcamento_id, "operacional", "-", 0, 1, desc="Alojamento Passo Fundo")

        data = client.post(f"/api/v1/orcamentos/{orcamento_id}/calcular").json()
        subtotal = Decimal(str(data["subtotal_faturavel"]))
        total_nf = Decimal(str(data["total_nao_faturavel"]))
        total = Decimal(str(data["total_proposta"]))
        assert total_nf > 0
        # sem desconto, total ≈ subtotal + nao_faturavel (tolerância p/ rounding
        # acumulado do rateio Fator K por linha — Decimal(4) × várias linhas)
        assert abs(total - (subtotal + total_nf)) < Decimal("0.50")
        assert Decimal(str(data["fator_k_percentual"])) > 0
        fat = [i for i in data["itens"] if i["bloco"] in ("servicos", "produtos")]
        soma = sum(Decimal(str(i["peso_rateio"])) for i in fat)
        assert abs(soma - Decimal("100")) < Decimal("0.20")

    def test_desconto_rateado(self, orcamento_id, bdi_rows, ficha_servico_id):
        self._add(orcamento_id, "servicos", "BDI-MAT+MO", 10, 100, fs=ficha_servico_id)
        client.put(
            f"/api/v1/orcamentos/{orcamento_id}", json={"desconto_percentual": "10.00"}
        )
        data = client.post(f"/api/v1/orcamentos/{orcamento_id}/calcular").json()
        subtotal = Decimal(str(data["subtotal_faturavel"]))
        total = Decimal(str(data["total_proposta"]))
        # total deve ser ~10% menor que o subtotal (sem itens não faturáveis)
        assert abs(total - subtotal * Decimal("0.90")) < Decimal("0.50")
        # desconto FLAT por linha: desconto_rateado = preco_venda_total × 10%
        item = data["itens"][0]
        preco = Decimal(str(item["preco_venda_total"]))
        desc = Decimal(str(item["desconto_rateado"]))
        assert abs(desc - preco * Decimal("0.10")) < Decimal("0.01")

    def test_calcular_sem_itens_422(self, orcamento_id):
        assert (
            client.post(f"/api/v1/orcamentos/{orcamento_id}/calcular").status_code
            == 422
        )

    def test_calcular_atualiza_totais(self, orcamento_id, bdi_rows, ficha_servico_id):
        self._add(orcamento_id, "servicos", "BDI-MAT+MO", 10, 10, fs=ficha_servico_id)
        client.post(f"/api/v1/orcamentos/{orcamento_id}/calcular")
        d = client.get(f"/api/v1/orcamentos/{orcamento_id}").json()
        assert Decimal(str(d["total_proposta"])) > 0
        assert Decimal(str(d["total_custo_direto"])) > 0
        assert Decimal(str(d["margem_liquida_real"])) > 0


# ── Dashboard (BLOCO 1.1 — regressão do 500 por campo renomeado) ──────────────


class TestDashboard:
    def _mk_orc(self, db_session, cliente_id, numero, status, total, custo):
        from decimal import Decimal
        from backend.models.orcamento_models import Orcamento
        o = Orcamento(
            numero=numero, cliente_id=cliente_id, uf_execucao="PR",
            status=status, total_proposta=Decimal(total),
            total_custo_direto=Decimal(custo),
            margem_liquida_real=Decimal("0.20"),
        )
        db_session.add(o)
        db_session.commit()

    def test_dashboard_vazio_200(self):
        d = client.get("/api/v1/dashboard").json()
        for chave in (
            "total_orcado_mes", "total_orcado_acumulado",
            "margem_rs_mes", "margem_rs_acumulado",
            "margem_pct_mes", "margem_pct_acumulado",
            "por_status", "total_orcamentos", "orcamentos_recentes",
        ):
            assert chave in d, chave

    def test_total_orcado_conta_so_enviado(self, db_session, cliente_id):
        self._mk_orc(db_session, cliente_id, "ENV-1", "enviado", "1000", "600")
        self._mk_orc(db_session, cliente_id, "RAS-1", "rascunho", "5000", "100")
        d = client.get("/api/v1/dashboard").json()
        assert float(d["total_orcado_acumulado"]) == 1000.0

    def test_margem_conta_so_fechado(self, db_session, cliente_id):
        self._mk_orc(db_session, cliente_id, "FEC-1", "fechado", "1000", "600")
        self._mk_orc(db_session, cliente_id, "ENV-2", "enviado", "9000", "100")
        d = client.get("/api/v1/dashboard").json()
        assert float(d["margem_rs_acumulado"]) == 400.0
        assert abs(float(d["margem_pct_acumulado"]) - 0.20) < 0.0001


# ── v2: desconto faturável-only, preço final, aprovar+observações+histórico ──


class TestV2Calculo:
    def _add(self, oid, bloco, mod_fat, margem, qty, fs=None, custo=None, desc="Item"):
        payload = {
            "bloco": bloco,
            "descricao": desc,
            "unidade": "un",
            "quantidade": str(qty),
            "mod_fat": mod_fat,
            "margem_lucro": str(margem),
        }
        if fs:
            payload["ficha_servico_id"] = fs
        if custo is not None:
            payload["custo_direto_unitario"] = str(custo)
        r = client.post(f"/api/v1/orcamentos/{oid}/itens", json=payload)
        assert r.status_code == 201, r.text
        return r.json()["id"]

    def test_desconto_so_faturaveis(
        self, orcamento_id, bdi_rows, ficha_servico_id, estrutura_aloj
    ):
        self._add(orcamento_id, "servicos", "BDI-MAT+MO", 10, 100, fs=ficha_servico_id)
        self._add(orcamento_id, "operacional", "-", 0, 1, desc="Alojamento Passo Fundo")
        client.put(
            f"/api/v1/orcamentos/{orcamento_id}", json={"desconto_percentual": "10.00"}
        )
        data = client.post(f"/api/v1/orcamentos/{orcamento_id}/calcular").json()
        for it in data["itens"]:
            if it["bloco"] in ("operacional", "excepcionais"):
                # BLOCO 1.2 — não-faturáveis NÃO recebem desconto
                assert Decimal(str(it["desconto_rateado"])) == Decimal("0")
            if it["bloco"] in ("servicos", "produtos"):
                assert Decimal(str(it["desconto_rateado"])) > 0

    def test_preco_unitario_final(self, orcamento_id, bdi_rows, ficha_servico_id):
        self._add(orcamento_id, "servicos", "BDI-MAT+MO", 10, 100, fs=ficha_servico_id)
        client.put(
            f"/api/v1/orcamentos/{orcamento_id}", json={"desconto_percentual": "10.00"}
        )
        data = client.post(f"/api/v1/orcamentos/{orcamento_id}/calcular").json()
        it = data["itens"][0]
        unit = Decimal(str(it["preco_venda_unitario"]))
        final = Decimal(str(it["preco_venda_unitario_final"]))
        # BLOCO 1.1 — final reflete o desconto (~10% menor)
        assert final < unit
        assert abs(final - unit * Decimal("0.90")) < Decimal("0.10")

    def test_aprovar_via_status_grava_historico(
        self, orcamento_id, bdi_rows, ficha_servico_id
    ):
        self._add(orcamento_id, "servicos", "BDI-MAT+MO", 10, 10, fs=ficha_servico_id)
        client.put(f"/api/v1/orcamentos/{orcamento_id}", json={"status": "enviado"})
        r = client.put(f"/api/v1/orcamentos/{orcamento_id}", json={"status": "aprovado"})
        assert r.status_code == 200
        assert r.json()["status"] == "aprovado"
        hist = client.get(
            f"/api/v1/orcamentos/{orcamento_id}/historico-descontos"
        ).json()
        assert len(hist) >= 1
        assert hist[0]["versao"] == 1


# ── v2: segmentos validados + data_limite ────────────────────────────────────


class TestSegmentosEDataLimite:
    @pytest.fixture
    def segs(self, db_session):
        from backend.models.param_models import ParametroSeguimento

        db_session.add_all(
            [
                ParametroSeguimento(nome="EPS", ativo=True),
                ParametroSeguimento(nome="VERTICAL", ativo=True),
            ]
        )
        db_session.commit()

    def test_cria_com_segmentos(self, cliente_id, segs):
        r = client.post(
            "/api/v1/orcamentos",
            json={
                "numero": "SEG-1",
                "cliente_id": cliente_id,
                "uf_execucao": "PR",
                "data_limite": "2026-07-01",
                "segmentos": ["EPS"],
            },
        )
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["segmentos"] == ["EPS"]
        assert body["data_limite"] == "2026-07-01"

    def test_rejeita_segmento_inexistente(self, cliente_id, segs):
        r = client.post(
            "/api/v1/orcamentos",
            json={
                "numero": "SEG-2",
                "cliente_id": cliente_id,
                "uf_execucao": "PR",
                "segmentos": ["NAO_EXISTE_XYZ"],
            },
        )
        assert r.status_code == 422

    def test_rejeita_segmento_duplicado(self, cliente_id, segs):
        r = client.post(
            "/api/v1/orcamentos",
            json={
                "numero": "SEG-DUP",
                "cliente_id": cliente_id,
                "uf_execucao": "PR",
                "segmentos": ["EPS", "EPS"],
            },
        )
        assert r.status_code == 422

    def test_substitui_segmentos_no_put(self, cliente_id, segs):
        r = client.post(
            "/api/v1/orcamentos",
            json={
                "numero": "SEG-3",
                "cliente_id": cliente_id,
                "uf_execucao": "PR",
                "segmentos": ["EPS"],
            },
        )
        assert r.status_code == 201, r.text
        oid = r.json()["id"]
        r2 = client.put(
            f"/api/v1/orcamentos/{oid}", json={"segmentos": ["VERTICAL"]}
        )
        assert r2.status_code == 200, r2.text
        assert r2.json()["segmentos"] == ["VERTICAL"]
