"""Entidade `tokens_refresh` (seção 5.4).

Guarda o refresh token opaco como hash SHA-256 (nunca o valor em claro). A `familia`
(UUID) liga a cadeia de rotações: a cada uso um token é revogado e outro nasce na
mesma família; o reuso de um token já revogado derruba a família inteira (seção 11).
"""

from __future__ import annotations

import datetime
import uuid

from sqlalchemy import (
    CHAR,
    BigInteger,
    DateTime,
    ForeignKey,
    Identity,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TokenRefresh(Base):
    __tablename__ = "tokens_refresh"
    __table_args__ = (UniqueConstraint("token_hash", name="uq_tokens_refresh_token_hash"),)

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    id_usuario: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("usuarios.id_usuario", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    familia: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    expira_em: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revogado_em: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    criado_em: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
