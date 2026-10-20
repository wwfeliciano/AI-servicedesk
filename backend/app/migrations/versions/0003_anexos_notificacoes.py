"""anexos e notificacoes

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-17

Cria as tabelas `anexos` e `notificacoes` (seção 5.4 do prompt).

- `anexos`: metadados do arquivo (o binário vai para o S3/MinIO). `chave_objeto`
  única; `mime_type` restrito a PNG/JPEG/PDF (CHECK, decisão B10); `tamanho_bytes`
  entre 1 e 10 MB (CHECK, decisão B9); `sha256` do conteúdo. FKs ON DELETE RESTRICT.
- `notificacoes`: notificação de portal por usuário, opcionalmente ligada a um
  chamado. Índice parcial `(id_usuario, data_criacao DESC) WHERE lida_em IS NULL`
  para a lista/contagem das não lidas (RF04).

O downgrade() remove as duas tabelas (e, com elas, seus índices e CHECKs).
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE anexos (
          id_anexo      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
          id_chamado    BIGINT NOT NULL REFERENCES chamados (id_chamado) ON UPDATE CASCADE ON DELETE RESTRICT,
          id_autor      BIGINT NOT NULL REFERENCES usuarios (id_usuario) ON UPDATE CASCADE ON DELETE RESTRICT,
          nome_original VARCHAR(255) NOT NULL,
          chave_objeto  VARCHAR(500) NOT NULL,
          mime_type     VARCHAR(100) NOT NULL,
          tamanho_bytes BIGINT NOT NULL,
          sha256        CHAR(64) NOT NULL,
          data_envio    TIMESTAMPTZ NOT NULL DEFAULT now(),
          CONSTRAINT ck_anexos_mime_type
            CHECK (mime_type IN ('image/png', 'image/jpeg', 'application/pdf')),
          CONSTRAINT ck_anexos_tamanho CHECK (tamanho_bytes BETWEEN 1 AND 10485760)
        );
        """
    )
    op.execute("CREATE UNIQUE INDEX uq_anexos_chave_objeto ON anexos (chave_objeto);")
    op.execute("CREATE INDEX ix_anexos_chamado ON anexos (id_chamado);")

    op.execute(
        """
        CREATE TABLE notificacoes (
          id_notificacao BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
          id_usuario     BIGINT NOT NULL REFERENCES usuarios (id_usuario) ON UPDATE CASCADE ON DELETE RESTRICT,
          id_chamado     BIGINT REFERENCES chamados (id_chamado) ON UPDATE CASCADE ON DELETE RESTRICT,
          tipo           VARCHAR(50) NOT NULL,
          titulo         VARCHAR(150) NOT NULL,
          mensagem       VARCHAR(500) NOT NULL,
          lida_em        TIMESTAMPTZ,
          data_criacao   TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """
    )
    op.execute(
        "CREATE INDEX ix_notificacoes_nao_lidas ON notificacoes (id_usuario, data_criacao DESC) "
        "WHERE lida_em IS NULL;"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS notificacoes;")
    op.execute("DROP TABLE IF EXISTS anexos;")
