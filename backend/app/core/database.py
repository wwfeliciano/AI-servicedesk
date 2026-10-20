"""Acesso ao banco: engine e sessão SQLAlchemy 2.0 síncrono (seção 3.1).

A API nunca aplica migrations na partida (isso é do serviço `migrate`). Aqui ficam
só o engine, a fábrica de sessões e a base declarativa das entidades (F0.3+).
"""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import obter_configuracao


class Base(DeclarativeBase):
    """Base declarativa das entidades ORM (as 6 tabelas chegam na F0.3)."""


def criar_engine() -> Engine:
    config = obter_configuracao()
    # pool_pre_ping evita usar conexões derrubadas pelo banco após ociosidade.
    return create_engine(config.database_url, pool_pre_ping=True, future=True)


engine: Engine = criar_engine()
FabricaSessao: sessionmaker[Session] = sessionmaker(
    bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
)


def obter_sessao() -> Iterator[Session]:
    """Dependência do FastAPI: uma sessão por requisição.

    Faz `commit()` quando a requisição termina sem erro e `rollback()` se o handler
    (ou a dependência) levanta exceção. Sem isso, os `flush()` dos services não são
    persistidos e a transação é desfeita ao fechar a sessão.
    """
    sessao = FabricaSessao()
    try:
        yield sessao
        sessao.commit()
    except Exception:
        sessao.rollback()
        raise
    finally:
        sessao.close()
