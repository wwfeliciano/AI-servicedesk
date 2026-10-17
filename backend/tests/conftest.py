"""Fixtures compartilhadas dos testes da F0.2.

Sem banco real neste recorte: o `/api/health/db` é testado com a dependência de
sessão substituída. O `test_conexao_banco` com PostgreSQL real e as 6 tabelas
entra na F0.3 (seção 12.1).
"""

from __future__ import annotations

import os
from collections.abc import Iterator

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
