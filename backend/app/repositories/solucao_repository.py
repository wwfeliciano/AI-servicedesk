"""Repositório de soluções do chamado (F4.2)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.entities.enums import StatusAprovacao
from app.entities.solucao import Solucao


class SolucaoRepository:
    def __init__(self, sessao: Session) -> None:
        self._sessao = sessao

    def criar(self, *, id_chamado: int, id_analista: int, descricao_solucao: str) -> Solucao:
        """Cria a solução com status PENDENTE_APROVACAO (padrão do banco)."""
        solucao = Solucao(
            id_chamado=id_chamado,
            id_analista=id_analista,
            descricao_solucao=descricao_solucao.strip(),
        )
        self._sessao.add(solucao)
        self._sessao.flush()
        self._sessao.refresh(solucao)
        return solucao

    def buscar_por_id(self, id_solucao: int) -> Solucao | None:
        return self._sessao.get(Solucao, id_solucao)

    def buscar_pendente(self, id_chamado: int) -> Solucao | None:
        """A (única) solução PENDENTE_APROVACAO do chamado, se houver."""
        consulta = select(Solucao).where(
            Solucao.id_chamado == id_chamado,
            Solucao.status_aprovacao == StatusAprovacao.PENDENTE_APROVACAO,
        )
        return self._sessao.scalars(consulta).one_or_none()

    def listar_do_chamado(self, id_chamado: int) -> list[Solucao]:
        consulta = (
            select(Solucao)
            .where(Solucao.id_chamado == id_chamado)
            .order_by(Solucao.data_solucao.asc(), Solucao.id_solucao.asc())
        )
        return list(self._sessao.scalars(consulta).all())
