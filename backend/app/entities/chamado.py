"""Entidade `chamados` (seção 5.2).

`protocolo` é coluna gerada e somente leitura (`Computed(persisted=True)`).
A expressão de busca é `func.f_unaccent(func.lower(titulo))`, idêntica à do índice
trigram `ix_chamados_titulo_trgm` para que o planejador o use (seção 5.2).
"""

from __future__ import annotations

import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Computed,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.entities.enums import (
    SeveridadeChamado,
    StatusChamado,
    severidade_chamado_enum,
    status_chamado_enum,
)

# Expressão da coluna gerada `protocolo`, idêntica ao SQL da seção 5.2.
_PROTOCOLO_EXPR = "'TK-' || lpad(id_chamado::text, greatest(4, length(id_chamado::text)), '0')"


class Chamado(Base):
    __tablename__ = "chamados"

    id_chamado: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    protocolo: Mapped[str] = mapped_column(
        String(20),
        Computed(_PROTOCOLO_EXPR, persisted=True),
        nullable=False,
    )
    id_usuario_abertura: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("usuarios.id_usuario", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    id_tecnico_responsavel: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("usuarios.id_usuario", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=True,
    )
    id_categoria: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("categorias.id_categoria", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    titulo: Mapped[str] = mapped_column(String(150), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    severidade: Mapped[SeveridadeChamado] = mapped_column(
        severidade_chamado_enum, nullable=False, server_default="BAIXA"
    )
    status_chamado: Mapped[StatusChamado] = mapped_column(
        status_chamado_enum, nullable=False, server_default="NOVO"
    )
    data_criacao: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    data_atualizacao: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("length(btrim(titulo)) > 0", name="ck_chamados_titulo_preenchido"),
        CheckConstraint(
            "length(btrim(descricao)) BETWEEN 1 AND 500",
            name="ck_chamados_descricao_tamanho",
        ),
        CheckConstraint(
            "status_chamado IN ('NOVO', 'PENDENTE') " "OR id_tecnico_responsavel IS NOT NULL",
            name="ck_chamados_rn03_tecnico",
        ),
        # O protocolo é único por índice (não constraint), como no SQL da seção 5.2.
        Index("uq_chamados_protocolo", "protocolo", unique=True),
        Index(
            "ix_chamados_solicitante_data",
            "id_usuario_abertura",
            text("data_criacao DESC"),
        ),
        Index(
            "ix_chamados_tecnico",
            "id_tecnico_responsavel",
            postgresql_where=text("id_tecnico_responsavel IS NOT NULL"),
        ),
        Index(
            "ix_chamados_status_data",
            "status_chamado",
            text("data_criacao DESC"),
        ),
        Index("ix_chamados_categoria", "id_categoria"),
        Index(
            "ix_chamados_titulo_trgm",
            func.f_unaccent(func.lower(text("titulo"))),
            postgresql_using="gin",
            postgresql_ops={"f_unaccent_1": "gin_trgm_ops"},
        ),
    )
