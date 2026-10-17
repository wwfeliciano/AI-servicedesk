"""Entidades ORM das 6 tabelas da Fase 0 (seção 5.2).

Importar este pacote registra todas as entidades no `Base.metadata`, que é o
`target_metadata` do Alembic. O esquema é criado só por migration; a API nunca
usa `metadata.create_all()`.
"""

from __future__ import annotations

from app.entities.base_conhecimento import BaseConhecimento
from app.entities.categoria import Categoria
from app.entities.chamado import Chamado
from app.entities.enums import (
    PerfilUsuario,
    SeveridadeChamado,
    StatusAprovacao,
    StatusChamado,
)
from app.entities.follow_up import FollowUp
from app.entities.solucao import Solucao
from app.entities.usuario import Usuario

__all__ = [
    "BaseConhecimento",
    "Categoria",
    "Chamado",
    "FollowUp",
    "PerfilUsuario",
    "SeveridadeChamado",
    "Solucao",
    "StatusAprovacao",
    "StatusChamado",
    "Usuario",
]
