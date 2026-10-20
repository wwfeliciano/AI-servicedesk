"""sla: politicas e prazo por chamado

Revision ID: 0008
Revises: 0007
Create Date: 2026-10-18

SLA (seção 7.2, F7.2; decisão B20): tabela `sla_politicas` com o prazo por
severidade (horas corridas) e a coluna `chamados.prazo_sla` (prazo-alvo gravado na
abertura). Metas padrão: CRITICO 4 h · ALTA 8 h · MEDIA 24 h · BAIXA 72 h,
ajustáveis na tabela.

O downgrade() remove a coluna e a tabela.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE sla_politicas (
          severidade  severidade_chamado PRIMARY KEY,
          prazo_horas INTEGER NOT NULL CHECK (prazo_horas > 0)
        );
        """
    )
    # Metas padrão (decisão B20).
    op.execute(
        """
        INSERT INTO sla_politicas (severidade, prazo_horas) VALUES
          ('CRITICO', 4),
          ('ALTA', 8),
          ('MEDIA', 24),
          ('BAIXA', 72);
        """
    )
    op.execute("ALTER TABLE chamados ADD COLUMN prazo_sla TIMESTAMPTZ;")


def downgrade() -> None:
    op.execute("ALTER TABLE chamados DROP COLUMN IF EXISTS prazo_sla;")
    op.execute("DROP TABLE IF EXISTS sla_politicas;")
