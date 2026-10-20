"""autenticacao: tokens_refresh

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-17

Cria a tabela `tokens_refresh` (seção 5.4 do prompt), que guarda os refresh tokens
opacos como hash SHA-256 (CHAR(64)). Cada token pertence a uma `familia` (UUID): a
rotação a cada uso cria um novo token na mesma família e revoga o anterior; o reuso
de um token já rotacionado revoga a família inteira (seção 11). FK para `usuarios`
com ON DELETE RESTRICT (usuários nunca são apagados). O downgrade() remove a tabela.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE tokens_refresh (
          id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
          id_usuario  BIGINT NOT NULL REFERENCES usuarios (id_usuario) ON UPDATE CASCADE ON DELETE RESTRICT,
          token_hash  CHAR(64) NOT NULL,
          familia     UUID NOT NULL,
          expira_em   TIMESTAMPTZ NOT NULL,
          revogado_em TIMESTAMPTZ,
          criado_em   TIMESTAMPTZ NOT NULL DEFAULT now(),
          CONSTRAINT uq_tokens_refresh_token_hash UNIQUE (token_hash)
        );
        """
    )
    # Busca por família (revogação em cascata) e por usuário (logout/limpeza).
    op.execute("CREATE INDEX ix_tokens_refresh_familia ON tokens_refresh (familia);")
    op.execute("CREATE INDEX ix_tokens_refresh_usuario ON tokens_refresh (id_usuario);")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS tokens_refresh;")
