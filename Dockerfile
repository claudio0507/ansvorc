# ── Stage 1: build deps ────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Instala dependências nativas para weasyprint e psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libcairo2 \
    libffi-dev \
    libssl-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: runtime ───────────────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Runtime libs para weasyprint (sem gcc)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libcairo2 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia site-packages instalados no stage builder
COPY --from=builder /install /usr/local

# Copia código da aplicação
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY scripts/entrypoint.sh ./entrypoint.sh

# Usuário não-root para segurança
RUN useradd -m -u 1001 sinalys \
    && chown -R sinalys:sinalys /app \
    && chmod +x /app/entrypoint.sh
USER sinalys

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["/app/entrypoint.sh"]
