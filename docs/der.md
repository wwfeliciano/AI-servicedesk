# Diagrama ER

Descreve o esquema **existente** no banco, criado pela migration `0001_esquema_inicial`
(seção 5.2 do prompt). Tabelas e colunas em português, iguais ao dicionário de dados do
Documento 02. Chaves primárias são `IDENTITY` (`BIGINT`, exceto `categorias`, que é `INT`);
datas em `TIMESTAMPTZ`; FKs com `ON UPDATE CASCADE ON DELETE RESTRICT`.

Tipos ENUM nativos: `perfil_usuario`, `severidade_chamado`, `status_chamado`,
`status_aprovacao`. A coluna `chamados.protocolo` é gerada (`TK-` + id com no mínimo 4 dígitos).

```mermaid
erDiagram
    usuarios ||--o{ chamados : "abre (id_usuario_abertura)"
    usuarios ||--o{ chamados : "atende (id_tecnico_responsavel)"
    usuarios ||--o{ follow_ups : "autor"
    usuarios ||--o{ solucoes : "analista"
    categorias ||--o{ chamados : "classifica"
    chamados ||--o{ follow_ups : "recebe"
    chamados ||--o{ solucoes : "tem"
    solucoes ||--|| base_conhecimento : "publica"

    usuarios {
        bigint id_usuario PK
        varchar nome
        varchar email UK
        varchar senha_hash
        perfil_usuario tipo_perfil
        varchar cargo "nulo"
        boolean ativo
        timestamptz data_cadastro
    }

    categorias {
        int id_categoria PK
        varchar nome_categoria UK
        varchar icone "nulo"
        smallint ordem
        boolean ativa
    }

    chamados {
        bigint id_chamado PK
        varchar protocolo UK "gerada"
        bigint id_usuario_abertura FK
        bigint id_tecnico_responsavel FK "nulo"
        int id_categoria FK
        varchar titulo
        text descricao
        severidade_chamado severidade
        status_chamado status_chamado
        timestamptz data_criacao
        timestamptz data_atualizacao
    }

    follow_ups {
        bigint id_followup PK
        bigint id_chamado FK
        bigint id_autor FK
        text mensagem
        timestamptz data_envio
    }

    solucoes {
        bigint id_solucao PK
        bigint id_chamado FK
        bigint id_analista FK
        text descricao_solucao
        status_aprovacao status_aprovacao
        timestamptz data_solucao
    }

    base_conhecimento {
        bigint id_base PK
        bigint id_solucao FK "UK"
        varchar titulo
        text conteudo_indexado
        timestamptz data_inclusao
    }
```

## Invariantes no banco (defesa em profundidade)

- `usuarios`: `uq_usuarios_email` (único) e `ck_usuarios_email_minusculo` (`email = lower(email)`).
- `chamados`: `ck_chamados_titulo_preenchido`, `ck_chamados_descricao_tamanho` (1 a 500),
  `ck_chamados_rn03_tecnico` (status `ATRIBUIDO`/`CONCLUIDO`/`FECHADO` exige técnico — RN03).
- `solucoes`: `descricao_solucao` não vazia e índice único parcial `uq_solucoes_uma_pendente`
  (no máximo uma solução `PENDENTE_APROVACAO` por chamado).
- `base_conhecimento`: `uq_base_conhecimento_solucao` (uma entrada por solução).

## Índices

- `chamados`: `uq_chamados_protocolo`, `ix_chamados_solicitante_data`,
  `ix_chamados_tecnico` (parcial), `ix_chamados_status_data`, `ix_chamados_categoria` e
  `ix_chamados_titulo_trgm` (GIN trigram sobre `f_unaccent(lower(titulo))`).
- `follow_ups`: `ix_followups_chamado_data`.
- `solucoes`: `ix_solucoes_chamado` e `uq_solucoes_uma_pendente`.

Extensões `pg_trgm` e `unaccent` e a função `IMMUTABLE f_unaccent(text)` dão suporte à busca por
título sem diferenciar acento (RNF02). A busca `tsvector` da Base de Conhecimento entra na F5.
