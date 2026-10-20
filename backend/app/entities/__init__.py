"""Entidades ORM das 6 tabelas da Fase 0 (seção 5.2).

Importar este pacote registra todas as entidades no `Base.metadata`, que é o
`target_metadata` do Alembic. O esquema é criado só por migration; a API nunca
usa `metadata.create_all()`.
"""

from __future__ import annotations

from app.entities.anexo import Anexo
from app.entities.base_conhecimento import BaseConhecimento
from app.entities.categoria import Categoria
from app.entities.chamado import Chamado
from app.entities.enums import (
    CanalNotificacao,
    CanalOrigem,
    PerfilUsuario,
    SeveridadeChamado,
    StatusAprovacao,
    StatusChamado,
    StatusOutbox,
)
from app.entities.eventos_outbox import EventoOutbox
from app.entities.follow_up import FollowUp
from app.entities.historico_chamado import HistoricoChamado
from app.entities.notificacao import Notificacao
from app.entities.sla_politica import SlaPolitica
from app.entities.solucao import Solucao
from app.entities.token_redefinicao_senha import TokenRedefinicaoSenha
from app.entities.token_refresh import TokenRefresh
from app.entities.usuario import Usuario

__all__ = [
    "Anexo",
    "BaseConhecimento",
    "CanalNotificacao",
    "CanalOrigem",
    "Categoria",
    "Chamado",
    "EventoOutbox",
    "FollowUp",
    "HistoricoChamado",
    "Notificacao",
    "PerfilUsuario",
    "SeveridadeChamado",
    "SlaPolitica",
    "Solucao",
    "StatusAprovacao",
    "StatusChamado",
    "StatusOutbox",
    "TokenRedefinicaoSenha",
    "TokenRefresh",
    "Usuario",
]
