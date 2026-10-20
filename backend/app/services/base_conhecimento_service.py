"""Service da Base de Conhecimento (F5; RF06, RN05, UC04).

RN05: um artigo só é publicado **a partir de uma solução APROVADA** e há no máximo
um artigo por solução. A escrita (publicar/editar) é de ANALISTA/ADMIN (garantido
no controller). A leitura (busca/detalhe) é de qualquer autenticado.

Não conhece HTTP: levanta `ErroBaseConhecimento` com código estável.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.entities.base_conhecimento import BaseConhecimento
from app.entities.enums import StatusAprovacao
from app.repositories.base_conhecimento_repository import BaseConhecimentoRepository, LinhaArtigo
from app.repositories.solucao_repository import SolucaoRepository


class ErroBaseConhecimento(Exception):
    def __init__(self, codigo: str, mensagem: str, campo: str | None = None) -> None:
        super().__init__(mensagem)
        self.codigo = codigo
        self.mensagem = mensagem
        self.campo = campo


@dataclass(frozen=True)
class PaginaArtigos:
    items: list[LinhaArtigo]
    total: int
    page: int
    page_size: int


class BaseConhecimentoService:
    def __init__(
        self,
        *,
        base: BaseConhecimentoRepository,
        solucoes: SolucaoRepository,
    ) -> None:
        self._base = base
        self._solucoes = solucoes

    def buscar(
        self,
        *,
        q: str | None = None,
        id_categoria: int | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> PaginaArtigos:
        itens, total = self._base.listar(
            q=q, id_categoria=id_categoria, page=page, page_size=page_size
        )
        return PaginaArtigos(items=itens, total=total, page=page, page_size=page_size)

    def obter(self, id_base: int) -> LinhaArtigo:
        linha = self._base.obter(id_base)
        if linha is None:
            raise ErroBaseConhecimento("NAO_ENCONTRADO", "Artigo não encontrado.")
        return linha

    def publicar(self, *, id_solucao: int, titulo: str, conteudo: str) -> BaseConhecimento:
        """Publica um artigo a partir de uma solução APROVADA (RN05)."""
        if not titulo.strip():
            raise ErroBaseConhecimento("VALIDACAO", "O título é obrigatório.", campo="titulo")
        if not conteudo.strip():
            raise ErroBaseConhecimento("VALIDACAO", "O conteúdo é obrigatório.", campo="conteudo")

        solucao = self._solucoes.buscar_por_id(id_solucao)
        if solucao is None:
            raise ErroBaseConhecimento(
                "NAO_ENCONTRADO", "Solução não encontrada.", campo="id_solucao"
            )
        # RN05: só de solução APROVADA.
        if solucao.status_aprovacao != StatusAprovacao.APROVADO:
            raise ErroBaseConhecimento(
                "SOLUCAO_NAO_APROVADA",
                "Só é possível publicar a partir de uma solução aprovada.",
                campo="id_solucao",
            )
        # Uma entrada por solução.
        if self._base.existe_por_solucao(id_solucao):
            raise ErroBaseConhecimento(
                "DUPLICADO", "Esta solução já foi publicada na base.", campo="id_solucao"
            )
        return self._base.criar(id_solucao=id_solucao, titulo=titulo, conteudo_indexado=conteudo)

    def editar(
        self, *, id_base: int, titulo: str | None = None, conteudo: str | None = None
    ) -> BaseConhecimento:
        artigo = self._base.obter_simples(id_base)
        if artigo is None:
            raise ErroBaseConhecimento("NAO_ENCONTRADO", "Artigo não encontrado.")
        if titulo is not None:
            if not titulo.strip():
                raise ErroBaseConhecimento(
                    "VALIDACAO", "O título não pode ficar vazio.", campo="titulo"
                )
            artigo.titulo = titulo.strip()
        if conteudo is not None:
            if not conteudo.strip():
                raise ErroBaseConhecimento(
                    "VALIDACAO", "O conteúdo não pode ficar vazio.", campo="conteudo"
                )
            artigo.conteudo_indexado = conteudo.strip()
        self._base.flush()
        return artigo
