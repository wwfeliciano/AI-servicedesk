"""Ambiente do Alembic (F0.3).

Lê a `DATABASE_URL` de `app.core.config` (ambiente / `.env`), não do `alembic.ini`.
`target_metadata = Base.metadata`, com todas as entidades importadas para que o
`--autogenerate` enxergue as 6 tabelas. Suporta os modos offline e online.
"""

from __future__ import annotations

from logging.config import fileConfig

# Importa as entidades para registrá-las no Base.metadata (autogenerate).
import app.entities  # noqa: F401
from alembic import context
from app.core.config import obter_configuracao
from app.core.database import Base
from sqlalchemy import engine_from_config, pool

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# A URL vem da configuração da aplicação (seção 5 do prompt), a menos que o
# chamador já tenha fixado uma `sqlalchemy.url` no Config (ex.: os testes, que
# injetam a URL do host). Assim o serviço `migrate` usa o host `db` da rede do
# Compose e o pytest no host usa `127.0.0.1`.
if not config.get_main_option("sqlalchemy.url"):
    config.set_main_option("sqlalchemy.url", obter_configuracao().database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Gera o SQL sem conexão (`alembic upgrade head --sql`)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Aplica as migrations com conexão ao banco."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
