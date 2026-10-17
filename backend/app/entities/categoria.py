"""Entidade `categorias` (seção 5.2). PK `INT`; grade montada pelo banco
(`icone`, `ordem`, `ativa`)."""

from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Identity,
    Integer,
    SmallInteger,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Categoria(Base):
    __tablename__ = "categorias"
    __table_args__ = (UniqueConstraint("nome_categoria", name="uq_categorias_nome"),)

    id_categoria: Mapped[int] = mapped_column(Integer, Identity(always=True), primary_key=True)
    nome_categoria: Mapped[str] = mapped_column(String(100), nullable=False)
    icone: Mapped[str | None] = mapped_column(String(16), nullable=True)
    ordem: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="0")
    ativa: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=func.true())
