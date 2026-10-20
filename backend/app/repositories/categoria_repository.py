"""Repositório de categorias (consultas da F2)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.entities.categoria import Categoria


class CategoriaRepository:
    def __init__(self, sessao: Session) -> None:
        self._sessao = sessao

    def listar_ativas(self) -> list[Categoria]:
        """Categorias ativas, ordenadas por `ordem` e depois por nome (RF05)."""
        consulta = (
            select(Categoria)
            .where(Categoria.ativa.is_(True))
            .order_by(Categoria.ordem.asc(), Categoria.nome_categoria.asc())
        )
        return list(self._sessao.scalars(consulta).all())

    def buscar_ativa_por_id(self, id_categoria: int) -> Categoria | None:
        """Categoria ativa pelo id. None se não existe ou está inativa (RN04)."""
        consulta = select(Categoria).where(
            Categoria.id_categoria == id_categoria, Categoria.ativa.is_(True)
        )
        return self._sessao.scalars(consulta).one_or_none()
