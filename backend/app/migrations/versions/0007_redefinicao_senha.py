"""redefinicao de senha por e-mail

Revision ID: 0007
Revises: 0006
Create Date: 2026-10-18

Tabela `tokens_redefinicao_senha` (seção 5.4, F7.1 / FA02): token de redefinição
guardado como hash SHA-256, com expiração curta e uso único (`usado_em`). As
tabelas de SLA (`sla_politicas`, `chamados.prazo_sla`) entram na F7.2 (migration
0008), para manter cada recorte isolado.

O downgrade() remove a tabela (e seus índices).
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE tokens_redefinicao_senha (
          id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
          id_usuario  BIGINT NOT NULL REFERENCES usuarios (id_usuario) ON UPDATE CASCADE ON DELETE RESTRICT,
          token_hash  CHAR(64) NOT NULL,
          expira_em   TIMESTAMPTZ NOT NULL,
          usado_em    TIMESTAMPTZ,
          criado_em   TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """
    )
    op.execute(
        "CREATE UNIQUE INDEX ix_tokens_redefinicao_token_hash "
        "ON tokens_redefinicao_senha (token_hash);"
    )
    op.execute(
        "CREATE INDEX ix_tokens_redefinicao_usuario ON tokens_redefinicao_senha (id_usuario);"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS tokens_redefinicao_senha;")
