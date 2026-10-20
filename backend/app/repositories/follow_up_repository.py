"""Repositório de follow-ups (mensagens) do chamado (F4.2)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.entities.follow_up import FollowUp


class FollowUpRepository:
    def __init__(self, sessao: Session) -> None:
        self._sessao = sessao

    def criar(self, *, id_chamado: int, id_autor: int, mensagem: str) -> FollowUp:
        followup = FollowUp(id_chamado=id_chamado, id_autor=id_autor, mensagem=mensagem.strip())
        self._sessao.add(followup)
        self._sessao.flush()
        self._sessao.refresh(followup)
        return followup

    def listar_do_chamado(self, id_chamado: int) -> list[FollowUp]:
        consulta = (
            select(FollowUp)
            .where(FollowUp.id_chamado == id_chamado)
            .order_by(FollowUp.data_envio.asc(), FollowUp.id_followup.asc())
        )
        return list(self._sessao.scalars(consulta).all())
