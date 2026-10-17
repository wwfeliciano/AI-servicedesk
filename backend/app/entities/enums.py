"""ENUMs de domínio e os tipos nativos do PostgreSQL correspondentes.

Os quatro tipos ENUM (`perfil_usuario`, `severidade_chamado`, `status_chamado`,
`status_aprovacao`) são criados e removidos **explicitamente** na migration
`0001_esquema_inicial` (seção 5.1 do prompt). Por isso as colunas referenciam o
tipo com `create_type=False`: o SQLAlchemy não tenta criar nem apagar o tipo ao
emitir o `CREATE TABLE`.
"""

from __future__ import annotations

import enum

from sqlalchemy.dialects.postgresql import ENUM


class PerfilUsuario(str, enum.Enum):
    ADMIN = "ADMIN"
    ANALISTA = "ANALISTA"
    CLIENTE = "CLIENTE"


class SeveridadeChamado(str, enum.Enum):
    BAIXA = "BAIXA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"
    CRITICO = "CRITICO"


class StatusChamado(str, enum.Enum):
    NOVO = "NOVO"
    PENDENTE = "PENDENTE"
    ATRIBUIDO = "ATRIBUIDO"
    CONCLUIDO = "CONCLUIDO"
    FECHADO = "FECHADO"


class StatusAprovacao(str, enum.Enum):
    PENDENTE_APROVACAO = "PENDENTE_APROVACAO"
    APROVADO = "APROVADO"
    REJEITADO = "REJEITADO"


# Nome do tipo igual ao do SQL; os valores gravados são os `.value` dos membros.
# create_type=False: o ciclo de vida do tipo é da migration, não do metadata.
perfil_usuario_enum = ENUM(
    PerfilUsuario,
    name="perfil_usuario",
    create_type=False,
    values_callable=lambda membros: [m.value for m in membros],
)
severidade_chamado_enum = ENUM(
    SeveridadeChamado,
    name="severidade_chamado",
    create_type=False,
    values_callable=lambda membros: [m.value for m in membros],
)
status_chamado_enum = ENUM(
    StatusChamado,
    name="status_chamado",
    create_type=False,
    values_callable=lambda membros: [m.value for m in membros],
)
status_aprovacao_enum = ENUM(
    StatusAprovacao,
    name="status_aprovacao",
    create_type=False,
    values_callable=lambda membros: [m.value for m in membros],
)
