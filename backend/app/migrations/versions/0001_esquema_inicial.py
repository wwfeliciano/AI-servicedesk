"""esquema inicial

Revision ID: 0001
Revises:
Create Date: 2026-10-17

Produz exatamente o esquema da seção 5.2 do prompt: extensões pg_trgm/unaccent,
a função IMMUTABLE f_unaccent, os 4 tipos ENUM, as 6 tabelas (com a coluna gerada
`protocolo`, CHECKs, FKs ON DELETE RESTRICT e índices, inclusive o índice único
parcial de solução pendente e o índice trigram de título), e as 7 categorias
iniciais. O downgrade() reverte tudo, inclusive DROP TYPE, DROP FUNCTION e
DROP EXTENSION.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent;")

    # unaccent() não é IMMUTABLE; este invólucro permite usá-la em índice.
    op.execute(
        "CREATE OR REPLACE FUNCTION f_unaccent(text) RETURNS text\n"
        "LANGUAGE sql IMMUTABLE PARALLEL SAFE STRICT\n"
        "AS $$ SELECT public.unaccent('public.unaccent'::regdictionary, $1) $$;"
    )

    op.execute("CREATE TYPE perfil_usuario     AS ENUM ('ADMIN', 'ANALISTA', 'CLIENTE');")
    op.execute("CREATE TYPE severidade_chamado AS ENUM " "('BAIXA', 'MEDIA', 'ALTA', 'CRITICO');")
    op.execute(
        "CREATE TYPE status_chamado     AS ENUM "
        "('NOVO', 'PENDENTE', 'ATRIBUIDO', 'CONCLUIDO', 'FECHADO');"
    )
    op.execute(
        "CREATE TYPE status_aprovacao   AS ENUM " "('PENDENTE_APROVACAO', 'APROVADO', 'REJEITADO');"
    )

    op.execute(
        """
        CREATE TABLE usuarios (
          id_usuario    BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
          nome          VARCHAR(150) NOT NULL,
          email         VARCHAR(100) NOT NULL,
          senha_hash    VARCHAR(255) NOT NULL,
          tipo_perfil   perfil_usuario NOT NULL DEFAULT 'CLIENTE',
          cargo         VARCHAR(100),
          ativo         BOOLEAN NOT NULL DEFAULT TRUE,
          data_cadastro TIMESTAMPTZ NOT NULL DEFAULT now(),
          CONSTRAINT uq_usuarios_email UNIQUE (email),
          CONSTRAINT ck_usuarios_email_minusculo CHECK (email = lower(email))
        );
        """
    )

    op.execute(
        """
        CREATE TABLE categorias (
          id_categoria   INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
          nome_categoria VARCHAR(100) NOT NULL,
          icone          VARCHAR(16),
          ordem          SMALLINT NOT NULL DEFAULT 0,
          ativa          BOOLEAN NOT NULL DEFAULT TRUE,
          CONSTRAINT uq_categorias_nome UNIQUE (nome_categoria)
        );
        """
    )

    op.execute(
        """
        CREATE TABLE chamados (
          id_chamado             BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
          protocolo              VARCHAR(20) GENERATED ALWAYS AS
                                 ('TK-' || lpad(id_chamado::text, greatest(4, length(id_chamado::text)), '0')) STORED,
          id_usuario_abertura    BIGINT NOT NULL REFERENCES usuarios (id_usuario) ON UPDATE CASCADE ON DELETE RESTRICT,
          id_tecnico_responsavel BIGINT REFERENCES usuarios (id_usuario) ON UPDATE CASCADE ON DELETE RESTRICT,
          id_categoria           INT NOT NULL REFERENCES categorias (id_categoria) ON UPDATE CASCADE ON DELETE RESTRICT,
          titulo                 VARCHAR(150) NOT NULL,
          descricao              TEXT NOT NULL,
          severidade             severidade_chamado NOT NULL DEFAULT 'BAIXA',
          status_chamado         status_chamado NOT NULL DEFAULT 'NOVO',
          data_criacao           TIMESTAMPTZ NOT NULL DEFAULT now(),
          data_atualizacao       TIMESTAMPTZ NOT NULL DEFAULT now(),
          CONSTRAINT ck_chamados_titulo_preenchido CHECK (length(btrim(titulo)) > 0),
          CONSTRAINT ck_chamados_descricao_tamanho CHECK (length(btrim(descricao)) BETWEEN 1 AND 500),
          CONSTRAINT ck_chamados_rn03_tecnico CHECK (status_chamado IN ('NOVO', 'PENDENTE') OR id_tecnico_responsavel IS NOT NULL)
        );
        """
    )
    op.execute("CREATE UNIQUE INDEX uq_chamados_protocolo ON chamados (protocolo);")
    op.execute(
        "CREATE INDEX ix_chamados_solicitante_data "
        "ON chamados (id_usuario_abertura, data_criacao DESC);"
    )
    op.execute(
        "CREATE INDEX ix_chamados_tecnico ON chamados (id_tecnico_responsavel) "
        "WHERE id_tecnico_responsavel IS NOT NULL;"
    )
    op.execute(
        "CREATE INDEX ix_chamados_status_data " "ON chamados (status_chamado, data_criacao DESC);"
    )
    op.execute("CREATE INDEX ix_chamados_categoria ON chamados (id_categoria);")
    op.execute(
        "CREATE INDEX ix_chamados_titulo_trgm "
        "ON chamados USING gin (f_unaccent(lower(titulo)) gin_trgm_ops);"
    )

    op.execute(
        """
        CREATE TABLE follow_ups (
          id_followup BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
          id_chamado  BIGINT NOT NULL REFERENCES chamados (id_chamado) ON UPDATE CASCADE ON DELETE RESTRICT,
          id_autor    BIGINT NOT NULL REFERENCES usuarios (id_usuario) ON UPDATE CASCADE ON DELETE RESTRICT,
          mensagem    TEXT NOT NULL CHECK (length(btrim(mensagem)) > 0),
          data_envio  TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """
    )
    op.execute("CREATE INDEX ix_followups_chamado_data " "ON follow_ups (id_chamado, data_envio);")

    op.execute(
        """
        CREATE TABLE solucoes (
          id_solucao        BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
          id_chamado        BIGINT NOT NULL REFERENCES chamados (id_chamado) ON UPDATE CASCADE ON DELETE RESTRICT,
          id_analista       BIGINT NOT NULL REFERENCES usuarios (id_usuario) ON UPDATE CASCADE ON DELETE RESTRICT,
          descricao_solucao TEXT NOT NULL CHECK (length(btrim(descricao_solucao)) > 0),
          status_aprovacao  status_aprovacao NOT NULL DEFAULT 'PENDENTE_APROVACAO',
          data_solucao      TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """
    )
    op.execute("CREATE INDEX ix_solucoes_chamado ON solucoes (id_chamado);")
    op.execute(
        "CREATE UNIQUE INDEX uq_solucoes_uma_pendente ON solucoes (id_chamado) "
        "WHERE status_aprovacao = 'PENDENTE_APROVACAO';"
    )

    op.execute(
        """
        CREATE TABLE base_conhecimento (
          id_base           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
          id_solucao        BIGINT NOT NULL REFERENCES solucoes (id_solucao) ON UPDATE CASCADE ON DELETE RESTRICT,
          titulo            VARCHAR(200) NOT NULL,
          conteudo_indexado TEXT NOT NULL,
          data_inclusao     TIMESTAMPTZ NOT NULL DEFAULT now(),
          CONSTRAINT uq_base_conhecimento_solucao UNIQUE (id_solucao)
        );
        """
    )

    op.execute(
        """
        INSERT INTO categorias (nome_categoria, icone, ordem) VALUES
          ('TI', '💻', 1), ('RH', '👥', 2), ('Financeiro', '💰', 3), ('Acesso', '🔐', 4),
          ('Hardware', '🖥️', 5), ('Software', '📱', 6), ('Outro', '❓', 7);
        """
    )


def downgrade() -> None:
    # Ordem inversa: tabelas (FKs), depois tipos, função e extensões.
    op.execute("DROP TABLE IF EXISTS base_conhecimento;")
    op.execute("DROP TABLE IF EXISTS solucoes;")
    op.execute("DROP TABLE IF EXISTS follow_ups;")
    op.execute("DROP TABLE IF EXISTS chamados;")
    op.execute("DROP TABLE IF EXISTS categorias;")
    op.execute("DROP TABLE IF EXISTS usuarios;")

    op.execute("DROP TYPE IF EXISTS status_aprovacao;")
    op.execute("DROP TYPE IF EXISTS status_chamado;")
    op.execute("DROP TYPE IF EXISTS severidade_chamado;")
    op.execute("DROP TYPE IF EXISTS perfil_usuario;")

    op.execute("DROP FUNCTION IF EXISTS f_unaccent(text);")
    op.execute("DROP EXTENSION IF EXISTS unaccent;")
    op.execute("DROP EXTENSION IF EXISTS pg_trgm;")
