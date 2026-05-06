#!/usr/bin/env bash
# Wipes all objects in the target Postgres database (public schema).
# Use before first deploy after squashed migrations, or to recover from
# inconsistent django_migrations history. Destroys all data.
#
# Requires: psql client. Set the same vars as Elastic Beanstalk / RDS:
#   POSTGRES_HOST POSTGRES_USER POSTGRES_PASSWORD POSTGRES_DB
#
# Example (with tunnel to private RDS):
#   export POSTGRES_HOST=127.0.0.1 POSTGRES_USER=huginn ...
#   bash scripts/reset_huginn_postgres.sh

set -euo pipefail

: "${POSTGRES_HOST:?POSTGRES_HOST not set}"
: "${POSTGRES_USER:?POSTGRES_USER not set}"
: "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD not set}"
: "${POSTGRES_DB:?POSTGRES_DB not set}"

export PGPASSWORD="${POSTGRES_PASSWORD}"
PSQL=(psql -h "${POSTGRES_HOST}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -v ON_ERROR_STOP=1)

echo "Dropping and recreating schema public on ${POSTGRES_HOST}/${POSTGRES_DB}..."
"${PSQL[@]}" <<'SQL'
DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO CURRENT_USER;
SQL

echo "Done. Run migrate from the app (or redeploy EB)."
