"""Controllers de notificações do portal (F3.2, RF04).

- GET  /api/notificacoes            → lista as do usuário (não lidas primeiro)
- GET  /api/notificacoes/contagem   → contador de não lidas (badge do menu)
- POST /api/notificacoes/{id}/lida  → marca uma como lida
- POST /api/notificacoes/lidas      → marca todas como lidas

Escopo: cada usuário vê e marca só as suas (o service filtra por `id_usuario`).
A rota fixa `/contagem` e `/lidas` vêm antes da paramétrica `/{id}` (seção 7.1).
"""

from __future__ import annotations

import datetime
from typing import Annotated

from fastapi import APIRouter, Query, Response, status
from pydantic import BaseModel

from app.controllers.dependencias import NotificacaoServiceDep, UsuarioAtualDep
from app.core.errors import ErroAPI
from app.entities.notificacao import Notificacao
from app.services.notificacao_service import ErroNotificacao

router = APIRouter(prefix="/api/notificacoes", tags=["notificacoes"])


class NotificacaoSaida(BaseModel):
    id_notificacao: int
    id_chamado: int | None
    tipo: str
    titulo: str
    mensagem: str
    lida: bool
    data_criacao: datetime.datetime


class ListaNotificacoes(BaseModel):
    items: list[NotificacaoSaida]
    total: int
    nao_lidas: int
    page: int
    page_size: int


class ContagemSaida(BaseModel):
    nao_lidas: int


def _saida(n: Notificacao) -> NotificacaoSaida:
    return NotificacaoSaida(
        id_notificacao=n.id_notificacao,
        id_chamado=n.id_chamado,
        tipo=n.tipo,
        titulo=n.titulo,
        mensagem=n.mensagem,
        lida=n.lida_em is not None,
        data_criacao=n.data_criacao,
    )


@router.get("", response_model=ListaNotificacoes, summary="Lista as notificações do usuário")
def listar(
    servico: NotificacaoServiceDep,
    usuario: UsuarioAtualDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 20,
) -> ListaNotificacoes:
    pagina = servico.listar(id_usuario=usuario.id_usuario, page=page, page_size=page_size)
    return ListaNotificacoes(
        items=[_saida(n) for n in pagina.items],
        total=pagina.total,
        nao_lidas=pagina.nao_lidas,
        page=pagina.page,
        page_size=pagina.page_size,
    )


@router.get("/contagem", response_model=ContagemSaida, summary="Contador de não lidas")
def contagem(servico: NotificacaoServiceDep, usuario: UsuarioAtualDep) -> ContagemSaida:
    return ContagemSaida(nao_lidas=servico.contar_nao_lidas(id_usuario=usuario.id_usuario))


@router.post(
    "/lidas",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Marca todas as notificações como lidas",
)
def marcar_todas(
    servico: NotificacaoServiceDep, usuario: UsuarioAtualDep, response: Response
) -> Response:
    servico.marcar_todas_lidas(id_usuario=usuario.id_usuario)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.post(
    "/{id_notificacao}/lida",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Marca uma notificação como lida",
)
def marcar_lida(
    id_notificacao: int,
    servico: NotificacaoServiceDep,
    usuario: UsuarioAtualDep,
    response: Response,
) -> Response:
    try:
        servico.marcar_lida(id_usuario=usuario.id_usuario, id_notificacao=id_notificacao)
    except ErroNotificacao as exc:
        raise ErroAPI(
            status_code=status.HTTP_404_NOT_FOUND, codigo=exc.codigo, mensagem=exc.mensagem
        ) from exc
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
