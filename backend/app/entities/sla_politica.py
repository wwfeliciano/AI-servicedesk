"""Entidade `sla_politicas` (seção 7.2, F7.2 / decisão B20).

Prazo (em horas corridas) por severidade. A severidade é a chave primária e usa o
mesmo ENUM dos chamados. Ajustável: alterar a linha muda a meta de SLA.
"""

from __future__ import annotations

from sqlalchemy import CheckConstraint, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.entities.enums import SeveridadeChamado, severidade_chamado_enum


class SlaPolitica(Base):
    __tablename__ = "sla_politicas"
    __table_args__ = (CheckConstraint("prazo_horas > 0", name="ck_sla_politicas_prazo_positivo"),)

    severidade: Mapped[SeveridadeChamado] = mapped_column(severidade_chamado_enum, primary_key=True)
    prazo_horas: Mapped[int] = mapped_column(Integer, nullable=False)
