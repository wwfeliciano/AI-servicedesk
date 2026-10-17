"""Entidade `solucoes` (seção 5.2).

Índice único parcial `uq_solucoes_uma_pendente`: no máximo uma solução
`PENDENTE_APROVACAO` por chamado (invariante da RN02/RN03).
"""

from __future__ import annotations

import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.entities.enums import StatusAprovacao, status_aprovacao_enum


class Solucao(Base):
    __tablename__ = "solucoes"
    __table_args__ = (
        CheckConstraint("length(btrim(descricao_solucao)) > 0", name="ck_solucoes_descricao"),
        Index("ix_solucoes_chamado", "id_chamado"),
        Index(
            "uq_solucoes_uma_pendente",
            "id_chamado",
            unique=True,
            postgresql_where=text("status_aprovacao = 'PENDENTE_APROVACAO'"),
        ),
    )

    id_solucao: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    id_chamado: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("chamados.id_chamado", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    id_analista: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("usuarios.id_usuario", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    descricao_solucao: Mapped[str] = mapped_column(Text, nullable=False)
    status_aprovacao: Mapped[StatusAprovacao] = mapped_column(
        status_aprovacao_enum, nullable=False, server_default="PENDENTE_APROVACAO"
    )
    data_solucao: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
