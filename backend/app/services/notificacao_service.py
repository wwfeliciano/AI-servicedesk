"""Service de notificações do portal (F3.2, RF04).

Lê e marca as notificações **do próprio usuário** (escopo). A criação de
notificações é feita pelo `EventoService` (a partir de eventos de domínio).
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass

from app.entities.notificacao import Notificacao
from app.repositories.notificacao_repository import NotificacaoRepository


class ErroNotificacao(Exception):
    def __init__(self, codigo: str, mensagem: str) -> None:
        super().__init__(mensagem)
        self.codigo = codigo
        self.mensagem = mensagem


@dataclass(frozen=True)
class PaginaNotificacoes:
    items: list[Notificacao]
    total: int
    nao_lidas: int
    page: int
    page_size: int


def _agora() -> datetime.datetime:
    return datetime.datetime.now(tz=datetime.UTC)


class NotificacaoService:
    def __init__(self, *, notificacoes: NotificacaoRepository) -> None:
        self._notificacoes = notificacoes

    def listar(self, *, id_usuario: int, page: int = 1, page_size: int = 20) -> PaginaNotificacoes:
        itens, total = self._notificacoes.listar_do_usuario(
            id_usuario, page=page, page_size=page_size
        )
        nao_lidas = self._notificacoes.contar_nao_lidas(id_usuario)
        return PaginaNotificacoes(
            items=itens, total=total, nao_lidas=nao_lidas, page=page, page_size=page_size
        )

    def contar_nao_lidas(self, *, id_usuario: int) -> int:
        return self._notificacoes.contar_nao_lidas(id_usuario)

    def marcar_lida(self, *, id_usuario: int, id_notificacao: int) -> None:
        """Marca uma notificação do usuário como lida. 404 se não for dele/inexistente."""
        if not self._notificacoes.existe_do_usuario(id_notificacao, id_usuario):
            raise ErroNotificacao("NAO_ENCONTRADO", "Notificação não encontrada.")
        # Idempotente: se já estava lida, não há erro (rowcount 0).
        self._notificacoes.marcar_lida(id_notificacao, id_usuario, _agora())

    def marcar_todas_lidas(self, *, id_usuario: int) -> int:
        return self._notificacoes.marcar_todas_lidas(id_usuario, _agora())
