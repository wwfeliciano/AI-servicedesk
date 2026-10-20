"""Entidade `tokens_redefinicao_senha` (seção 5.4, F7.1 / FA02).

Guarda o token de redefinição de senha como **hash SHA-256** (nunca em claro),
com expiração curta e marca de uso único (`usado_em`). Enviado ao usuário por
e-mail no link `/redefinir-senha?token=...`.
"""

from __future__ import annotations

import datetime

from sqlalchemy import CHAR, BigInteger, DateTime, ForeignKey, Identity, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TokenRedefinicaoSenha(Base):
    __tablename__ = "tokens_redefinicao_senha"
    __table_args__ = (
        Index("ix_tokens_redefinicao_token_hash", "token_hash", unique=True),
        Index("ix_tokens_redefinicao_usuario", "id_usuario"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    id_usuario: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("usuarios.id_usuario", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    expira_em: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    usado_em: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    criado_em: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
