"""Service do SLA (F7.2). O indicador "SLA do mês" (seção 8.4) é o percentual de
chamados concluídos no mês corrente que respeitaram o prazo (decisão B20).
"""

from __future__ import annotations

import datetime

from app.repositories.sla_repository import ResumoSla, SlaRepository


class SlaService:
    def __init__(self, *, sla: SlaRepository) -> None:
        self._sla = sla

    def sla_do_mes(self) -> ResumoSla:
        return self._sla.sla_do_mes(referencia=datetime.datetime.now(datetime.UTC))
