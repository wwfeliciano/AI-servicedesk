"""Repositório de notificações do portal (F3.2)."""

from __future__ import annotations

import datetime
from typing import Any, cast

from sqlalchemy import CursorResult, func, select, update
from sqlalchemy.orm import Session

from app.entities.notificacao import Notificacao


class NotificacaoRepository:
    def __init__(self, sessao: Session) -> None:
        self._sessao = sessao

    def criar(
        self,
        *,
        id_usuario: int,
        tipo: str,
        titulo: str,
        mensagem: str,
        id_chamado: int | None = None,
    ) -> Notificacao:
        notificacao = Notificacao(
            id_usuario=id_usuario,
            id_chamado=id_chamado,
            tipo=tipo,
            titulo=titulo,
            mensagem=mensagem,
        )
        self._sessao.add(notificacao)
        self._sessao.flush()
        return notificacao

    def listar_do_usuario(
        self, id_usuario: int, *, page: int = 1, page_size: int = 20
    ) -> tuple[list[Notificacao], int]:
        """Notificações do usuário, não lidas primeiro e mais recentes primeiro."""
        base = select(Notificacao).where(Notificacao.id_usuario == id_usuario)
        total = int(
            self._sessao.scalar(
                select(func.count())
                .select_from(Notificacao)
                .where(Notificacao.id_usuario == id_usuario)
            )
            or 0
        )
        consulta = (
            base.order_by(
                Notificacao.lida_em.is_(None).desc(),  # não lidas primeiro
                Notificacao.data_criacao.desc(),
                Notificacao.id_notificacao.desc(),
            )
            .limit(page_size)
            .offset((page - 1) * page_size)
        )
        return list(self._sessao.scalars(consulta).all()), total

    def contar_nao_lidas(self, id_usuario: int) -> int:
        return int(
            self._sessao.scalar(
                select(func.count())
                .select_from(Notificacao)
                .where(Notificacao.id_usuario == id_usuario, Notificacao.lida_em.is_(None))
            )
            or 0
        )

    def marcar_lida(self, id_notificacao: int, id_usuario: int, agora: datetime.datetime) -> bool:
        """Marca uma notificação do usuário como lida. False se não for dele/inexistente."""
        resultado = cast(
            "CursorResult[Any]",
            self._sessao.execute(
                update(Notificacao)
                .where(
                    Notificacao.id_notificacao == id_notificacao,
                    Notificacao.id_usuario == id_usuario,
                    Notificacao.lida_em.is_(None),
                )
                .values(lida_em=agora)
            ),
        )
        # rowcount > 0 quando marcou; 0 se já estava lida, não existe ou é de outro.
        return bool(resultado.rowcount)

    def existe_do_usuario(self, id_notificacao: int, id_usuario: int) -> bool:
        return (
            self._sessao.scalar(
                select(func.count())
                .select_from(Notificacao)
                .where(
                    Notificacao.id_notificacao == id_notificacao,
                    Notificacao.id_usuario == id_usuario,
                )
            )
            or 0
        ) > 0

    def marcar_todas_lidas(self, id_usuario: int, agora: datetime.datetime) -> int:
        """Marca todas as não lidas do usuário como lidas. Devolve quantas."""
        resultado = cast(
            "CursorResult[Any]",
            self._sessao.execute(
                update(Notificacao)
                .where(Notificacao.id_usuario == id_usuario, Notificacao.lida_em.is_(None))
                .values(lida_em=agora)
            ),
        )
        return int(resultado.rowcount or 0)
