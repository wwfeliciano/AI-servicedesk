"""Fixtures compartilhadas dos testes.

A F0.2 testa `/api/health/db` com a dependência de sessão substituída (sem banco).
A F0.3 adiciona testes com PostgreSQL real: a URL vem do `.env` da raiz do
repositório, reescrita para o host (`db:5432` → `127.0.0.1:PORTA_DB`), já que o
pytest roda no host, não dentro da rede do Compose. Se o banco não estiver no ar,
esses testes são pulados (`skip`), não falham.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest

# Ambiente de teste determinístico (não depende de um .env presente).
os.environ.setdefault("AMBIENTE", "dev")
os.environ.setdefault("LOG_LEVEL", "WARNING")
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://helpdesk:x@db:5432/helpdesk")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from app.main import create_app
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(create_app()) as cliente:
        yield cliente


def _ler_env_raiz() -> dict[str, str]:
    """Lê o `.env` da raiz do repositório (duas pastas acima de tests/)."""
    caminho = Path(__file__).resolve().parents[2] / ".env"
    valores: dict[str, str] = {}
    if not caminho.exists():
        return valores
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, _, valor = linha.partition("=")
        valores[chave.strip()] = valor.strip()
    return valores


def url_banco_host() -> str | None:
    """URL do banco acessível pelo host (porta publicada em 127.0.0.1).

    Devolve `None` quando não há `.env` com as variáveis do PostgreSQL.
    """
    env = _ler_env_raiz()
    usuario = env.get("POSTGRES_USER")
    senha = env.get("POSTGRES_PASSWORD")
    banco = env.get("POSTGRES_DB")
    porta = env.get("PORTA_DB", "5442")
    if not (usuario and senha and banco):
        return None
    return f"postgresql+psycopg://{usuario}:{senha}@127.0.0.1:{porta}/{banco}"
