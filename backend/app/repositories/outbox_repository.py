"""Repositório do outbox dos canais externos (F6.1 enfileiramento; F6.2 despacho).

Seção 9.2: a reserva do lote usa `FOR UPDATE SKIP LOCKED` para que vários workers
não peguem o mesmo evento. O backoff é exponencial (30 s, 1, 2, 4, 8 min… até 1 h)
e, após 8 tentativas, o evento vai para `FALHOU`.
"""

from __future__ import annotations

import datetime
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.entities.enums import CanalNotificacao, StatusOutbox
from app.entities.eventos_outbox import EventoOutbox

MAX_TENTATIVAS = 8
# Backoff por nº de tentativas já feitas (em segundos): 30s, 1, 2, 4, 8, 16, 32 min, 1 h.
_BACKOFF_SEGUNDOS = [30, 60, 120, 240, 480, 960, 1920, 3600]


def _agora() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC)


def _atraso_para(tentativas: int) -> datetime.timedelta:
    idx = min(max(tentativas - 1, 0), len(_BACKOFF_SEGUNDOS) - 1)
    return datetime.timedelta(seconds=_BACKOFF_SEGUNDOS[idx])


class OutboxRepository:
    def __init__(self, sessao: Session) -> None:
        self._sessao = sessao

    def enfileirar(
        self,
        *,
        tipo: str,
        canal: CanalNotificacao,
        destino: str,
        payload: dict[str, Any],
    ) -> EventoOutbox:
        """Grava um evento PENDENTE no outbox (na transação corrente, sem commit)."""
        evento = EventoOutbox(tipo=tipo, canal=canal, destino=destino, payload=payload)
        self._sessao.add(evento)
        self._sessao.flush()
        return evento

    # ----- despacho (F6.2) -----

    def reservar_lote(self, *, limite: int = 20, bloqueio_segundos: int = 60) -> list[EventoOutbox]:
        """Reserva um lote de eventos a despachar (seção 9.2).

        Marca como PROCESSANDO e define `bloqueado_ate = now() + bloqueio`, usando
        `FOR UPDATE SKIP LOCKED` para não colidir com outro worker. Devolve os
        eventos reservados (PENDENTE vencidos ou PROCESSANDO cujo bloqueio expirou).
        """
        linhas = self._sessao.execute(
            text(
                """
                UPDATE eventos_outbox
                   SET status = 'PROCESSANDO',
                       bloqueado_ate = now() + make_interval(secs => :bloqueio)
                 WHERE id_evento IN (
                       SELECT id_evento FROM eventos_outbox
                        WHERE (status = 'PENDENTE' AND proxima_tentativa_em <= now())
                           OR (status = 'PROCESSANDO' AND bloqueado_ate < now())
                        ORDER BY id_evento
                        LIMIT :limite
                        FOR UPDATE SKIP LOCKED)
                RETURNING id_evento
                """
            ),
            {"bloqueio": bloqueio_segundos, "limite": limite},
        ).all()
        ids = [linha[0] for linha in linhas]
        if not ids:
            return []
        eventos = self._sessao.scalars(
            select(EventoOutbox)
            .where(EventoOutbox.id_evento.in_(ids))
            .order_by(EventoOutbox.id_evento)
        ).all()
        return list(eventos)

    def marcar_enviado(self, id_evento: int) -> None:
        evento = self._sessao.get(EventoOutbox, id_evento)
        if evento is None:
            return
        evento.status = StatusOutbox.ENVIADO
        evento.enviado_em = _agora()
        evento.bloqueado_ate = None
        evento.ultimo_erro = None
        self._sessao.flush()

    def registrar_falha(self, id_evento: int, erro: str) -> StatusOutbox:
        """Conta a tentativa e reagenda (backoff) ou marca FALHOU após 8 tentativas.

        Devolve o novo status (PENDENTE reagendado ou FALHOU).
        """
        evento = self._sessao.get(EventoOutbox, id_evento)
        if evento is None:
            return StatusOutbox.FALHOU
        evento.tentativas += 1
        evento.ultimo_erro = erro[:1000]
        evento.bloqueado_ate = None
        if evento.tentativas >= MAX_TENTATIVAS:
            evento.status = StatusOutbox.FALHOU
        else:
            evento.status = StatusOutbox.PENDENTE
            evento.proxima_tentativa_em = _agora() + _atraso_para(evento.tentativas)
        self._sessao.flush()
        return evento.status

    # ----- consulta/admin (F6.2) -----

    def listar(
        self, *, status: StatusOutbox | None = None, page: int = 1, page_size: int = 20
    ) -> tuple[list[EventoOutbox], int]:
        consulta = select(EventoOutbox)
        contagem = select(func.count()).select_from(EventoOutbox)
        if status is not None:
            consulta = consulta.where(EventoOutbox.status == status)
            contagem = contagem.where(EventoOutbox.status == status)
        total = int(self._sessao.scalar(contagem) or 0)
        itens = self._sessao.scalars(
            consulta.order_by(EventoOutbox.id_evento.desc())
            .limit(page_size)
            .offset((page - 1) * page_size)
        ).all()
        return list(itens), total

    def contar_por_status(self) -> dict[str, int]:
        linhas = self._sessao.execute(
            select(EventoOutbox.status, func.count()).group_by(EventoOutbox.status)
        ).all()
        contagem = {s.value: 0 for s in StatusOutbox}
        for status_valor, qtd in linhas:
            chave = status_valor.value if hasattr(status_valor, "value") else str(status_valor)
            contagem[chave] = int(qtd)
        return contagem

    def reenfileirar(self, id_evento: int) -> EventoOutbox | None:
        """Volta um evento FALHOU para PENDENTE imediato (reenvio manual, admin)."""
        evento = self._sessao.get(EventoOutbox, id_evento)
        if evento is None:
            return None
        evento.status = StatusOutbox.PENDENTE
        evento.tentativas = 0
        evento.proxima_tentativa_em = _agora()
        evento.bloqueado_ate = None
        evento.ultimo_erro = None
        self._sessao.flush()
        return evento

    def obter(self, id_evento: int) -> EventoOutbox | None:
        return self._sessao.get(EventoOutbox, id_evento)
