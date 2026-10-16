#!/bin/sh
# Cria o banco e o usuário do n8n (Fase 6) no mesmo PostgreSQL.
# O entrypoint oficial só executa este script na primeira inicialização do volume pg_data.
set -eu

if [ -z "${N8N_DB_NAME:-}" ] || [ -z "${N8N_DB_USER:-}" ] || [ -z "${N8N_DB_PASSWORD:-}" ]; then
  echo "01-n8n.sh: N8N_DB_* não definidos; banco do n8n não criado."
  exit 0
fi

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  -v nome="$N8N_DB_NAME" -v usuario="$N8N_DB_USER" -v senha="$N8N_DB_PASSWORD" <<'SQL'
CREATE ROLE :"usuario" LOGIN PASSWORD :'senha';
CREATE DATABASE :"nome" OWNER :"usuario";
SQL

echo "01-n8n.sh: banco do n8n criado."
