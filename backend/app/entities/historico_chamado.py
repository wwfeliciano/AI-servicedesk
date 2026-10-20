"""Entidade `historico_chamado` (seção 5.4). Linha do tempo das transições de
status do chamado. `id_autor` nulo = ação do sistema. `status_anterior` nulo no
evento de criação (NOVO)."""

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
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.entities.enums import StatusChamado, status_chamado_enum


class HistoricoChamado(Base):
    __tablename__ = "historico_chamado"
    __table_args__ = (Index("ix_historico_chamado_data", "id_chamado", "data_evento"),)

    id_historico: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    id_chamado: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("chamados.id_chamado", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    id_autor: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("usuarios.id_usuario", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=True,
    )
    status_anterior: Mapped[StatusChamado | None] = mapped_column(
        status_chamado_enum, nullable=True
    )
    status_novo: Mapped[StatusChamado] = mapped_column(status_chamado_enum, nullable=False)
    observacao: Mapped[str | None] = mapped_column(String(500), nullable=True)
    data_evento: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
