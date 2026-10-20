"""Controller do SLA (F7.2, seção 7.2/8.4).

`GET /api/sla/mes`: percentual de chamados concluídos no mês dentro do prazo
(decisão B20). Qualquer autenticado.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.controllers.dependencias import SlaServiceDep, usuario_atual

router = APIRouter(prefix="/api/sla", tags=["sla"], dependencies=[Depends(usuario_atual)])


class SlaMesSaida(BaseModel):
    total: int
    no_prazo: int
    percentual: float


@router.get("/mes", response_model=SlaMesSaida, summary="SLA do mês (autenticado)")
def sla_do_mes(servico: SlaServiceDep) -> SlaMesSaida:
    resumo = servico.sla_do_mes()
    return SlaMesSaida(total=resumo.total, no_prazo=resumo.no_prazo, percentual=resumo.percentual)
