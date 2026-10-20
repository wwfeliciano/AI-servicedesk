"""Entidade `anexos` (seção 5.4). Arquivo guardado no S3 (MinIO); o banco guarda
só os metadados. `chave_objeto` é única; `mime_type` e `tamanho_bytes` têm CHECK."""

from __future__ import annotations

import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Anexo(Base):
    __tablename__ = "anexos"
    __table_args__ = (
        CheckConstraint(
            "mime_type IN ('image/png', 'image/jpeg', 'application/pdf')",
            name="ck_anexos_mime_type",
        ),
        CheckConstraint(
            "tamanho_bytes BETWEEN 1 AND 10485760",
            name="ck_anexos_tamanho",
        ),
        Index("uq_anexos_chave_objeto", "chave_objeto", unique=True),
        Index("ix_anexos_chamado", "id_chamado"),
    )

    id_anexo: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
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
    nome_original: Mapped[str] = mapped_column(String(255), nullable=False)
    chave_objeto: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    tamanho_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    data_envio: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
