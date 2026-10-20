"""Controllers da Base de Conhecimento (F5; RF06, RN05, UC04).

- GET  /api/base-conhecimento        → busca (`q`) + filtro por categoria, paginado
- GET  /api/base-conhecimento/{id}   → detalhe do artigo
- POST /api/base-conhecimento        → publica a partir de uma solução aprovada (RN05)
- PATCH /api/base-conhecimento/{id}  → edita título/conteúdo

Leitura: qualquer autenticado. Escrita (POST/PATCH): ANALISTA/ADMIN (dependência
por rota). `ErroBaseConhecimento` vira o formato único de erro (seção 7.1).
"""

from __future__ import annotations

import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel

from app.controllers.dependencias import (
    BaseConhecimentoServiceDep,
    exigir_perfil,
    usuario_atual,
)
from app.core.errors import ErroAPI
from app.entities.enums import PerfilUsuario
from app.repositories.base_conhecimento_repository import LinhaArtigo
from app.services.base_conhecimento_service import ErroBaseConhecimento

# Leitura: qualquer autenticado.
router = APIRouter(
    prefix="/api/base-conhecimento",
    tags=["base-conhecimento"],
    dependencies=[Depends(usuario_atual)],
)
# Escrita: ANALISTA/ADMIN (router à parte, mesmo prefixo).
router_escrita = APIRouter(
    prefix="/api/base-conhecimento",
    tags=["base-conhecimento"],
    dependencies=[Depends(exigir_perfil(PerfilUsuario.ANALISTA, PerfilUsuario.ADMIN))],
)

_STATUS_POR_CODIGO = {
    "NAO_ENCONTRADO": status.HTTP_404_NOT_FOUND,
    "SOLUCAO_NAO_APROVADA": status.HTTP_409_CONFLICT,
    "DUPLICADO": status.HTTP_409_CONFLICT,
    "VALIDACAO": status.HTTP_422_UNPROCESSABLE_ENTITY,
}


class ArtigoCategoria(BaseModel):
    id_categoria: int
    nome_categoria: str
    icone: str | None = None


class ArtigoSaida(BaseModel):
    id_base: int
    id_solucao: int
    titulo: str
    conteudo: str
    categoria: ArtigoCategoria
    data_inclusao: datetime.datetime


class PaginaArtigosSaida(BaseModel):
    items: list[ArtigoSaida]
    total: int
    page: int
    page_size: int


class ArtigoCriar(BaseModel):
    id_solucao: int
    titulo: str
    conteudo: str


class ArtigoEditar(BaseModel):
    titulo: str | None = None
    conteudo: str | None = None


def _erro_http(exc: ErroBaseConhecimento) -> ErroAPI:
    status_code = _STATUS_POR_CODIGO.get(exc.codigo, status.HTTP_409_CONFLICT)
    campos = {exc.campo: exc.mensagem} if exc.campo else None
    return ErroAPI(status_code=status_code, codigo=exc.codigo, mensagem=exc.mensagem, campos=campos)


def _saida(linha: LinhaArtigo) -> ArtigoSaida:
    a = linha.artigo
    return ArtigoSaida(
        id_base=a.id_base,
        id_solucao=a.id_solucao,
        titulo=a.titulo,
        conteudo=a.conteudo_indexado,
        categoria=ArtigoCategoria(
            id_categoria=linha.id_categoria,
            nome_categoria=linha.nome_categoria,
            icone=linha.icone,
        ),
        data_inclusao=a.data_inclusao,
    )


@router.get("", response_model=PaginaArtigosSaida, summary="Busca/lista artigos (autenticado)")
def listar(
    servico: BaseConhecimentoServiceDep,
    q: Annotated[str | None, Query(max_length=150)] = None,
    id_categoria: Annotated[int | None, Query(ge=1)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 10,
) -> PaginaArtigosSaida:
    pagina = servico.buscar(q=q, id_categoria=id_categoria, page=page, page_size=page_size)
    return PaginaArtigosSaida(
        items=[_saida(linha) for linha in pagina.items],
        total=pagina.total,
        page=pagina.page,
        page_size=pagina.page_size,
    )


@router.get("/{id_base}", response_model=ArtigoSaida, summary="Detalhe do artigo (autenticado)")
def obter(id_base: int, servico: BaseConhecimentoServiceDep) -> ArtigoSaida:
    try:
        linha = servico.obter(id_base)
    except ErroBaseConhecimento as exc:
        raise _erro_http(exc) from exc
    return _saida(linha)


@router_escrita.post(
    "",
    response_model=ArtigoSaida,
    status_code=status.HTTP_201_CREATED,
    summary="Publica a partir de uma solução aprovada (ANALISTA/ADMIN, RN05)",
)
def publicar(dados: ArtigoCriar, servico: BaseConhecimentoServiceDep) -> ArtigoSaida:
    try:
        artigo = servico.publicar(
            id_solucao=dados.id_solucao, titulo=dados.titulo, conteudo=dados.conteudo
        )
        linha = servico.obter(artigo.id_base)
    except ErroBaseConhecimento as exc:
        raise _erro_http(exc) from exc
    return _saida(linha)


@router_escrita.patch(
    "/{id_base}", response_model=ArtigoSaida, summary="Edita o artigo (ANALISTA/ADMIN)"
)
def editar(id_base: int, dados: ArtigoEditar, servico: BaseConhecimentoServiceDep) -> ArtigoSaida:
    try:
        servico.editar(id_base=id_base, titulo=dados.titulo, conteudo=dados.conteudo)
        linha = servico.obter(id_base)
    except ErroBaseConhecimento as exc:
        raise _erro_http(exc) from exc
    return _saida(linha)
