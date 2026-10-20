"""Controllers de usuários (UC01, RF01, RN07; seção 7.2).

Todas as rotas exigem perfil ADMIN (não há auto-cadastro, decisão B1):

- POST /api/usuarios        → cadastra um usuário (201)
- GET  /api/usuarios        → lista paginada (`q`, `perfil`, `ativo`, `page`, `page_size`)
- GET  /api/usuarios/{id}   → detalhe

O controller traduz HTTP ↔ service e converte `ErroUsuario` no formato único de
erro (seção 7.1). A regra de negócio (RN07, TU05/TU06) fica no `UsuarioService`.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.controllers.dependencias import (
    UsuarioAtualDep,
    UsuarioRepositoryDep,
    UsuarioServiceDep,
    exigir_perfil,
)
from app.controllers.schemas_usuarios import (
    PaginaUsuariosSaida,
    TecnicoSaida,
    UsuarioAtualizar,
    UsuarioCriar,
    UsuarioDetalhe,
)
from app.core.errors import ErroAPI
from app.entities.enums import PerfilUsuario
from app.entities.usuario import Usuario
from app.services.usuario_service import ErroUsuario

# Toda a rota exige ADMIN; a dependência roda antes do corpo e devolve 401/403.
router = APIRouter(
    prefix="/api/usuarios",
    tags=["usuarios"],
    dependencies=[Depends(exigir_perfil(PerfilUsuario.ADMIN))],
)

# Técnicos para atribuição (RN03): ANALISTA e ADMIN podem consultar. Router à parte
# para não herdar o guard de ADMIN do router acima. Declarado antes de /{id_usuario}.
router_tecnicos = APIRouter(
    prefix="/api/usuarios",
    tags=["usuarios"],
    dependencies=[Depends(exigir_perfil(PerfilUsuario.ANALISTA, PerfilUsuario.ADMIN))],
)


@router_tecnicos.get(
    "/tecnicos", response_model=list[TecnicoSaida], summary="Técnicos ativos (ANALISTA/ADMIN)"
)
def listar_tecnicos(repo: UsuarioRepositoryDep) -> list[TecnicoSaida]:
    return [
        TecnicoSaida(id_usuario=u.id_usuario, nome=u.nome, tipo_perfil=u.tipo_perfil)
        for u in repo.listar_tecnicos_ativos()
    ]


# Código de domínio → status HTTP do contrato (seção 7.1).
_STATUS_POR_CODIGO = {
    "EMAIL_DUPLICADO": status.HTTP_409_CONFLICT,
    "VALIDACAO": status.HTTP_422_UNPROCESSABLE_ENTITY,
    "NAO_ENCONTRADO": status.HTTP_404_NOT_FOUND,
}


def _erro_http(exc: ErroUsuario) -> ErroAPI:
    status_code = _STATUS_POR_CODIGO.get(exc.codigo, status.HTTP_400_BAD_REQUEST)
    campos = {exc.campo: exc.mensagem} if exc.campo else None
    return ErroAPI(status_code=status_code, codigo=exc.codigo, mensagem=exc.mensagem, campos=campos)


def _detalhe(usuario: Usuario) -> UsuarioDetalhe:
    return UsuarioDetalhe(
        id_usuario=usuario.id_usuario,
        nome=usuario.nome,
        email=usuario.email,
        tipo_perfil=usuario.tipo_perfil,
        cargo=usuario.cargo,
        ativo=usuario.ativo,
        data_cadastro=usuario.data_cadastro,
    )


@router.post(
    "",
    response_model=UsuarioDetalhe,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra um usuário (ADMIN)",
)
def cadastrar(dados: UsuarioCriar, servico: UsuarioServiceDep) -> UsuarioDetalhe:
    try:
        usuario = servico.cadastrar(
            nome=dados.nome,
            email=str(dados.email),
            senha=dados.senha,
            tipo_perfil=dados.tipo_perfil,
            cargo=dados.cargo,
        )
    except ErroUsuario as exc:
        raise _erro_http(exc) from exc
    return _detalhe(usuario)


@router.get("", response_model=PaginaUsuariosSaida, summary="Lista usuários (ADMIN)")
def listar(
    servico: UsuarioServiceDep,
    q: Annotated[str | None, Query(max_length=100)] = None,
    perfil: PerfilUsuario | None = None,
    ativo: bool | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 10,
) -> PaginaUsuariosSaida:
    pagina = servico.listar(q=q, perfil=perfil, ativo=ativo, page=page, page_size=page_size)
    return PaginaUsuariosSaida(
        items=[_detalhe(u) for u in pagina.items],
        total=pagina.total,
        page=pagina.page,
        page_size=pagina.page_size,
    )


@router.get("/{id_usuario}", response_model=UsuarioDetalhe, summary="Detalhe (ADMIN)")
def obter(id_usuario: int, servico: UsuarioServiceDep) -> UsuarioDetalhe:
    try:
        usuario = servico.obter(id_usuario)
    except ErroUsuario as exc:
        raise _erro_http(exc) from exc
    return _detalhe(usuario)


@router.patch(
    "/{id_usuario}", response_model=UsuarioDetalhe, summary="Atualiza/ativa/desativa (ADMIN)"
)
def atualizar(
    id_usuario: int,
    dados: UsuarioAtualizar,
    servico: UsuarioServiceDep,
    ator: UsuarioAtualDep,
) -> UsuarioDetalhe:
    try:
        usuario = servico.atualizar(
            id_usuario=id_usuario,
            id_ator=ator.id_usuario,
            nome=dados.nome,
            cargo=dados.cargo,
            tipo_perfil=dados.tipo_perfil,
            ativo=dados.ativo,
        )
    except ErroUsuario as exc:
        raise _erro_http(exc) from exc
    return _detalhe(usuario)
