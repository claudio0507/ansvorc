import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.auth import criar_token
from backend.database import Base, get_db
from backend.main import app

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


class TestConfigDiretor:
    def test_get_inclui_campos_diretor(self):
        d = client.get("/api/v1/config").json()
        for chave in ("diretor_nome", "diretor_funcao", "diretor_telefone", "diretor_email"):
            assert chave in d

    def test_put_persiste_diretor(self):
        r = client.put("/api/v1/config", json={
            "diretor_nome": "Carlos Mendes",
            "diretor_funcao": "Diretor Comercial",
            "diretor_telefone": "(41) 9 8888-7777",
            "diretor_email": "carlos@empresa.com",
        })
        assert r.status_code == 200
        assert r.json()["diretor_nome"] == "Carlos Mendes"
        d2 = client.get("/api/v1/config").json()
        assert d2["diretor_funcao"] == "Diretor Comercial"
        assert d2["diretor_email"] == "carlos@empresa.com"
