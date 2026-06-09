#!/usr/bin/env bash
# entrypoint.sh — executa seed se banco estiver vazio, depois sobe o app
set -euo pipefail

echo "[entrypoint] Aguardando banco de dados..."
python - <<'EOF'
import time, sys
from sqlalchemy import create_engine, text
from backend.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
for attempt in range(30):
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print(f"[entrypoint] Banco disponível após {attempt+1} tentativa(s).")
        sys.exit(0)
    except Exception as e:
        print(f"[entrypoint] Tentativa {attempt+1}/30: {e}")
        time.sleep(2)
print("[entrypoint] Banco não ficou disponível. Abortando.")
sys.exit(1)
EOF

echo "[entrypoint] Criando tabelas e executando seed..."
python -c "
from backend.database import Base, engine
from backend.models import bd_models, orcamento_models, usuario_models  # noqa: F401
Base.metadata.create_all(bind=engine)
import os
if os.getenv('ENV') == 'production':
    from backend.seeds_prod import run
else:
    from backend.seeds import run
run()
"

echo "[entrypoint] Iniciando servidor..."
exec uvicorn backend.main:app --host 0.0.0.0 --port 8000
