"""Entidade `base_conhecimento` (seção 5.2). Uma entrada por solução aprovada
(`uq_base_conhecimento_solucao`). A coluna de busca `tsvector` entra na F5."""

from __future__ import annotations

import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Identity,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class BaseConhecimento(Base):
    __tablename__ = "base_conhecimento"
    __table_args__ = (UniqueConstraint("id_solucao", name="uq_base_conhecimento_solucao"),)

    id_base: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    id_solucao: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("solucoes.id_solucao", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    conteudo_indexado: Mapped[str] = mapped_column(Text, nullable=False)
    data_inclusao: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
