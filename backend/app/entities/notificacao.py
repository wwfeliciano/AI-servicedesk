"""Entidade `notificacoes` (seção 5.4). Notificação de portal por usuário; pode
referenciar um chamado. Índice parcial para as não lidas (`lida_em IS NULL`)."""

from __future__ import annotations

import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    String,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Notificacao(Base):
    __tablename__ = "notificacoes"
    __table_args__ = (
        # Lista das não lidas por usuário, mais recentes primeiro (índice parcial).
        Index(
            "ix_notificacoes_nao_lidas",
            "id_usuario",
            text("data_criacao DESC"),
            postgresql_where=text("lida_em IS NULL"),
        ),
    )

    id_notificacao: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    id_usuario: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("usuarios.id_usuario", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    id_chamado: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("chamados.id_chamado", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=True,
    )
    tipo: Mapped[str] = mapped_column(String(50), nullable=False)
    titulo: Mapped[str] = mapped_column(String(150), nullable=False)
    mensagem: Mapped[str] = mapped_column(String(500), nullable=False)
    lida_em: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    data_criacao: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
