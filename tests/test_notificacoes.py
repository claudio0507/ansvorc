from datetime import date, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.auth import criar_token
from backend.database import Base, get_db
from backend.main import app
from backend.models.orcamento_models import Cliente, Orcamento

engine_test = create_engine(
    "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
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
    c = Cliente(nome="ACME", cnpj_cpf="00.000.000/0001-91")
    db_session.add(c); db_session.commit(); db_session.refresh(c)
    return c.id

def _mk(db_session, cliente_id, numero, status, dlimite):
    o = Orcamento(numero=numero, cliente_id=cliente_id, uf_execucao="PR", status=status, data_limite=dlimite)
    db_session.add(o); db_session.commit()


class TestNotificacoes:
    def test_so_rascunho_reprovado_ate_amanha(self, db_session, cliente_id):
        hoje = date.today()
        _mk(db_session, cliente_id, "N-ATRASO", "rascunho", hoje - timedelta(days=2))
        _mk(db_session, cliente_id, "N-HOJE", "reprovado", hoje)
        _mk(db_session, cliente_id, "N-AMANHA", "rascunho", hoje + timedelta(days=1))
        _mk(db_session, cliente_id, "N-FUTURO", "rascunho", hoje + timedelta(days=5))
        _mk(db_session, cliente_id, "N-ENVIADO", "enviado", hoje)
        d = client.get("/api/v1/notificacoes").json()
        numeros = {n["numero"] for n in d["notificacoes"]}
        assert numeros == {"N-ATRASO", "N-HOJE", "N-AMANHA"}
        assert d["total"] == 3
        urg = {n["numero"]: n["urgencia"] for n in d["notificacoes"]}
        assert urg["N-ATRASO"] == "atrasado"
        assert urg["N-HOJE"] == "hoje"
        assert urg["N-AMANHA"] == "amanha"

    def test_vazio(self):
        d = client.get("/api/v1/notificacoes").json()
        assert d["total"] == 0
        assert d["notificacoes"] == []


class TestPrazos:
    def test_filtra_por_mes(self, db_session, cliente_id):
        hoje = date.today()
        _mk(db_session, cliente_id, "P-ESTE", "rascunho", date(hoje.year, hoje.month, 15))
        prox = date(hoje.year + (hoje.month == 12), (hoje.month % 12) + 1, 10)
        _mk(db_session, cliente_id, "P-PROX", "rascunho", prox)
        mes_str = f"{hoje.year}-{hoje.month:02d}"
        lista = client.get(f"/api/v1/prazos?mes={mes_str}").json()
        numeros = {p["numero"] for p in lista}
        assert "P-ESTE" in numeros
        assert "P-PROX" not in numeros
