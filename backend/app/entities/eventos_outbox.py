"""Entidade `eventos_outbox` (seção 9.2).

Outbox transacional dos canais externos (e-mail e WhatsApp): o service que muda o
estado grava aqui, na **mesma transação** da mudança. O `worker` (F6.2) lê e
despacha ao n8n com retentativas. O canal Portal NÃO entra aqui — vai para
`notificacoes`.
"""

from __future__ import annotations

import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    DateTime,
    Identity,
    Index,
    SmallInteger,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.entities.enums import (
    CanalNotificacao,
    StatusOutbox,
    canal_notificacao_enum,
    status_outbox_enum,
)


class EventoOutbox(Base):
    __tablename__ = "eventos_outbox"
    __table_args__ = (
        # Índice parcial da fila: o worker busca PENDENTE/PROCESSANDO por
        # proxima_tentativa_em (seção 9.2).
        Index(
            "ix_eventos_outbox_fila",
            "proxima_tentativa_em",
            postgresql_where=text("status IN ('PENDENTE', 'PROCESSANDO')"),
        ),
    )

    id_evento: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    tipo: Mapped[str] = mapped_column(String(60), nullable=False)
    canal: Mapped[CanalNotificacao] = mapped_column(canal_notificacao_enum, nullable=False)
    destino: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[StatusOutbox] = mapped_column(
        status_outbox_enum, nullable=False, server_default="PENDENTE"
    )
    tentativas: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text("0"))
    proxima_tentativa_em: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    bloqueado_ate: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ultimo_erro: Mapped[str | None] = mapped_column(Text, nullable=True)
    criado_em: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    enviado_em: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
