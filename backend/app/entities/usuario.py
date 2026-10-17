"""Entidade `usuarios` (seção 5.2). Exclusão lógica por `ativo`; e-mail único e
sempre em minúsculas (RN07)."""

from __future__ import annotations

import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Identity,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.entities.enums import PerfilUsuario, perfil_usuario_enum


class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = (
        UniqueConstraint("email", name="uq_usuarios_email"),
        CheckConstraint("email = lower(email)", name="ck_usuarios_email_minusculo"),
    )

    id_usuario: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo_perfil: Mapped[PerfilUsuario] = mapped_column(
        perfil_usuario_enum, nullable=False, server_default="CLIENTE"
    )
    cargo: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=func.true())
    data_cadastro: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
