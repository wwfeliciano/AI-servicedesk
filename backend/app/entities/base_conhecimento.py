"""Entidade `base_conhecimento` (seção 5.2). Uma entrada por solução aprovada
(`uq_base_conhecimento_solucao`). A coluna de busca `tsvector` entra na F5."""

from __future__ import annotations

import datetime

from sqlalchemy import (
    BigInteger,
    Computed,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

# Expressão da coluna gerada `busca` (migration 0005): título com peso A e
# conteúdo com peso B, na configuração pt_br_unaccent (full-text sem acento).
_BUSCA_EXPR = (
    "setweight(to_tsvector('pt_br_unaccent', titulo), 'A') || "
    "setweight(to_tsvector('pt_br_unaccent', conteudo_indexado), 'B')"
)


class BaseConhecimento(Base):
    __tablename__ = "base_conhecimento"
    __table_args__ = (
        UniqueConstraint("id_solucao", name="uq_base_conhecimento_solucao"),
        Index("ix_base_conhecimento_busca", "busca", postgresql_using="gin"),
    )

    id_base: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    id_solucao: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("solucoes.id_solucao", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    conteudo_indexado: Mapped[str] = mapped_column(Text, nullable=False)
    # Coluna gerada e somente leitura (full-text). O ciclo de vida é da migration 0005.
    busca: Mapped[str] = mapped_column(
        TSVECTOR, Computed(_BUSCA_EXPR, persisted=True), nullable=False
    )
    data_inclusao: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
