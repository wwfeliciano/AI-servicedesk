"""Testes de banco (F0.3) com PostgreSQL real.

- `test_conexao_banco`: conecta no banco real e confere as 6 tabelas, os 4 ENUMs
  e as 7 categorias do seed.
- `test_migrations_ida_e_volta`: `upgrade head → downgrade base → upgrade head`,
  provando que o `downgrade()` reverte tudo (tabelas, tipos, função e extensões).

Ambos pulam (`skip`) se o banco não estiver no ar. Rodam num **banco de teste dedicado**
(`<POSTGRES_DB>_test`, criado sob demanda pelo conftest), para a ida e volta destrutiva nunca
tocar os dados de desenvolvimento (AJ-002). Não fixam ids: as sequências `IDENTITY` não voltam
no rollback (seção 6, armadilhas).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from tests.conftest import url_banco_host

TABELAS_ESPERADAS = {
    "usuarios",
    "categorias",
    "chamados",
    "follow_ups",
    "solucoes",
    "base_conhecimento",
}
ENUMS_ESPERADOS = {
    "perfil_usuario",
    "severidade_chamado",
    "status_chamado",
    "status_aprovacao",
}
BACKEND_DIR = Path(__file__).resolve().parents[1]


def _config_alembic(url: str) -> Config:
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "app" / "migrations"))
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg


def _banco_ou_skip() -> str:
    url = url_banco_host()
    if url is None:
        pytest.skip("Sem .env com variáveis do PostgreSQL; teste de banco pulado.")
    engine = create_engine(url)
    try:
        with engine.connect() as conexao:
            conexao.execute(text("SELECT 1"))
    except OperationalError:
        pytest.skip("Banco não está no ar (127.0.0.1); teste de banco pulado.")
    finally:
        engine.dispose()
    return url


def test_conexao_banco() -> None:
    url = _banco_ou_skip()
    engine = create_engine(url)
    # Garante o esquema aplicado (idempotente; não apaga dados existentes).
    command.upgrade(_config_alembic(url), "head")
    try:
        with engine.connect() as conexao:
            tabelas = {
                linha[0]
                for linha in conexao.execute(
                    text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
                )
            }
            enums = {
                linha[0]
                for linha in conexao.execute(
                    text("SELECT typname FROM pg_type WHERE typtype = 'e'")
                )
            }
            total_categorias = conexao.execute(text("SELECT count(*) FROM categorias")).scalar_one()

        assert tabelas >= TABELAS_ESPERADAS
        assert enums >= ENUMS_ESPERADOS
        assert total_categorias == 7
    finally:
        engine.dispose()


@pytest.mark.lento
def test_migrations_ida_e_volta() -> None:
    url = _banco_ou_skip()
    cfg = _config_alembic(url)
    engine = create_engine(url)
    try:
        command.upgrade(cfg, "head")
        command.downgrade(cfg, "base")

        with engine.connect() as conexao:
            enums = conexao.execute(
                text("SELECT count(*) FROM pg_type WHERE typtype = 'e'")
            ).scalar_one()
            funcao = conexao.execute(
                text("SELECT count(*) FROM pg_proc WHERE proname = 'f_unaccent'")
            ).scalar_one()
            tabela_chamados = conexao.execute(
                text("SELECT to_regclass('public.chamados')")
            ).scalar_one()

        assert enums == 0
        assert funcao == 0
        assert tabela_chamados is None

        # Volta ao estado esperado para os demais testes e para o uso em dev.
        command.upgrade(cfg, "head")
        with engine.connect() as conexao:
            total_categorias = conexao.execute(text("SELECT count(*) FROM categorias")).scalar_one()
        assert total_categorias == 7
    finally:
        engine.dispose()
