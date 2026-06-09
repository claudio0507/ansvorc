#!/usr/bin/env bash
# backup.sh — pg_dump do banco Sinalys, mantém últimos 7 backups
# Uso: ./scripts/backup.sh
# Variáveis de ambiente respeitadas:
#   PGHOST     (default: localhost)
#   PGPORT     (default: 5432)
#   PGUSER     (default: sinalys)
#   PGPASSWORD (default: sinalys)
#   PGDATABASE (default: sinalys)
#   BACKUP_DIR (default: ./backups)
#   KEEP_DAYS  (default: 7)

set -euo pipefail

PGHOST="${PGHOST:-localhost}"
PGPORT="${PGPORT:-5432}"
PGUSER="${PGUSER:-sinalys}"
PGPASSWORD="${PGPASSWORD:-sinalys}"
PGDATABASE="${PGDATABASE:-sinalys}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
KEEP_DAYS="${KEEP_DAYS:-7}"

export PGPASSWORD

TIMESTAMP=$(date +%Y-%m-%d_%H%M)
FILENAME="backup_${TIMESTAMP}.sql.gz"
FILEPATH="${BACKUP_DIR}/${FILENAME}"

mkdir -p "${BACKUP_DIR}"

echo "[backup] Iniciando dump de ${PGDATABASE}@${PGHOST}:${PGPORT}..."
pg_dump \
  -h "${PGHOST}" \
  -p "${PGPORT}" \
  -U "${PGUSER}" \
  "${PGDATABASE}" \
  | gzip -9 > "${FILEPATH}"

SIZE=$(du -sh "${FILEPATH}" | cut -f1)
echo "[backup] Arquivo gerado: ${FILEPATH} (${SIZE})"

# Remove backups mais antigos que KEEP_DAYS dias
echo "[backup] Removendo backups com mais de ${KEEP_DAYS} dias..."
find "${BACKUP_DIR}" -name "backup_*.sql.gz" -mtime "+${KEEP_DAYS}" -delete

TOTAL=$(find "${BACKUP_DIR}" -name "backup_*.sql.gz" | wc -l | tr -d ' ')
echo "[backup] Backups retidos: ${TOTAL}"

# ── Placeholder: upload para S3 ───────────────────────────────────────────────
# Descomente e configure AWS_BUCKET para ativar upload S3:
#
# if [ -n "${AWS_BUCKET:-}" ]; then
#   echo "[backup] Enviando para s3://${AWS_BUCKET}/sinalys/..."
#   aws s3 cp "${FILEPATH}" "s3://${AWS_BUCKET}/sinalys/${FILENAME}"
#   echo "[backup] Upload concluído."
# fi

echo "[backup] Concluído."
