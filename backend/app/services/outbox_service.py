"""Service da fila do outbox para o admin (F6.2).

Lista os eventos (por status, paginado) com os contadores, e reenfileira um evento
(normalmente FALHOU) para nova tentativa imediata. Não conhece HTTP.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.entities.enums import StatusOutbox
from app.entities.eventos_outbox import EventoOutbox
from app.repositories.outbox_repository import OutboxRepository


class ErroOutbox(Exception):
    def __init__(self, codigo: str, mensagem: str) -> None:
        super().__init__(mensagem)
        self.codigo = codigo
        self.mensagem = mensagem


@dataclass(frozen=True)
class PaginaOutbox:
    items: list[EventoOutbox]
    total: int
    page: int
    page_size: int
    contadores: dict[str, int]


class OutboxService:
    def __init__(self, *, outbox: OutboxRepository) -> None:
        self._outbox = outbox

    def listar(
        self, *, status: StatusOutbox | None = None, page: int = 1, page_size: int = 20
    ) -> PaginaOutbox:
        itens, total = self._outbox.listar(status=status, page=page, page_size=page_size)
        return PaginaOutbox(
            items=itens,
            total=total,
            page=page,
            page_size=page_size,
            contadores=self._outbox.contar_por_status(),
        )

    def reenviar(self, id_evento: int) -> EventoOutbox:
        evento = self._outbox.reenfileirar(id_evento)
        if evento is None:
            raise ErroOutbox("NAO_ENCONTRADO", "Evento não encontrado.")
        return evento
