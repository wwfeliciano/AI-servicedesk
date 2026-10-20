"""Dependências de autenticação e autorização do FastAPI (seção 11).

- `obter_auth_service`: monta o `AuthService` com os repositórios e o limitador.
- `usuario_atual`: exige `Authorization: Bearer <access_token>`, recarrega o usuário
  do banco e recusa se inativo. `401 NAO_AUTENTICADO` quando falta ou é inválido.
- `exigir_perfil(...)`: fábrica de dependência que exige um dos perfis (→ `403`).

O controller usa essas dependências; a regra de autorização por perfil não é
reimplementada em cada rota.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Request, status
from sqlalchemy.orm import Session

from app.core.database import obter_sessao
from app.core.errors import ErroAPI
from app.core.rate_limit import LimiteTentativasLogin
from app.core.redis import criar_cliente_redis
from app.entities.enums import PerfilUsuario
from app.entities.usuario import Usuario
from app.integrations.whatsapp.estado import EstadoBot
from app.repositories.anexo_repository import AnexoRepository
from app.repositories.base_conhecimento_repository import BaseConhecimentoRepository
from app.repositories.categoria_repository import CategoriaRepository
from app.repositories.chamado_historico_repository import HistoricoRepository
from app.repositories.chamado_repository import ChamadoRepository
from app.repositories.follow_up_repository import FollowUpRepository
from app.repositories.notificacao_repository import NotificacaoRepository
from app.repositories.outbox_repository import OutboxRepository
from app.repositories.sla_repository import SlaRepository
from app.repositories.solucao_repository import SolucaoRepository
from app.repositories.token_redefinicao_repository import TokenRedefinicaoRepository
from app.repositories.token_refresh_repository import TokenRefreshRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.services.anexo_service import AnexoService
from app.services.auth_service import AuthService, ErroAutenticacao
from app.services.base_conhecimento_service import BaseConhecimentoService
from app.services.bot_service import BotService
from app.services.chamado_service import ChamadoService
from app.services.ciclo_vida_service import CicloVidaService
from app.services.evento_service import EventoService
from app.services.notificacao_service import NotificacaoService
from app.services.outbox_service import OutboxService
from app.services.perfil_service import PerfilService
from app.services.sla_service import SlaService
from app.services.usuario_service import UsuarioService


def obter_auth_service(
    sessao: Annotated[Session, Depends(obter_sessao)],
) -> AuthService:
    from app.core.config import obter_configuracao

    config = obter_configuracao()
    usuarios = UsuarioRepository(sessao)
    return AuthService(
        usuarios=usuarios,
        tokens=TokenRefreshRepository(sessao),
        limite_login=LimiteTentativasLogin(criar_cliente_redis()),
        refresh_dias=config.jwt_refresh_dias,
        redefinicao=TokenRedefinicaoRepository(sessao),
        eventos=_montar_evento_service(sessao, usuarios),
        portal_url=config.portal_url,
    )


AuthServiceDep = Annotated[AuthService, Depends(obter_auth_service)]


def obter_usuario_service(
    sessao: Annotated[Session, Depends(obter_sessao)],
) -> UsuarioService:
    return UsuarioService(usuarios=UsuarioRepository(sessao))


UsuarioServiceDep = Annotated[UsuarioService, Depends(obter_usuario_service)]


def obter_usuario_repository(
    sessao: Annotated[Session, Depends(obter_sessao)],
) -> UsuarioRepository:
    return UsuarioRepository(sessao)


UsuarioRepositoryDep = Annotated[UsuarioRepository, Depends(obter_usuario_repository)]


def _montar_evento_service(sessao: Session, usuarios: UsuarioRepository) -> EventoService:
    """EventoService com portal + outbox (e-mail/WhatsApp), lendo o portal_url da config."""
    from app.core.config import obter_configuracao

    config = obter_configuracao()
    return EventoService(
        notificacoes=NotificacaoRepository(sessao),
        usuarios=usuarios,
        outbox=OutboxRepository(sessao),
        portal_url=config.portal_url,
    )


def obter_chamado_service(
    sessao: Annotated[Session, Depends(obter_sessao)],
) -> ChamadoService:
    usuarios = UsuarioRepository(sessao)
    eventos = _montar_evento_service(sessao, usuarios)
    return ChamadoService(
        chamados=ChamadoRepository(sessao),
        categorias=CategoriaRepository(sessao),
        usuarios=usuarios,
        eventos=eventos,
        historico=HistoricoRepository(sessao),
        sla=SlaRepository(sessao),
    )


ChamadoServiceDep = Annotated[ChamadoService, Depends(obter_chamado_service)]


def obter_sla_service(
    sessao: Annotated[Session, Depends(obter_sessao)],
) -> SlaService:
    return SlaService(sla=SlaRepository(sessao))


SlaServiceDep = Annotated[SlaService, Depends(obter_sla_service)]


def obter_notificacao_service(
    sessao: Annotated[Session, Depends(obter_sessao)],
) -> NotificacaoService:
    return NotificacaoService(notificacoes=NotificacaoRepository(sessao))


NotificacaoServiceDep = Annotated[NotificacaoService, Depends(obter_notificacao_service)]


def obter_ciclo_vida_service(
    sessao: Annotated[Session, Depends(obter_sessao)],
) -> CicloVidaService:
    usuarios = UsuarioRepository(sessao)
    eventos = _montar_evento_service(sessao, usuarios)
    return CicloVidaService(
        chamados=ChamadoRepository(sessao),
        categorias=CategoriaRepository(sessao),
        usuarios=usuarios,
        historico=HistoricoRepository(sessao),
        solucoes=SolucaoRepository(sessao),
        followups=FollowUpRepository(sessao),
        eventos=eventos,
    )


CicloVidaServiceDep = Annotated[CicloVidaService, Depends(obter_ciclo_vida_service)]


def obter_base_conhecimento_service(
    sessao: Annotated[Session, Depends(obter_sessao)],
) -> BaseConhecimentoService:
    return BaseConhecimentoService(
        base=BaseConhecimentoRepository(sessao),
        solucoes=SolucaoRepository(sessao),
    )


BaseConhecimentoServiceDep = Annotated[
    BaseConhecimentoService, Depends(obter_base_conhecimento_service)
]


def obter_outbox_service(
    sessao: Annotated[Session, Depends(obter_sessao)],
) -> OutboxService:
    return OutboxService(outbox=OutboxRepository(sessao))


OutboxServiceDep = Annotated[OutboxService, Depends(obter_outbox_service)]


def obter_perfil_service(
    sessao: Annotated[Session, Depends(obter_sessao)],
) -> PerfilService:
    from app.core.config import obter_configuracao
    from app.core.vinculo_whatsapp import VinculoWhatsApp

    config = obter_configuracao()
    return PerfilService(
        usuarios=UsuarioRepository(sessao),
        vinculo=VinculoWhatsApp(criar_cliente_redis()),
        numero_suporte=config.whatsapp_numero_suporte,
    )


PerfilServiceDep = Annotated[PerfilService, Depends(obter_perfil_service)]


def obter_bot_service(
    sessao: Annotated[Session, Depends(obter_sessao)],
) -> BotService:
    from app.core.config import obter_configuracao
    from app.core.vinculo_whatsapp import VinculoWhatsApp
    from app.integrations.whatsapp.estado import EstadoBot

    config = obter_configuracao()
    cliente_redis = criar_cliente_redis()
    usuarios = UsuarioRepository(sessao)
    chamados = ChamadoRepository(sessao)
    eventos = _montar_evento_service(sessao, usuarios)
    chamado_service = ChamadoService(
        chamados=chamados,
        categorias=CategoriaRepository(sessao),
        usuarios=usuarios,
        eventos=eventos,
        historico=HistoricoRepository(sessao),
    )
    ciclo_vida = CicloVidaService(
        chamados=chamados,
        categorias=CategoriaRepository(sessao),
        usuarios=usuarios,
        historico=HistoricoRepository(sessao),
        solucoes=SolucaoRepository(sessao),
        followups=FollowUpRepository(sessao),
        eventos=eventos,
    )
    return BotService(
        usuarios=usuarios,
        chamados=chamados,
        chamado_service=chamado_service,
        ciclo_vida=ciclo_vida,
        vinculo=VinculoWhatsApp(cliente_redis),
        estado=EstadoBot(cliente_redis),
        portal_url=config.portal_url,
    )


BotServiceDep = Annotated[BotService, Depends(obter_bot_service)]


def obter_estado_bot() -> EstadoBot:
    return EstadoBot(criar_cliente_redis())


EstadoBotDep = Annotated[EstadoBot, Depends(obter_estado_bot)]


def obter_anexo_service(
    sessao: Annotated[Session, Depends(obter_sessao)],
) -> AnexoService:
    from app.core.config import obter_configuracao
    from app.core.storage import criar_storage

    config = obter_configuracao()
    return AnexoService(
        anexos=AnexoRepository(sessao),
        chamados=ChamadoRepository(sessao),
        storage=criar_storage(config),
        max_bytes=config.anexos_max_bytes,
        max_por_chamado=config.anexos_max_por_chamado,
    )


AnexoServiceDep = Annotated[AnexoService, Depends(obter_anexo_service)]


def _extrair_bearer(request: Request) -> str:
    cabecalho = request.headers.get("Authorization", "")
    prefixo = "Bearer "
    if not cabecalho.startswith(prefixo):
        raise ErroAPI(
            status_code=status.HTTP_401_UNAUTHORIZED,
            codigo="NAO_AUTENTICADO",
            mensagem="Não autenticado.",
        )
    return cabecalho[len(prefixo) :].strip()


def usuario_atual(request: Request, auth: AuthServiceDep) -> Usuario:
    token = _extrair_bearer(request)
    try:
        return auth.usuario_do_access_token(token)
    except ErroAutenticacao as exc:
        raise ErroAPI(
            status_code=status.HTTP_401_UNAUTHORIZED,
            codigo="NAO_AUTENTICADO",
            mensagem=exc.mensagem,
        ) from exc


UsuarioAtualDep = Annotated[Usuario, Depends(usuario_atual)]


def exigir_perfil(*perfis: PerfilUsuario) -> Callable[[Usuario], Usuario]:
    """Dependência que exige que o usuário atual tenha um dos perfis dados."""
    permitidos = set(perfis)

    def _dependencia(usuario: UsuarioAtualDep) -> Usuario:
        if usuario.tipo_perfil not in permitidos:
            raise ErroAPI(
                status_code=status.HTTP_403_FORBIDDEN,
                codigo="SEM_PERMISSAO",
                mensagem="Você não tem permissão para esta ação.",
            )
        return usuario

    return _dependencia
