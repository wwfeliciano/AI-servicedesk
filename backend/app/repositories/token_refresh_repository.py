"""Repositório dos refresh tokens (seção 5.4, 11)."""

from __future__ import annotations

import datetime
import uuid
from typing import cast

from sqlalchemy import CursorResult, select, update
from sqlalchemy.orm import Session

from app.entities.token_refresh import TokenRefresh


class TokenRefreshRepository:
    def __init__(self, sessao: Session) -> None:
        self._sessao = sessao

    def criar(
        self,
        *,
        id_usuario: int,
        token_hash: str,
        familia: uuid.UUID,
        expira_em: datetime.datetime,
    ) -> TokenRefresh:
        token = TokenRefresh(
            id_usuario=id_usuario,
            token_hash=token_hash,
            familia=familia,
            expira_em=expira_em,
        )
        self._sessao.add(token)
        self._sessao.flush()
        return token

    def buscar_por_hash(self, token_hash: str) -> TokenRefresh | None:
        consulta = select(TokenRefresh).where(TokenRefresh.token_hash == token_hash)
        return self._sessao.scalars(consulta).one_or_none()

    def revogar(self, token: TokenRefresh, quando: datetime.datetime) -> None:
        token.revogado_em = quando
        self._sessao.flush()

    def revogar_familia(self, familia: uuid.UUID, quando: datetime.datetime) -> int:
        """Revoga todos os tokens ativos da família. Retorna quantos foram revogados."""
        comando = (
            update(TokenRefresh)
            .where(TokenRefresh.familia == familia, TokenRefresh.revogado_em.is_(None))
            .values(revogado_em=quando)
        )
        resultado = cast("CursorResult[object]", self._sessao.execute(comando))
        self._sessao.flush()
        return int(resultado.rowcount)

    def revogar_do_usuario(self, id_usuario: int, quando: datetime.datetime) -> int:
        """Revoga todas as sessões ativas de um usuário. Retorna quantas foram revogadas."""
        comando = (
            update(TokenRefresh)
            .where(TokenRefresh.id_usuario == id_usuario, TokenRefresh.revogado_em.is_(None))
            .values(revogado_em=quando)
        )
        resultado = cast("CursorResult[object]", self._sessao.execute(comando))
        self._sessao.flush()
        return int(resultado.rowcount)
