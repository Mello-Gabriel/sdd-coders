#!/bin/sh
# Periodic Postgres backup with retention. Run via the docker-compose "backup"
# profile (see infra/docker-compose.yml). Dumps are gzipped into the pgbackups
# volume; restore with:
#   gunzip -c /backups/<file>.sql.gz | psql -h db -U "$POSTGRES_USER" "$POSTGRES_DB"
set -eu

DB="${POSTGRES_DB:-app}"
DB_USER="${POSTGRES_USER:-postgres}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"
INTERVAL="${BACKUP_INTERVAL_SECONDS:-86400}"

mkdir -p /backups

while true; do
  ts="$(date +%Y%m%d-%H%M%S)"
  out="/backups/${DB}-${ts}.sql.gz"
  echo "[backup] dumping ${DB} -> ${out}"
  if pg_dump -h db -U "${DB_USER}" "${DB}" | gzip >"${out}"; then
    echo "[backup] ok"
  else
    echo "[backup] FAILED" >&2
    rm -f "${out}"
  fi
  find /backups -name '*.sql.gz' -mtime "+${RETENTION_DAYS}" -delete
  sleep "${INTERVAL}"
done
