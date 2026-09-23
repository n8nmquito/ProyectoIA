#!/usr/bin/env bash
set -Eeuo pipefail

# La imagen oficial ejecuta este archivo solo al inicializar un volumen vacío.
# Las contraseñas se pasan como variables psql y se escapan como literales SQL.
psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  --set=ON_ERROR_STOP=1 \
  --set=n8n_password="$N8N_DB_PASSWORD" \
  --set=redmine_password="$REDMINE_DB_PASSWORD" <<'SQL'
CREATE ROLE n8n LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD :'n8n_password';
CREATE ROLE redmine LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD :'redmine_password';

CREATE DATABASE n8n OWNER n8n;
CREATE DATABASE redmine OWNER redmine;

REVOKE ALL ON DATABASE n8n FROM PUBLIC;
REVOKE ALL ON DATABASE redmine FROM PUBLIC;
GRANT CONNECT, TEMPORARY ON DATABASE n8n TO n8n;
GRANT CONNECT, TEMPORARY ON DATABASE redmine TO redmine;
SQL
