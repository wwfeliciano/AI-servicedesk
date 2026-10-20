"""Repositório da Base de Conhecimento (F5.1).

A busca full-text usa a configuração `pt_br_unaccent` (migration 0005):
`busca @@ websearch_to_tsquery(...)` ordenado por `ts_rank`. A categoria do artigo
vem por join `base_conhecimento → solucoes → chamados → categorias` (a tabela da
base não guarda a categoria diretamente).
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import ColumnElement, Row, Select, func, select
from sqlalchemy.orm import Session

from app.entities.base_conhecimento import BaseConhecimento
from app.entities.categoria import Categoria
from app.entities.chamado import Chamado
from app.entities.solucao import Solucao

_CONFIG = "pt_br_unaccent"


@dataclass(frozen=True)
class LinhaArtigo:
    """Artigo + categoria (derivada via join) para montar a resposta."""

    artigo: BaseConhecimento
    id_categoria: int
    nome_categoria: str
    icone: str | None


class BaseConhecimentoRepository:
    def __init__(self, sessao: Session) -> None:
        self._sessao = sessao

    def existe_por_solucao(self, id_solucao: int) -> bool:
        return (
            self._sessao.scalar(
                select(func.count())
                .select_from(BaseConhecimento)
                .where(BaseConhecimento.id_solucao == id_solucao)
            )
            or 0
        ) > 0

    def criar(self, *, id_solucao: int, titulo: str, conteudo_indexado: str) -> BaseConhecimento:
        artigo = BaseConhecimento(
            id_solucao=id_solucao,
            titulo=titulo.strip(),
            conteudo_indexado=conteudo_indexado.strip(),
        )
        self._sessao.add(artigo)
        self._sessao.flush()
        self._sessao.refresh(artigo)
        return artigo

    def obter(self, id_base: int) -> LinhaArtigo | None:
        consulta = self._base_join().where(BaseConhecimento.id_base == id_base)
        linha = self._sessao.execute(consulta).one_or_none()
        return self._linha(linha) if linha is not None else None

    def obter_simples(self, id_base: int) -> BaseConhecimento | None:
        return self._sessao.get(BaseConhecimento, id_base)

    def flush(self) -> None:
        """Descarrega mudanças pendentes (ex.: edição de artigo)."""
        self._sessao.flush()

    def listar(
        self,
        *,
        q: str | None = None,
        id_categoria: int | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[LinhaArtigo], int]:
        cond = self._condicoes(q=q, id_categoria=id_categoria)

        total = int(self._sessao.scalar(self._contagem_join().where(*cond)) or 0)

        consulta = self._base_join().where(*cond)
        if q and q.strip():
            rank = func.ts_rank(BaseConhecimento.busca, self._tsquery(q))
            consulta = consulta.order_by(rank.desc(), BaseConhecimento.data_inclusao.desc())
        else:
            consulta = consulta.order_by(BaseConhecimento.data_inclusao.desc())
        consulta = consulta.limit(page_size).offset((page - 1) * page_size)

        linhas = [self._linha(r) for r in self._sessao.execute(consulta).all()]
        return linhas, total

    # ----- internos -----
    def _tsquery(self, q: str) -> ColumnElement[bool]:
        return func.websearch_to_tsquery(_CONFIG, q.strip())

    def _condicoes(self, *, q: str | None, id_categoria: int | None) -> list[ColumnElement[bool]]:
        cond: list[ColumnElement[bool]] = []
        if q and q.strip():
            cond.append(BaseConhecimento.busca.op("@@")(self._tsquery(q)))
        if id_categoria is not None:
            cond.append(Chamado.id_categoria == id_categoria)
        return cond

    def _base_join(self) -> Select[tuple[BaseConhecimento, int, str, str | None]]:
        return (
            select(
                BaseConhecimento,
                Categoria.id_categoria,
                Categoria.nome_categoria,
                Categoria.icone,
            )
            .join(Solucao, BaseConhecimento.id_solucao == Solucao.id_solucao)
            .join(Chamado, Solucao.id_chamado == Chamado.id_chamado)
            .join(Categoria, Chamado.id_categoria == Categoria.id_categoria)
        )

    def _contagem_join(self) -> Select[tuple[int]]:
        return (
            select(func.count())
            .select_from(BaseConhecimento)
            .join(Solucao, BaseConhecimento.id_solucao == Solucao.id_solucao)
            .join(Chamado, Solucao.id_chamado == Chamado.id_chamado)
            .join(Categoria, Chamado.id_categoria == Categoria.id_categoria)
        )

    @staticmethod
    def _linha(r: Row[tuple[BaseConhecimento, int, str, str | None]]) -> LinhaArtigo:
        artigo, id_cat, nome_cat, icone = r
        return LinhaArtigo(artigo=artigo, id_categoria=id_cat, nome_categoria=nome_cat, icone=icone)
