"""Repositório dos tokens de redefinição de senha (F7.1 / FA02)."""

from __future__ import annotations

import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.entities.token_redefinicao_senha import TokenRedefinicaoSenha


class TokenRedefinicaoRepository:
    def __init__(self, sessao: Session) -> None:
        self._sessao = sessao

    def criar(
        self, *, id_usuario: int, token_hash: str, expira_em: datetime.datetime
    ) -> TokenRedefinicaoSenha:
        token = TokenRedefinicaoSenha(
            id_usuario=id_usuario, token_hash=token_hash, expira_em=expira_em
        )
        self._sessao.add(token)
        self._sessao.flush()
        return token

    def buscar_por_hash(self, token_hash: str) -> TokenRedefinicaoSenha | None:
        consulta = select(TokenRedefinicaoSenha).where(
            TokenRedefinicaoSenha.token_hash == token_hash
        )
        return self._sessao.scalars(consulta).one_or_none()

    def marcar_usado(self, token: TokenRedefinicaoSenha, quando: datetime.datetime) -> None:
        token.usado_em = quando
        self._sessao.flush()
