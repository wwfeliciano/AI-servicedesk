"""Repositório do SLA (F7.2): política de prazo por severidade e o cálculo do
"SLA do mês" (percentual de chamados concluídos no prazo).
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.entities.chamado import Chamado
from app.entities.enums import SeveridadeChamado
from app.entities.sla_politica import SlaPolitica


@dataclass(frozen=True)
class ResumoSla:
    total: int  # chamados concluídos no período
    no_prazo: int  # desses, quantos dentro do prazo
    percentual: float  # no_prazo / total * 100 (0.0 quando total = 0)


class SlaRepository:
    def __init__(self, sessao: Session) -> None:
        self._sessao = sessao

    def prazo_horas(self, severidade: SeveridadeChamado) -> int | None:
        """Horas do SLA para a severidade (None se não houver política)."""
        return self._sessao.scalar(
            select(SlaPolitica.prazo_horas).where(SlaPolitica.severidade == severidade)
        )

    def sla_do_mes(self, *, referencia: datetime.datetime) -> ResumoSla:
        """SLA do mês de `referencia`: entre os chamados **concluídos** no mês
        (com `data_conclusao` no mês), o percentual cujo `data_conclusao` ficou
        dentro do `prazo_sla`. Chamados sem `prazo_sla` (anteriores à F7.2) contam
        no total mas não como "no prazo"."""
        inicio = referencia.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        proximo_mes = (inicio + datetime.timedelta(days=32)).replace(day=1)

        no_mes = (
            (Chamado.data_conclusao.is_not(None))
            & (Chamado.data_conclusao >= inicio)
            & (Chamado.data_conclusao < proximo_mes)
        )
        total = int(self._sessao.scalar(select(func.count()).where(no_mes)) or 0)
        if total == 0:
            return ResumoSla(total=0, no_prazo=0, percentual=0.0)
        no_prazo = int(
            self._sessao.scalar(
                select(func.count()).where(
                    no_mes,
                    Chamado.prazo_sla.is_not(None),
                    Chamado.data_conclusao <= Chamado.prazo_sla,
                )
            )
            or 0
        )
        return ResumoSla(
            total=total, no_prazo=no_prazo, percentual=round(no_prazo / total * 100, 1)
        )
