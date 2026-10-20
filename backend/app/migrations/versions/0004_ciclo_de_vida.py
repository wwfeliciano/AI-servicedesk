"""ciclo de vida: historico_chamado e datas de conclusao/fechamento

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-17

Cria a tabela `historico_chamado` (linha do tempo das transições de status, seção
5.4) e adiciona `data_conclusao` e `data_fechamento` em `chamados`. Faz o backfill
de um evento `NOVO` (status_anterior nulo) por chamado já existente, usando a
`data_criacao` do chamado, para que a linha do tempo comece corretamente.

- `historico_chamado.id_autor` nulo = ação do sistema; `status_anterior` nulo no
  evento de criação. FKs ON DELETE RESTRICT. Índice por (id_chamado, data_evento).

O downgrade() remove a tabela e as duas colunas.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE historico_chamado (
          id_historico    BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
          id_chamado      BIGINT NOT NULL REFERENCES chamados (id_chamado) ON UPDATE CASCADE ON DELETE RESTRICT,
          id_autor        BIGINT REFERENCES usuarios (id_usuario) ON UPDATE CASCADE ON DELETE RESTRICT,
          status_anterior status_chamado,
          status_novo     status_chamado NOT NULL,
          observacao      VARCHAR(500),
          data_evento     TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """
    )
    op.execute(
        "CREATE INDEX ix_historico_chamado_data ON historico_chamado (id_chamado, data_evento);"
    )

    op.execute("ALTER TABLE chamados ADD COLUMN data_conclusao TIMESTAMPTZ;")
    op.execute("ALTER TABLE chamados ADD COLUMN data_fechamento TIMESTAMPTZ;")

    # Backfill: um evento de criação (NOVO) por chamado existente, com a data de criação.
    op.execute(
        """
        INSERT INTO historico_chamado (id_chamado, id_autor, status_anterior, status_novo,
                                       observacao, data_evento)
        SELECT id_chamado, id_usuario_abertura, NULL, 'NOVO', 'Chamado criado', data_criacao
        FROM chamados;
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE chamados DROP COLUMN IF EXISTS data_fechamento;")
    op.execute("ALTER TABLE chamados DROP COLUMN IF EXISTS data_conclusao;")
    op.execute("DROP TABLE IF EXISTS historico_chamado;")
