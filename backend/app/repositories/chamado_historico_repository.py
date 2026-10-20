"""Repositório do histórico de status do chamado (F4.1)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.entities.enums import StatusChamado
from app.entities.historico_chamado import HistoricoChamado


class HistoricoRepository:
    def __init__(self, sessao: Session) -> None:
        self._sessao = sessao

    def registrar(
        self,
        *,
        id_chamado: int,
        status_anterior: StatusChamado | None,
        status_novo: StatusChamado,
        id_autor: int | None,
        observacao: str | None = None,
    ) -> HistoricoChamado:
        evento = HistoricoChamado(
            id_chamado=id_chamado,
            id_autor=id_autor,
            status_anterior=status_anterior,
            status_novo=status_novo,
            observacao=observacao,
        )
        self._sessao.add(evento)
        self._sessao.flush()
        return evento

    def listar_do_chamado(self, id_chamado: int) -> list[HistoricoChamado]:
        consulta = (
            select(HistoricoChamado)
            .where(HistoricoChamado.id_chamado == id_chamado)
            .order_by(HistoricoChamado.data_evento.asc(), HistoricoChamado.id_historico.asc())
        )
        return list(self._sessao.scalars(consulta).all())
