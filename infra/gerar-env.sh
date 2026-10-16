#!/bin/sh
# Cria o .env a partir do .env.example, trocando cada placeholder por um segredo aleatório.
# Nunca sobrescreve um .env existente. Os segredos não são exibidos.
set -eu
cd "$(dirname "$0")/.."

if [ -e .env ]; then
  echo ".env já existe; nada foi alterado."
  exit 0
fi

umask 077
awk '
  function aleatorio(bytes,   cmd, valor) {
    cmd = "openssl rand -hex " bytes
    cmd | getline valor
    close(cmd)
    return valor
  }
  /^[A-Z0-9_]+=/ {
    chave = substr($0, 1, index($0, "=") - 1)
    valor = substr($0, index($0, "=") + 1)
    if (valor ~ /^(troque-me|troque-me-agora|gere-)/) {
      bytes = (valor ~ /hex-16/) ? 16 : 32
      valor = aleatorio(bytes)
      if (chave == "POSTGRES_PASSWORD") senha_pg = valor
      print chave "=" valor
      next
    }
    if (chave == "DATABASE_URL" && senha_pg != "") {
      sub(/:troque-me@/, ":" senha_pg "@", valor)
      print chave "=" valor
      next
    }
  }
  { print }
' .env.example > .env

echo ".env criado com segredos aleatórios (permissão 600)."
