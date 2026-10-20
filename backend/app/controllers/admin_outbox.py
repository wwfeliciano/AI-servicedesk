"""Controller da fila do outbox para o admin (F6.2, seção 7.2).

- GET  /api/admin/outbox             → lista por status (paginada) + contadores
- POST /api/admin/outbox/{id}/reenviar → reenfileira um evento (FALHOU → PENDENTE)

Só ADMIN (dependência de perfil no router).
"""

from __future__ import annotations

import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel

from app.controllers.dependencias import OutboxServiceDep, exigir_perfil
from app.core.errors import ErroAPI
from app.entities.enums import PerfilUsuario, StatusOutbox
from app.entities.eventos_outbox import EventoOutbox
from app.services.outbox_service import ErroOutbox

router = APIRouter(
    prefix="/api/admin/outbox",
    tags=["admin-outbox"],
    dependencies=[Depends(exigir_perfil(PerfilUsuario.ADMIN))],
)


class EventoOutboxSaida(BaseModel):
    id_evento: int
    tipo: str
    canal: str
    destino: str
    status: str
    tentativas: int
    ultimo_erro: str | None
    proxima_tentativa_em: datetime.datetime
    criado_em: datetime.datetime
    enviado_em: datetime.datetime | None


class PaginaOutboxSaida(BaseModel):
    items: list[EventoOutboxSaida]
    total: int
    page: int
    page_size: int
    contadores: dict[str, int]


def _saida(e: EventoOutbox) -> EventoOutboxSaida:
    return EventoOutboxSaida(
        id_evento=e.id_evento,
        tipo=e.tipo,
        canal=e.canal.value,
        destino=e.destino,
        status=e.status.value,
        tentativas=e.tentativas,
        ultimo_erro=e.ultimo_erro,
        proxima_tentativa_em=e.proxima_tentativa_em,
        criado_em=e.criado_em,
        enviado_em=e.enviado_em,
    )


@router.get("", response_model=PaginaOutboxSaida, summary="Fila do outbox (ADMIN)")
def listar(
    servico: OutboxServiceDep,
    status_filtro: Annotated[StatusOutbox | None, Query(alias="status")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginaOutboxSaida:
    pagina = servico.listar(status=status_filtro, page=page, page_size=page_size)
    return PaginaOutboxSaida(
        items=[_saida(e) for e in pagina.items],
        total=pagina.total,
        page=pagina.page,
        page_size=pagina.page_size,
        contadores=pagina.contadores,
    )


@router.post(
    "/{id_evento}/reenviar",
    response_model=EventoOutboxSaida,
    summary="Reenfileira um evento (ADMIN)",
)
def reenviar(id_evento: int, servico: OutboxServiceDep) -> EventoOutboxSaida:
    try:
        evento = servico.reenviar(id_evento)
    except ErroOutbox as exc:
        raise ErroAPI(
            status_code=status.HTTP_404_NOT_FOUND, codigo=exc.codigo, mensagem=exc.mensagem
        ) from exc
    return _saida(evento)
