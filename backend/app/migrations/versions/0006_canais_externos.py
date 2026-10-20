"""canais externos (outbox, whatsapp, e-mail)

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-17

Base de dados dos canais externos (seção 9, F6). Ainda sem SMTP/WAHA: só o
esquema e o outbox transacional.

- ENUMs `canal_notificacao` (WHATSAPP/EMAIL), `status_outbox`
  (PENDENTE/PROCESSANDO/ENVIADO/FALHOU) e `canal_origem` (PORTAL/WHATSAPP);
- `usuarios`: `whatsapp_chat_id`/`whatsapp_lid` (únicos quando preenchidos),
  `whatsapp_numero`, `whatsapp_opt_in` (padrão false), `whatsapp_consentimento_em`
  e `notificar_email` (padrão true);
- `chamados`: `canal_origem` (padrão PORTAL);
- tabela `eventos_outbox` (seção 9.2), com índice parcial da fila.

O downgrade() desfaz tudo, inclusive os `DROP TYPE`.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE TYPE canal_notificacao AS ENUM ('WHATSAPP', 'EMAIL');")
    op.execute(
        "CREATE TYPE status_outbox AS ENUM ('PENDENTE', 'PROCESSANDO', 'ENVIADO', 'FALHOU');"
    )
    op.execute("CREATE TYPE canal_origem AS ENUM ('PORTAL', 'WHATSAPP');")

    op.execute(
        """
        ALTER TABLE usuarios
          ADD COLUMN whatsapp_chat_id          VARCHAR(64),
          ADD COLUMN whatsapp_lid              VARCHAR(64),
          ADD COLUMN whatsapp_numero           VARCHAR(20),
          ADD COLUMN whatsapp_opt_in           BOOLEAN     NOT NULL DEFAULT false,
          ADD COLUMN whatsapp_consentimento_em TIMESTAMPTZ,
          ADD COLUMN notificar_email           BOOLEAN     NOT NULL DEFAULT true;
        """
    )
    op.execute(
        "ALTER TABLE usuarios "
        "ADD CONSTRAINT uq_usuarios_whatsapp_chat_id UNIQUE (whatsapp_chat_id);"
    )
    op.execute(
        "ALTER TABLE usuarios ADD CONSTRAINT uq_usuarios_whatsapp_lid UNIQUE (whatsapp_lid);"
    )

    op.execute(
        "ALTER TABLE chamados " "ADD COLUMN canal_origem canal_origem NOT NULL DEFAULT 'PORTAL';"
    )

    op.execute(
        """
        CREATE TABLE eventos_outbox (
          id_evento            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
          tipo                 VARCHAR(60) NOT NULL,
          canal                canal_notificacao NOT NULL,
          destino              VARCHAR(255) NOT NULL,
          payload              JSONB NOT NULL,
          status               status_outbox NOT NULL DEFAULT 'PENDENTE',
          tentativas           SMALLINT NOT NULL DEFAULT 0,
          proxima_tentativa_em TIMESTAMPTZ NOT NULL DEFAULT now(),
          bloqueado_ate        TIMESTAMPTZ,
          ultimo_erro          TEXT,
          criado_em            TIMESTAMPTZ NOT NULL DEFAULT now(),
          enviado_em           TIMESTAMPTZ
        );
        """
    )
    op.execute(
        "CREATE INDEX ix_eventos_outbox_fila ON eventos_outbox (proxima_tentativa_em) "
        "WHERE status IN ('PENDENTE', 'PROCESSANDO');"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS eventos_outbox;")
    op.execute("ALTER TABLE chamados DROP COLUMN IF EXISTS canal_origem;")
    op.execute("ALTER TABLE usuarios DROP CONSTRAINT IF EXISTS uq_usuarios_whatsapp_lid;")
    op.execute("ALTER TABLE usuarios DROP CONSTRAINT IF EXISTS uq_usuarios_whatsapp_chat_id;")
    op.execute(
        """
        ALTER TABLE usuarios
          DROP COLUMN IF EXISTS notificar_email,
          DROP COLUMN IF EXISTS whatsapp_consentimento_em,
          DROP COLUMN IF EXISTS whatsapp_opt_in,
          DROP COLUMN IF EXISTS whatsapp_numero,
          DROP COLUMN IF EXISTS whatsapp_lid,
          DROP COLUMN IF EXISTS whatsapp_chat_id;
        """
    )
    op.execute("DROP TYPE IF EXISTS canal_origem;")
    op.execute("DROP TYPE IF EXISTS status_outbox;")
    op.execute("DROP TYPE IF EXISTS canal_notificacao;")
