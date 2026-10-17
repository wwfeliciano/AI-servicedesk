"""Entidade `follow_ups` (seção 5.2). Mensagens do acompanhamento do chamado."""

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
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class FollowUp(Base):
    __tablename__ = "follow_ups"
    __table_args__ = (
        CheckConstraint("length(btrim(mensagem)) > 0", name="ck_follow_ups_mensagem"),
        Index("ix_followups_chamado_data", "id_chamado", "data_envio"),
    )

    id_followup: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    id_chamado: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("chamados.id_chamado", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    id_autor: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("usuarios.id_usuario", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    mensagem: Mapped[str] = mapped_column(Text, nullable=False)
    data_envio: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
