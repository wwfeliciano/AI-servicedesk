"""busca full-text da base de conhecimento

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-17

Habilita a busca full-text da Base de Conhecimento (seção 5.4 do prompt, F5):

- configuração de busca `pt_br_unaccent` (cópia de `portuguese`), com o mapeamento
  de palavras passando por `unaccent` + `portuguese_stem` (busca sem acento);
- coluna gerada `busca` (tsvector) em `base_conhecimento`: título com peso A e
  conteúdo com peso B; índice GIN para o `@@`.

O downgrade() remove o índice, a coluna e a configuração de busca.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE TEXT SEARCH CONFIGURATION pt_br_unaccent (COPY = portuguese);")
    op.execute(
        """
        ALTER TEXT SEARCH CONFIGURATION pt_br_unaccent
          ALTER MAPPING FOR hword, hword_part, word WITH unaccent, portuguese_stem;
        """
    )
    op.execute(
        """
        ALTER TABLE base_conhecimento ADD COLUMN busca tsvector GENERATED ALWAYS AS (
          setweight(to_tsvector('pt_br_unaccent', titulo), 'A') ||
          setweight(to_tsvector('pt_br_unaccent', conteudo_indexado), 'B')
        ) STORED;
        """
    )
    op.execute("CREATE INDEX ix_base_conhecimento_busca ON base_conhecimento USING gin (busca);")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_base_conhecimento_busca;")
    op.execute("ALTER TABLE base_conhecimento DROP COLUMN IF EXISTS busca;")
    op.execute("DROP TEXT SEARCH CONFIGURATION IF EXISTS pt_br_unaccent;")
