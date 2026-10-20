# Prompt de Implementação — Mentory Help Desk

> **Versão 1.0 · 16/10/2026**
> Backend Python (FastAPI) · Front-end React + TypeScript · PostgreSQL · Redis · S3 (SeaweedFS) · n8n + WAHA · tudo em Docker
> **Custo de licenciamento: zero** (ver seção 3.3)

---

## Como usar este pacote (para o time)

1. Extraia o pacote na raiz do repositório `mentory-helpdesk/`. Ele contém:
   - `docs/PROMPT_IMPLEMENTACAO.md`: este arquivo, com a especificação completa e as instruções para o agente de código.
   - `docs/requisitos/`: Documentos 01, 02 e 03 convertidos para Markdown.
   - `docs/prototipo/`: as 6 capturas de tela do Documento 01, usadas só como referência visual.
2. Na raiz do repositório, abra o agente de código (Claude Code ou equivalente) e envie a mensagem da Fase 0 do Apêndice A.
3. Ao fim de cada fase o agente para e entrega um relatório (seção 15). Revisem, abram o PR para `develop` e enviem a mensagem da fase seguinte.

---

## 1. Papel, objetivo e contexto

Você é um engenheiro de software full-stack sênior (Python, TypeScript, PostgreSQL, Docker). Implemente do zero, em fases, o **Mentory Help Desk**: portal corporativo para abertura, acompanhamento e resolução de chamados, com três perfis — **CLIENTE** (solicitante), **ANALISTA** (técnico) e **ADMIN** — e notificações/atendimento por e-mail e WhatsApp.

É um projeto acadêmico (CEUNSP, Ciência da Computação, disciplina Análise e Projeto de Sistemas). A avaliação cobra **rastreabilidade**: os códigos dos documentos (RF, RNF, RN, UC, UJ, FA, FE, TU) precisam aparecer em código, testes, commits e documentação.

**Precedência das fontes**

1. Este prompt: stack, arquitetura, modelo de dados, contratos de API, integração e fases. Ele substitui a stack citada no Documento 02 (NestJS/TypeORM/Jest) e mantém a mesma arquitetura em camadas.
2. `docs/requisitos/*.md`: regras de negócio, telas, jornadas e critérios de aceite.
3. `docs/prototipo/*.png`: só referência visual. Não existe código de protótipo para reaproveitar; todas as telas são implementadas do zero, em código.

Lacunas ou conflitos: aplique o padrão da seção 14, registre em `docs/DECISOES.md` e siga em frente. Não invente requisitos.

**Fora do escopo:** multiempresa (multi-tenant), app móvel nativo, chat em tempo real por WebSocket, anexos recebidos pelo WhatsApp, integração com LDAP/AD, SLA em horário comercial, exportação de relatórios.

## 2. Regras de trabalho (obrigatórias)

1. **Uma fase por vez** (seção 13). Ao concluir: rode lint, testes e build; atualize `README.md` e `docs/`; entregue o relatório da seção 15 e **pare**. Só comece a fase seguinte quando o time pedir.
2. **Custo zero de licença.** Use só software gratuito e de código aberto. Antes de adicionar qualquer dependência, confira a licença. Aceitas: MIT, BSD, Apache-2.0, ISC, MPL-2.0, PostgreSQL, Unlicense, OFL (fontes) e LGPL (biblioteca usada sem modificação), além das exceções avaliadas na seção 3.3. **Proibido:** SaaS ou API paga; recurso que exija license key; Figma; MinIO; imagens Bitnami; biblioteca "open core" cujo recurso necessário seja pago. Na dúvida, pergunte antes.
3. **Versões fixas.** Nunca use a tag `latest`. Fixe imagens Docker por versão e commite os lockfiles (`uv.lock`, `package-lock.json`).
4. **Rastreabilidade.** Cite os códigos nas docstrings dos services, nos nomes dos testes (`test_tu03_...`), nos commits e em `docs/RASTREABILIDADE.md`.
5. **Qualidade.** Type hints em todo o Python; `ruff check`, `ruff format --check` e `mypy` sem erros; TypeScript em modo `strict`; ESLint sem erros. Nenhuma regra de negócio em controller, componente de UI ou workflow do n8n.
6. **Segredos** só no `.env`, fora do Git. Versione o `.env.example` com placeholders.
7. **Idioma e nomes.** Interface, mensagens e documentação em PT-BR. Identificadores de domínio em português sem acento, iguais ao dicionário de dados (`chamado`, `id_usuario_abertura`, `status_chamado`); sufixos técnicos em inglês (`ChamadoService`, `ChamadoRepository`). Commits no padrão Conventional Commits citando o código: `feat(chamados): RN04 exige categoria e solicitante ativo`.
8. **Esquema só por migration.** Toda mudança no banco é uma migration Alembic. Nunca use `metadata.create_all()`; os testes também sobem o esquema via Alembic.

## 3. Stack

### 3.1 Tecnologias e licenças

| Camada | Tecnologia | Licença |
|---|---|---|
| Backend | Python 3.13 · FastAPI · Pydantic v2 · pydantic-settings · Uvicorn · SQLAlchemy 2.0 (síncrono) + psycopg 3 · Alembic · PyJWT · bcrypt · python-multipart · filetype · boto3 · redis-py · httpx · Typer | MIT, BSD, Apache-2.0, LGPL (psycopg) |
| Qualidade backend | uv · Ruff · mypy · pytest · pytest-cov · moto · fakeredis · Faker | MIT, Apache-2.0, BSD |
| Front-end | TypeScript · React 19 · Vite · React Router 7 · TanStack Query 5 · Zustand · React Hook Form + Zod · Tailwind CSS 4 · shadcn/ui (Radix) · lucide-react · date-fns · openapi-typescript + openapi-fetch · sonner · qrcode | MIT, ISC, Apache-2.0 |
| Fontes | IBM Plex Sans e IBM Plex Mono via `@fontsource`, auto-hospedadas (sem CDN) | OFL-1.1 |
| Testes front | Vitest · Testing Library · MSW · Playwright | MIT, Apache-2.0 |
| Banco | PostgreSQL 17 + extensões `pg_trgm` e `unaccent` | PostgreSQL |
| Estado efêmero | Redis 8 (ou Valkey 8, substituto direto) | AGPLv3 (Valkey: BSD) |
| Arquivos (anexos e backups) | SeaweedFS com API S3 | Apache-2.0 |
| Automação | n8n Community (self-hosted) | Sustainable Use License |
| WhatsApp | WAHA ≥ 2026.6.1 (imagem pública) | Apache-2.0 |
| Proxy e HTTPS | Nginx no container `web` · Traefik v3 + Let's Encrypt em produção | BSD-2, MIT |
| E-mail em dev | Mailpit | MIT |
| Contêineres | Docker Engine + Compose v2 | Apache-2.0 |
| CI | GitHub Actions | gratuito dentro dos limites do plano |

SQLAlchemy síncrono foi escolhido de propósito: é mais simples de testar, o FastAPI executa rotas síncronas em threadpool e o volume do sistema atende o RNF02 com folga.

### 3.2 Por que React + TypeScript no front-end

- O Documento 02 já define uma SPA React/TypeScript desacoplada da API REST. Só o backend muda.
- O FastAPI gera o OpenAPI automaticamente e o front gera os tipos TypeScript a partir dele (`openapi-typescript`). O contrato Python ↔ TypeScript passa a ser verificado na compilação.
- As telas pedem interação rica: wizard de 3 etapas com validação por etapa, busca em tempo real, abas com contadores, badge de notificações, upload com arrastar e soltar, menu lateral que vira gaveta no celular.
- É o maior ecossistema gratuito (shadcn/ui, Radix, TanStack), com testes E2E maduros (Playwright).
- Alternativa avaliada e descartada: HTMX + Jinja2 (tudo em Python). É mais simples, mas foge da arquitetura documentada (SPA com state management) e complica o wizard e os estados de interface.

### 3.3 Licenças que pedem atenção (já avaliadas)

- **Redis 8** usa AGPLv3 (tri-licença). Não tem custo, e a AGPL só gera obrigação se vocês modificarem o próprio Redis e o oferecerem pela rede. Quem preferir licença permissiva usa **Valkey** (BSD): mesmo protocolo e mesma biblioteca cliente, troca só a imagem.
- **n8n** usa a Sustainable Use License: gratuito para uso interno da organização, inclusive self-hosted em produção. Não é permitido oferecer o n8n como serviço para terceiros criarem ou editarem workflows. Use só recursos da edição Community, sem license key: nada de Variables, SSO, Source Control/Environments, External Secrets ou Log Streaming.
- **WAHA**: a partir da versão 2026.6.1, tudo o que era do Plus (sessões ilimitadas, mídia, storages, API key, health checks e métricas) está na imagem pública gratuita. Não é preciso assinar nada.
- **MinIO: não usar.** O Community Edition parou de publicar binários e imagens em outubro de 2025, entrou em modo só de manutenção em dezembro de 2025 e teve o repositório arquivado em abril de 2026; o substituto oficial (AIStor) é proprietário. O código usa a API S3 genérica (boto3), então trocar SeaweedFS por Garage, AWS S3 ou outro compatível é só configuração.
- **Imagens Bitnami: não usar.** A Bitnami restringiu o catálogo gratuito em 2025. Use imagens oficiais.
- **Docker Desktop** só é gratuito para uso pessoal, projetos open source não comerciais e empresas com **menos de 250 funcionários e menos de US$ 10 milhões** de receita anual. No servidor, use Docker Engine no Linux (gratuito). Em estações fora dessas condições, use Docker Engine no WSL2, Rancher Desktop ou Podman Desktop.
- **GitHub**: proteção de branch com revisão obrigatória em repositório **privado** exige GitHub Pro ou Team. Opções sem custo: repositório público, ou repositório privado na conta pessoal de um aluno com GitHub Pro gratuito pelo GitHub Education (Student Developer Pack). O GitHub Actions oferece 2.000 min/mês em repositório privado no plano Free e é ilimitado em repositório público.

### 3.4 Equivalência com o Documento 02 (NestJS → Python)

| Documento 02 | Nesta implementação |
|---|---|
| Controllers (endpoints) | `backend/app/controllers/` — `APIRouter` do FastAPI |
| Services (regras de negócio) | `backend/app/services/` — Python puro, sem importar FastAPI |
| Repositories / DAO | `backend/app/repositories/` — SQLAlchemy 2.0 |
| Entities (6 tabelas) | `backend/app/entities/` — modelos ORM |
| DTOs (validação de entrada) | `backend/app/dtos/` — schemas Pydantic v2 |
| Migrations (TypeORM) | `backend/migrations/` — Alembic |
| Jest / Supertest | pytest + `TestClient` (httpx); no front, Vitest |
| `npm run migration:run` | `make migrate` (`alembic upgrade head`) |
| `npm run test` | `make test` |
| `npm run build` | `make build` |

## 4. Arquitetura

### 4.1 Visão geral

```text
Navegador ──HTTPS──▶ web (Nginx: SPA + proxy /api) ──▶ api (FastAPI)
                                                         ├──▶ db     PostgreSQL (dados + outbox)
                                                         ├──▶ redis  estado efêmero com TTL
                                                         └──▶ s3     SeaweedFS (anexos e backups)

Saída:    worker ──lê o outbox──▶ n8n ──▶ waha ──▶ WhatsApp
                                     └──▶ SMTP ──▶ e-mail
Entrada:  WhatsApp ──▶ waha ──webhook──▶ n8n ──▶ api (/api/integracoes/whatsapp/mensagens)
          a api devolve as respostas do bot ──▶ n8n ──▶ waha ──▶ WhatsApp
```

Princípios:

- **Camadas** (Documento 02): controller → service → repository → entity. O service recebe os repositórios por injeção e não conhece HTTP; é nele que vivem RN01–RN07 e os testes unitários.
- **PostgreSQL guarda tudo o que precisa ser durável ou transacional. Redis guarda só estado efêmero, sempre com TTL** (conversa do bot, códigos de vínculo, limite de tentativas, deduplicação). Se o Redis for zerado, nada importante se perde.
- **Outbox transacional**: a mudança de estado e o evento de notificação são gravados na mesma transação, e o `worker` entrega ao n8n com retentativas. Nenhuma notificação se perde se o n8n ou o WAHA estiverem fora do ar.
- **O n8n é transporte, não regra.** Regras, textos das mensagens e estado da conversa ficam no backend, versionados e testados. O n8n recebe e entrega mensagens, filtra eventos, faz as pausas anti-bloqueio, envia e-mail e alerta falhas.
- **Arquivos fora do banco**: anexos ficam no S3 (SeaweedFS) e o banco guarda só os metadados. O download sempre passa pela API, que confere a permissão; o S3 nunca é exposto.

### 4.2 Estrutura de pastas

```text
mentory-helpdesk/
├── docker-compose.yml               # base: serviços, redes e volumes
├── docker-compose.override.yml      # dev: portas, hot reload, Mailpit
├── docker-compose.prod.yml          # prod: labels do Traefik, sem portas publicadas
├── .env.example
├── Makefile
├── README.md
├── AGENTS.md                        # regras permanentes para agentes (resumo da seção 2)
├── CLAUDE.md                        # contém apenas: @AGENTS.md
├── .github/
│   ├── workflows/ci.yml
│   └── pull_request_template.md
├── docs/
│   ├── PROMPT_IMPLEMENTACAO.md
│   ├── DECISOES.md                  # decisões no formato ADR curto
│   ├── RASTREABILIDADE.md           # RF/RNF/RN/UC → telas, endpoints e testes
│   ├── der.md                       # DER em Mermaid (erDiagram)
│   ├── requisitos/
│   └── prototipo/
├── infra/
│   ├── postgres/init/01-n8n.sh      # cria banco e usuário do n8n
│   ├── seaweedfs/entrypoint.sh      # gera o s3.json a partir do .env e inicia o servidor
│   └── nginx/default.conf
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── alembic.ini
│   ├── migrations/                  # env.py + versions/
│   ├── app/
│   │   ├── main.py                  # create_app(): routers, middlewares, handlers
│   │   ├── core/                    # config, database, security, redis, storage, errors, logging
│   │   ├── controllers/             # rotas finas: valida → chama o service → responde
│   │   ├── services/                # regras de negócio (RN01–RN07)
│   │   ├── repositories/
│   │   ├── entities/
│   │   ├── dtos/
│   │   ├── integrations/            # outbox, bot do WhatsApp, textos das mensagens
│   │   ├── worker.py                # despacho do outbox + tarefas periódicas
│   │   └── cli.py                   # criar-admin, seed, seed-performance
│   └── tests/
│       ├── unit/
│       ├── integration/
│       ├── conftest.py
│       └── factories.py
├── frontend/
│   ├── Dockerfile                   # build com Node → Nginx
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── src/
│   │   ├── pages/                   # telas da seção 8.4
│   │   ├── components/              # AppShell, StatusBadge, SeveridadeBadge...
│   │   ├── services/                # cliente da API (tipos gerados do OpenAPI)
│   │   ├── state/                   # Zustand: sessão e rascunho do wizard
│   │   ├── hooks/
│   │   ├── lib/
│   │   ├── styles/
│   │   ├── router.tsx
│   │   └── main.tsx
│   └── e2e/                         # Playwright
└── integrations/
    ├── n8n/workflows/*.json         # workflows exportados (importáveis, sem credenciais)
    ├── n8n/README.md
    └── waha/README.md               # sessão, QR code, webhook, número dedicado
```

## 5. Modelo de dados

### 5.1 Convenções

- Nomes de tabelas e colunas iguais ao dicionário de dados do Documento 02 (snake_case, em português).
- Chave primária `BIGINT GENERATED ALWAYS AS IDENTITY` (em `categorias`, `INT`). No SQLAlchemy, `Identity(always=True)`.
- Datas em `TIMESTAMPTZ`, gravadas em UTC e exibidas em `America/Sao_Paulo`.
- ENUMs nativos do PostgreSQL para perfil, severidade, status e aprovação, criados e removidos **explicitamente** na migration (`postgresql.ENUM(..., create_type=False)` nas colunas) para o `downgrade()` funcionar. Tipos de evento e de notificação ficam em `VARCHAR`, para novos tipos não exigirem migration de ENUM.
- Chaves estrangeiras com `ON DELETE RESTRICT`. Usuários e chamados nunca são apagados; a exclusão é lógica, pela coluna `ativo`.
- Invariantes também no banco (CHECK e índice único parcial), como defesa em profundidade. A validação principal e as mensagens de erro ficam na API.

### 5.2 Migration `0001_esquema_inicial` (Fase 0)

O SQL abaixo foi executado e validado no PostgreSQL. A migration Alembic deve produzir exatamente este esquema (use `op.execute` para extensões, função, coluna gerada e índices de expressão) e ter um `downgrade()` completo, incluindo os `DROP TYPE`.

```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;

-- unaccent() não é IMMUTABLE; este invólucro permite usá-la em índice
CREATE OR REPLACE FUNCTION f_unaccent(text) RETURNS text
LANGUAGE sql IMMUTABLE PARALLEL SAFE STRICT
AS $$ SELECT public.unaccent('public.unaccent'::regdictionary, $1) $$;

CREATE TYPE perfil_usuario     AS ENUM ('ADMIN', 'ANALISTA', 'CLIENTE');
CREATE TYPE severidade_chamado AS ENUM ('BAIXA', 'MEDIA', 'ALTA', 'CRITICO');
CREATE TYPE status_chamado     AS ENUM ('NOVO', 'PENDENTE', 'ATRIBUIDO', 'CONCLUIDO', 'FECHADO');
CREATE TYPE status_aprovacao   AS ENUM ('PENDENTE_APROVACAO', 'APROVADO', 'REJEITADO');

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

CREATE TABLE categorias (
  id_categoria   INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  nome_categoria VARCHAR(100) NOT NULL,
  icone          VARCHAR(16),
  ordem          SMALLINT NOT NULL DEFAULT 0,
  ativa          BOOLEAN NOT NULL DEFAULT TRUE,
  CONSTRAINT uq_categorias_nome UNIQUE (nome_categoria)
);

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
CREATE UNIQUE INDEX uq_chamados_protocolo ON chamados (protocolo);
CREATE INDEX ix_chamados_solicitante_data ON chamados (id_usuario_abertura, data_criacao DESC);
CREATE INDEX ix_chamados_tecnico ON chamados (id_tecnico_responsavel) WHERE id_tecnico_responsavel IS NOT NULL;
CREATE INDEX ix_chamados_status_data ON chamados (status_chamado, data_criacao DESC);
CREATE INDEX ix_chamados_categoria ON chamados (id_categoria);
CREATE INDEX ix_chamados_titulo_trgm ON chamados USING gin (f_unaccent(lower(titulo)) gin_trgm_ops);

CREATE TABLE follow_ups (
  id_followup BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  id_chamado  BIGINT NOT NULL REFERENCES chamados (id_chamado) ON UPDATE CASCADE ON DELETE RESTRICT,
  id_autor    BIGINT NOT NULL REFERENCES usuarios (id_usuario) ON UPDATE CASCADE ON DELETE RESTRICT,
  mensagem    TEXT NOT NULL CHECK (length(btrim(mensagem)) > 0),
  data_envio  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_followups_chamado_data ON follow_ups (id_chamado, data_envio);

CREATE TABLE solucoes (
  id_solucao        BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  id_chamado        BIGINT NOT NULL REFERENCES chamados (id_chamado) ON UPDATE CASCADE ON DELETE RESTRICT,
  id_analista       BIGINT NOT NULL REFERENCES usuarios (id_usuario) ON UPDATE CASCADE ON DELETE RESTRICT,
  descricao_solucao TEXT NOT NULL CHECK (length(btrim(descricao_solucao)) > 0),
  status_aprovacao  status_aprovacao NOT NULL DEFAULT 'PENDENTE_APROVACAO',
  data_solucao      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_solucoes_chamado ON solucoes (id_chamado);
CREATE UNIQUE INDEX uq_solucoes_uma_pendente ON solucoes (id_chamado) WHERE status_aprovacao = 'PENDENTE_APROVACAO';

CREATE TABLE base_conhecimento (
  id_base           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  id_solucao        BIGINT NOT NULL REFERENCES solucoes (id_solucao) ON UPDATE CASCADE ON DELETE RESTRICT,
  titulo            VARCHAR(200) NOT NULL,
  conteudo_indexado TEXT NOT NULL,
  data_inclusao     TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_base_conhecimento_solucao UNIQUE (id_solucao)
);

INSERT INTO categorias (nome_categoria, icone, ordem) VALUES
  ('TI', '💻', 1), ('RH', '👥', 2), ('Financeiro', '💰', 3), ('Acesso', '🔐', 4),
  ('Hardware', '🖥️', 5), ('Software', '📱', 6), ('Outro', '❓', 7);
```

No SQLAlchemy, mapeie `protocolo` com `Computed(..., persisted=True)` (somente leitura) e monte a busca com `func.f_unaccent(func.lower(Chamado.titulo))`. A expressão precisa ser idêntica à do índice para ele ser usado.

### 5.3 Diferenças em relação ao Documento 02 (registrar em `docs/DECISOES.md`)

| Mudança | Motivo |
|---|---|
| `usuarios.ativo` | RN04 e TU02 exigem "solicitante ativo"; também é a exclusão lógica prevista |
| `usuarios.cargo` (opcional) | O protótipo mostra o cargo abaixo do nome ("Analista de Marketing") |
| `chamados.protocolo` (coluna gerada) | Busca por protocolo com índice; formato estável acima de 9999 (`TK-12345`) |
| `chamados.data_atualizacao` | Os cards exibem "Atualizado: dd/mm/aa" |
| `categorias.icone`, `ordem` e `ativa` | Grade de categorias montada pelo banco; desativar sem apagar (FK) |
| CHECKs e índice único parcial em `solucoes` | Invariantes da RN03, do TU04 e de "uma solução pendente por chamado" |
| `TIMESTAMPTZ` em vez de `TIMESTAMP` | Evita erro de fuso horário |
| Extensões `pg_trgm` e `unaccent` + `f_unaccent()` | Busca por título em tempo real, sem diferenciar acento, dentro do RNF02 |

### 5.4 Migrations seguintes

| Migration (fase) | Conteúdo |
|---|---|
| `0002_autenticacao` (F1) | `tokens_refresh`: `id`, `id_usuario` (FK), `token_hash` CHAR(64) UNIQUE (SHA-256), `familia` UUID, `expira_em`, `revogado_em`, `criado_em` |
| `0003_anexos_notificacoes` (F3) | `anexos`: `id_anexo`, `id_chamado` (FK), `id_autor` (FK), `nome_original` VARCHAR(255), `chave_objeto` VARCHAR(500) UNIQUE, `mime_type` (CHECK em `image/png`, `image/jpeg`, `application/pdf`), `tamanho_bytes` (CHECK de 1 a 10485760), `sha256` CHAR(64), `data_envio`. `notificacoes`: `id_notificacao`, `id_usuario` (FK), `id_chamado` (FK, nulo), `tipo` VARCHAR(50), `titulo` VARCHAR(150), `mensagem` VARCHAR(500), `lida_em` (nulo), `data_criacao`, com índice parcial `(id_usuario, data_criacao DESC) WHERE lida_em IS NULL` |
| `0004_ciclo_de_vida` (F4) | `historico_chamado`: `id_historico`, `id_chamado` (FK), `id_autor` (FK, nulo = sistema), `status_anterior`, `status_novo`, `observacao` VARCHAR(500), `data_evento`, com backfill de um registro `NOVO` por chamado existente. Em `chamados`: `data_conclusao` e `data_fechamento` |
| `0005_busca_base_conhecimento` (F5) | Configuração de busca `pt_br_unaccent`, coluna gerada `busca` e índice GIN (SQL abaixo) |
| `0006_canais_externos` (F6) | Em `usuarios`: `whatsapp_chat_id` VARCHAR(64) UNIQUE, `whatsapp_lid` VARCHAR(64) UNIQUE, `whatsapp_numero` VARCHAR(20), `whatsapp_opt_in` BOOLEAN (padrão `false`), `whatsapp_consentimento_em`, `notificar_email` BOOLEAN (padrão `true`). ENUM `canal_origem` (`PORTAL`, `WHATSAPP`) em `chamados.canal_origem` (padrão `PORTAL`). Tabela `eventos_outbox` (seção 9.2) |
| `0007_sla_senha` (F7) | `sla_politicas` (`severidade` PK, `prazo_horas`); `chamados.prazo_sla`; `tokens_redefinicao_senha` (`id`, `id_usuario`, `token_hash`, `expira_em`, `usado_em`, `criado_em`) |

Busca da base de conhecimento (migration 0005, também validada):

```sql
CREATE TEXT SEARCH CONFIGURATION pt_br_unaccent (COPY = portuguese);
ALTER TEXT SEARCH CONFIGURATION pt_br_unaccent
  ALTER MAPPING FOR hword, hword_part, word WITH unaccent, portuguese_stem;

ALTER TABLE base_conhecimento ADD COLUMN busca tsvector GENERATED ALWAYS AS (
  setweight(to_tsvector('pt_br_unaccent', titulo), 'A') ||
  setweight(to_tsvector('pt_br_unaccent', conteudo_indexado), 'B')
) STORED;
CREATE INDEX ix_base_conhecimento_busca ON base_conhecimento USING gin (busca);

-- Consulta: WHERE busca @@ websearch_to_tsquery('pt_br_unaccent', :q)
--           ORDER BY ts_rank(busca, websearch_to_tsquery('pt_br_unaccent', :q)) DESC
```

### 5.5 Redis (estado efêmero)

| Chave (com prefixo `REDIS_PREFIXO`) | Conteúdo | TTL |
|---|---|---|
| `rl:login:ip:{ip}` e `rl:login:email:{email}` | Tentativas de login | 15 min |
| `rl:wa:{chat_id}` | Mensagens recebidas por minuto (anti-loop) | 60 s |
| `wa:msg:{message_id}` | Deduplicação de webhook (`SET NX`) | 24 h |
| `wa:conversa:{chat_id}` | Estado do bot (JSON com a etapa e os dados parciais) | 30 min, renovado a cada mensagem |
| `wa:vinculo:{sha256(codigo)}` | `id_usuario` aguardando vínculo | 10 min |
| `cache:categorias` | Categorias ativas | 5 min (invalidar ao alterar) |
| `worker:heartbeat` | Último ciclo do worker (usado no healthcheck) | 30 s |

### 5.6 Armazenamento de objetos (S3)

- Buckets privados: `mentory-anexos` e `mentory-backups`.
- Chave do objeto: `chamados/{id_chamado}/{uuid4}.{ext}`. O nome original fica só no banco.
- Cliente `boto3` com `endpoint_url` configurável, `addressing_style="path"` e `signature_version="s3v4"`. Se o servidor recusar os checksums automáticos do boto3 (versão 1.36 em diante), configure `request_checksum_calculation="when_required"` e `response_checksum_validation="when_required"`.
- A API cria os buckets no startup se não existirem (operação idempotente).
- Interface `StorageService` (`salvar`, `abrir_stream`, `remover`): trocar de provedor é só configuração.

### 5.7 Dados iniciais

- Categorias: inseridas pela migration 0001 (TI, RH, Financeiro, Acesso, Hardware, Software, Outro).
- Primeiro ADMIN: `make criar-admin`, que lê `ADMIN_NOME`, `ADMIN_EMAIL` e `ADMIN_SENHA` do `.env` e não duplica se já existir.
- `make seed` (só em dev): 1 admin, 3 analistas e 10 clientes — entre eles "Ana Lima, Analista de Marketing" e o analista "Rafael Mendes", como no protótipo — e cerca de 60 chamados variados.
- `make seed-performance`: 10.000 chamados e 200 usuários, para medir o RNF02.
- Use domínios de e-mail válidos nos seeds (`@empresa.com.br`). O `EmailStr` do Pydantic recusa domínios reservados, como `.local` e `.test`.

## 6. Regras de negócio

### 6.1 Equivalência de termos (Documento 01) e cores dos badges

| Rótulo na tela | Valor no banco | Badge (texto / token) |
|---|---|---|
| Aberto | `NOVO`, `PENDENTE` | `--info` `#2563EB` (fundo `info-soft`) |
| Em andamento | `ATRIBUIDO` | `--warning` `#C77700` (fundo `warning-soft`) |
| Resolvido | `CONCLUIDO` | `--success` `#16885B` (fundo `success-soft`) |
| Encerrado | `FECHADO` | `--secondary` `#475569` (fundo neutro) |
| Baixa | `BAIXA` | `--success` `#16885B` |
| Média | `MEDIA` | `--info` `#2563EB` |
| Alta | `ALTA` | `--warning` `#C77700` |
| Urgente | `CRITICO` | `--danger` `#D13B4A`, com ícone de sirene |

As cores saem da paleta Foundations (seção 8.2); os fundos suaves (`*-soft`) e as variantes do tema
escuro ficam nos tokens do Tailwind. O badge sempre traz o rótulo em texto (acessibilidade).

Grupos usados nas abas e nos indicadores:

- `abertos` = `NOVO` + `PENDENTE`
- `em_andamento` = `ATRIBUIDO`
- `resolvidos` = `CONCLUIDO`
- `encerrados` = `FECHADO`
- `urgentes` = severidade `CRITICO` com status `NOVO`, `PENDENTE` ou `ATRIBUIDO`

Protocolo: `TK-` seguido do id com no mínimo 4 dígitos (`TK-0051`, `TK-12345`), gerado pelo banco.

### 6.2 Regras RN01 a RN07

| Regra | Enunciado resumido | Onde é garantida | Fase | Testes |
|---|---|---|---|---|
| RN04 | Chamado só nasce ligado a uma categoria ativa e a um solicitante ativo | `ChamadoService.abrir` + FKs | F2 | TU01, TU02 |
| RN06 | Só usuário autenticado abre e consulta chamados; o CLIENTE vê só os seus | Dependência `usuario_atual` + filtro de escopo dentro do repositório | F1, F2 | TU07 |
| RN07 | E-mail único por usuário | `UsuarioService.cadastrar` + UNIQUE + e-mail normalizado em minúsculas | F1 | TU05 |
| RN03 | Status ATRIBUIDO exige técnico responsável (ANALISTA ou ADMIN ativo) | `CicloVidaService.atribuir` + CHECK no banco | F4 | TU10 |
| RN01 | Concluir exige registrar a solução aplicada | `CicloVidaService.concluir` | F4 | TU11 |
| RN02 | FECHADO exige aprovação expressa do solicitante | `CicloVidaService.responder_solucao` | F4 | TU12, TU13 |
| RN05 | Só solução aprovada vai para a Base de Conhecimento | `BaseConhecimentoService.publicar` | F5 | TU15 |

### 6.3 Ciclo de vida (Fase 4)

| De | Para | Quem | Condição | Efeitos |
|---|---|---|---|---|
| — | NOVO | Qualquer perfil autenticado, sempre para si | RN04 | Histórico; evento `CHAMADO_CRIADO` (e `CHAMADO_URGENTE` se CRITICO) |
| NOVO | PENDENTE | ANALISTA, ADMIN | Triagem; pode ajustar categoria e severidade | Histórico; evento `STATUS_ALTERADO` |
| NOVO, PENDENTE | ATRIBUIDO | ANALISTA (a si mesmo) ou ADMIN (a qualquer técnico) | RN03 | Evento `CHAMADO_ATRIBUIDO` |
| ATRIBUIDO | ATRIBUIDO | ADMIN ou o técnico atual | Reatribuição; RN03 | Evento `CHAMADO_ATRIBUIDO` |
| ATRIBUIDO | CONCLUIDO | Técnico responsável ou ADMIN | RN01: cria a solução com `PENDENTE_APROVACAO` | Preenche `data_conclusao`; evento `SOLUCAO_REGISTRADA` |
| CONCLUIDO | FECHADO | Somente o solicitante | RN02: aprova a solução pendente, que vira `APROVADO` | Preenche `data_fechamento`; evento `SOLUCAO_APROVADA` |
| CONCLUIDO | ATRIBUIDO | Somente o solicitante | Reprova com motivo obrigatório; a solução vira `REJEITADO` e o motivo vira follow-up | Evento `SOLUCAO_REJEITADA` |

Qualquer outra transição devolve `409 TRANSICAO_INVALIDA`. FECHADO é final: não aceita follow-up nem edição. Cada transição grava `historico_chamado` e atualiza `data_atualizacao` na mesma transação.

### 6.4 Escopo por perfil

- **CLIENTE**: só os próprios chamados (RN06). Pedir o chamado de outro usuário devolve `404`, para não revelar que ele existe.
- **ANALISTA**: todos os chamados (fila), com filtros "Atribuídos a mim" e "Sem responsável" (padrão a confirmar, seção 14).
- **ADMIN**: tudo, incluindo usuários, categorias e integrações.

### 6.5 Ordenação e busca

- Ordem padrão: chamados `CRITICO` ainda não resolvidos primeiro; depois, `data_criacao` decrescente.
- Busca `q` por título ou protocolo:
  - Título: `f_unaccent(lower(titulo)) LIKE '%' || f_unaccent(lower(:q)) || '%'`, escapando `%`, `_` e `\` do termo. Usa o índice trigram.
  - Se o termo tiver forma de protocolo (`^(tk-?)?0*(\d+)$`, sem diferenciar maiúsculas), inclua também `OR id_chamado = :numero`.
- Os contadores das abas respeitam busca e categoria, mas ignoram o filtro de status. Calcule-os numa única consulta com `count(*) FILTER (WHERE ...)`.
- `qtd_mensagens` vem de agregação ou subconsulta na mesma consulta da lista (nada de N+1).

## 7. API REST

### 7.1 Convenções

- Prefixo `/api`, JSON, datas ISO 8601 com fuso (`2026-10-09T14:32:00Z`).
- Autenticação de usuário: `Authorization: Bearer <access_token>`. O n8n autentica com o header `X-Integracao-Chave`.
- OpenAPI em `/api/docs` e `/api/openapi.json` (desligado em produção).
- Paginação: `?page=1&page_size=10` (máximo 50), com resposta `{ "items": [...], "total": 0, "page": 1, "page_size": 10 }`.
- Formato único de erro, com mensagens em PT-BR (converta os erros do Pydantic para este formato):

  ```json
  {
    "codigo": "EMAIL_DUPLICADO",
    "mensagem": "Este e-mail já está cadastrado.",
    "campos": { "email": "Este e-mail já está cadastrado." }
  }
  ```

- Status HTTP: `401` não autenticado · `403` perfil sem permissão · `404` inexistente ou fora do escopo · `409` conflito (e-mail duplicado, transição inválida, duplicidade) · `413` arquivo grande demais · `415` tipo de arquivo não permitido · `422` validação · `429` excesso de tentativas.
- Códigos de erro: `NAO_AUTENTICADO`, `SEM_PERMISSAO`, `NAO_ENCONTRADO`, `VALIDACAO`, `EMAIL_DUPLICADO`, `CATEGORIA_INVALIDA`, `SOLICITANTE_INATIVO`, `TRANSICAO_INVALIDA`, `ARQUIVO_GRANDE`, `TIPO_ARQUIVO_INVALIDO`, `MUITAS_TENTATIVAS`.
- Declare rotas fixas antes das paramétricas: `/api/chamados/resumo` antes de `/api/chamados/{id_chamado}`.
- Toda resposta leva o header `X-Request-ID` (gerado ou propagado), que também aparece nos logs.

### 7.2 Endpoints

| Método e rota | Perfis | Descrição | Fase | Requisitos |
|---|---|---|---|---|
| `GET /api/health` · `GET /api/health/db` | Público | Vida da API e conexão com o banco (`SELECT 1`) | F0 | DoD Doc 02 |
| `GET /api/config/publica` | Público | `{ whatsapp_suporte, email_suporte, google_sso, versao }` para a tela de login | F1 | — |
| `POST /api/auth/login` | Público | Login: devolve o access token e grava o cookie de refresh | F1 | RNF01, UJ01, FE01 |
| `POST /api/auth/refresh` | Cookie | Novo access token; rotaciona o refresh | F1 | RNF01 |
| `POST /api/auth/logout` | Autenticado | Revoga o refresh e apaga o cookie | F1 | — |
| `GET /api/auth/me` | Autenticado | Usuário atual | F1 | — |
| `PUT /api/auth/senha` | Autenticado | Troca de senha (senha atual + nova) | F1 | — |
| `POST /api/usuarios` | ADMIN | Cadastro de usuário | F1 | UC01, RF01, RN07 |
| `GET /api/usuarios` | ADMIN | Lista paginada (`q`, `perfil`, `ativo`) | F1 | UC01 |
| `GET /api/usuarios/{id}` | ADMIN | Detalhe | F1 | UC01 |
| `PATCH /api/usuarios/{id}` | ADMIN | Nome, cargo, perfil e `ativo` (exclusão lógica) | F4 | UC01 |
| `GET /api/usuarios/tecnicos` | ANALISTA, ADMIN | ANALISTAs e ADMINs ativos, para atribuição | F4 | RN03 |
| `GET /api/categorias` | Autenticado | Categorias ativas, ordenadas por `ordem` | F2 | RF05 |
| `POST /api/categorias` · `PATCH /api/categorias/{id}` | ADMIN | Criar, renomear, reordenar e desativar categorias | F7 | Doc 01 |
| `POST /api/chamados` | Autenticado | Abre chamado para o próprio usuário | F2 | UC02, RF02, RF05, RN04 |
| `GET /api/chamados` | Autenticado | Lista com busca, filtros, contadores e paginação | F2 | UC03, RF03, RF04, RN06, RNF02 |
| `GET /api/chamados/resumo` | Autenticado | Indicadores do Dashboard | F2 | RF04 |
| `GET /api/chamados/{id}` | Escopo do perfil | Detalhe | F2 | UC03, RN06 |
| `POST /api/chamados/{id}/anexos` · `GET /api/chamados/{id}/anexos` | Escopo do chamado | Envio (multipart) e lista de anexos | F3 | RF02 |
| `GET /api/anexos/{id}/download` | Escopo do chamado | Download em stream | F3 | RN06 |
| `GET /api/notificacoes` · `GET /api/notificacoes/contagem` | Autenticado | Lista e contador de não lidas | F3 | RF04 |
| `POST /api/notificacoes/{id}/lida` · `POST /api/notificacoes/lidas` | Autenticado | Marca uma ou todas como lidas | F3 | RF04 |
| `POST /api/chamados/{id}/triagem` | ANALISTA, ADMIN | NOVO → PENDENTE; ajusta categoria e severidade | F4 | RF03 |
| `POST /api/chamados/{id}/atribuicao` | ANALISTA, ADMIN | Atribui técnico → ATRIBUIDO | F4 | RF03, RN03 |
| `GET /api/chamados/{id}/followups` · `POST /api/chamados/{id}/followups` | Participantes | Mensagens do chamado | F4 | UC03, RF03 |
| `POST /api/chamados/{id}/solucoes` | Técnico responsável, ADMIN | Registra a solução → CONCLUIDO | F4 | RF03, RN01 |
| `POST /api/solucoes/{id}/resposta` | Solicitante | `{ "aprovada": true }` → FECHADO; `{ "aprovada": false, "motivo": "..." }` → ATRIBUIDO | F4 | RF03, RN02 |
| `GET /api/chamados/{id}/historico` | Escopo do chamado | Linha do tempo de status | F4 | RF03 |
| `GET /api/base-conhecimento` · `GET /api/base-conhecimento/{id}` | Autenticado | Busca (full-text) e filtro por categoria | F5 | UC04, RF06 |
| `POST /api/base-conhecimento` · `PATCH /api/base-conhecimento/{id}` | ANALISTA, ADMIN | Publica ou edita artigo a partir de solução aprovada | F5 | RF06, RN05 |
| `POST /api/perfil/whatsapp/vinculo` | Autenticado | Gera código e link `wa.me` (exige consentimento) | F6 | — |
| `GET /api/perfil/whatsapp` · `DELETE /api/perfil/whatsapp` | Autenticado | Status do vínculo e desvínculo | F6 | — |
| `PATCH /api/perfil/preferencias` | Autenticado | `notificar_email` e `whatsapp_opt_in` | F6 | — |
| `POST /api/integracoes/whatsapp/mensagens` | n8n (chave) | Mensagem recebida → respostas do bot | F6 | — |
| `POST /api/integracoes/whatsapp/sessao` | n8n (chave) | Status da sessão do WAHA, exibido em `/admin/integracoes` | F6 | — |
| `GET /api/admin/outbox` · `POST /api/admin/outbox/{id}/reenviar` | ADMIN | Fila de envios externos e reenvio de falhas | F6 | — |
| `POST /api/auth/esqueci-senha` · `POST /api/auth/redefinir-senha` | Público | Redefinição de senha por e-mail | F7 | FA02 |
| `GET /api/auth/google/login` · `GET /api/auth/google/callback` | Público | Login com Google Workspace (opcional) | F7 | UJ01 |
| `GET /api/sla/mes` | Autenticado | Percentual de chamados concluídos no prazo no mês | F7 | Doc 01 |

### 7.3 Contratos principais

`POST /api/chamados`

```json
{ "id_categoria": 1, "severidade": "MEDIA", "titulo": "VPN não conecta", "descricao": "Desde a atualização do Windows o cliente VPN falha." }
```

Validações: `id_categoria` obrigatório; `severidade` opcional (padrão `BAIXA`); `titulo` de 1 a 150 caracteres e `descricao` de 1 a 500, contados depois do `strip`. O solicitante vem sempre do token, nunca do corpo.

Resposta `201`, que é também o formato de cada item da lista:

```json
{
  "id_chamado": 51,
  "protocolo": "TK-0051",
  "titulo": "VPN não conecta",
  "descricao": "Desde a atualização do Windows o cliente VPN falha.",
  "categoria": { "id_categoria": 1, "nome_categoria": "TI", "icone": "💻" },
  "severidade": "MEDIA",
  "status_chamado": "NOVO",
  "status_grupo": "abertos",
  "solicitante": { "id_usuario": 7, "nome": "Ana Lima" },
  "tecnico_responsavel": null,
  "qtd_mensagens": 0,
  "data_criacao": "2026-10-09T14:32:00Z",
  "data_atualizacao": "2026-10-09T14:32:00Z"
}
```

`GET /api/chamados?q=vpn&grupo=abertos&id_categoria=1&page=1&page_size=10`

```json
{
  "items": [],
  "total": 2,
  "page": 1,
  "page_size": 10,
  "contadores": { "todos": 7, "abertos": 2, "em_andamento": 2, "resolvidos": 2, "encerrados": 1 }
}
```

Filtros extras para ANALISTA e ADMIN (F4): `responsavel=eu|nenhum|{id}`, `severidade`, `id_solicitante`.

`GET /api/chamados/resumo`

```json
{ "abertos": 1, "em_andamento": 2, "resolvidos": 3, "encerrados": 1, "urgentes": 1 }
```

`POST /api/auth/login`

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "expires_in": 1800,
  "usuario": { "id_usuario": 7, "nome": "Ana Lima", "email": "ana.lima@empresa.com.br", "tipo_perfil": "CLIENTE", "cargo": "Analista de Marketing" }
}
```

## 8. Front-end

### 8.1 Base

- Vite + React 19 + TypeScript `strict`; React Router 7 em modo SPA (`createBrowserRouter`), com rotas carregadas sob demanda (`lazy`).
- Estado do servidor: TanStack Query (cache, `placeholderData` durante a busca, invalidação depois de mutações). Estado do cliente: Zustand (sessão em memória e rascunho do wizard).
- Formulários: React Hook Form + Zod, com as mesmas regras da API (título até 150, descrição até 500, senha com 8 ou mais).
- Cliente HTTP: `openapi-fetch` com tipos gerados por `npm run gen:api` a partir de `/api/openapi.json`. Commite o arquivo gerado.
- Autenticação: access token só em memória, nunca em `localStorage`. Ao abrir o app, chame `/api/auth/refresh` para restaurar a sessão pelo cookie. Em `401`, tente o refresh uma vez e repita a requisição; se falhar, vá para `/login`.
- Rotas protegidas por perfil (`<RequirePerfil perfis={["ADMIN"]}>`); o menu lateral mostra só o que o perfil pode acessar.
- Datas com `date-fns`, locale `pt-BR` e fuso `America/Sao_Paulo`: `dd/MM/yy` nos cards; tempo relativo curto no Dashboard (`agora`, `5 min atrás`, `2 h atrás`, `15 d atrás`).
- Desenvolvimento: `npm run dev` com proxy `/api → http://localhost:8000`. Produção: build estático servido pelo Nginx do container `web`.

### 8.2 Identidade visual (design system "Foundations" do esboço)

A identidade do Mentory é **herdada do esboço aprovado** (coleção "01 — Foundations", ex-HelpFlow;
ver `docs/design/mentory/` e o ADR em `docs/DECISOES.md`). Fonte da verdade da identidade: a tela
Foundations do esboço. Marca **teal/petróleo**, tipografia **IBM Plex Sans**, sidebar **branca**,
superfícies com borda de 1px e sombras discretas, e **tema claro e escuro** (o escuro deriva da
mesma paleta).

Tokens definidos no `@theme` do Tailwind 4 (variáveis CSS). Cores base (tema claro):

| Token (esboço) | Valor | Uso |
|---|---|---|
| `--brand-600` | `#066873` | Primária: botões, logo, item ativo do menu, foco |
| `--brand-500` | `#087F8C` | Acento/eyebrow, realces e hover de marca |
| `--canvas` | `#F8FAFC` | Fundo das páginas |
| `--surface` | `#FFFFFF` | Cards, sidebar, topbar |
| `--text` | `#0B1220` | Texto principal (tinta) |
| `--secondary` | `#475569` | Texto secundário, rótulos, breadcrumb |
| `--success` | `#16885B` | "Resolvido", severidade "Baixa", status operacional |
| `--warning` | `#C77700` | "Em andamento", severidade "Alta" |
| `--danger` | `#D13B4A` | Alerta de urgência, severidade "Urgente", notificação |
| `--info` | `#2563EB` | "Aberto", severidade "Média", links informativos |

- **Item ativo do menu:** pílula teal-clara (`brand-soft` ≈ `#EAF4F4`) com texto `--brand-600` — a
  sidebar é **branca**, não escura.
- **Tipografia:** **IBM Plex Sans** (400/500/600/700), auto-hospedada via `@fontsource`. Escala do
  esboço: `Display/XL` (hero), `Heading/H1`, `Heading/H2`, `Body/MD`, `Label/SM` (caixa alta, com
  tracking). Monoespaçada (IBM Plex Mono) para protocolo (`TK-0051`) e números tabulares.
- **Forma e espaçamento:** raios `6 · 10 · 14 · 20 · full`; escala de espaço `4 · 8 · 12 · 16 · 20
  · 24 · 32 · 40 · 48 · 64`; ícones `16 · 20 · 24` (linha, `lucide-react`); breakpoints `390`
  (mobile) · `768` (tablet) · `1440` (desktop).
- **Tema escuro:** derivado da paleta (canvas ≈ `#0A1114`, surface ≈ `#0F181C`, brand clareada
  para contraste AA). Alternância por `data-theme` / `prefers-color-scheme`; persistir a escolha.
- **Badge sempre com texto, nunca só cor** (acessibilidade). As cores semânticas dos estados
  (seção 6.1) usam esta paleta: `--info` (Aberto/Média), `--warning` (Em andamento/Alta),
  `--success` (Resolvido/Baixa), `--secondary` neutro (Encerrado), `--danger` (Urgente).

> **Assistente de IA/RAG:** faz parte da **visão final do produto** (está na identidade: item de
> menu "Assistente IA", hero conversacional e card de apoio). A **implementação é de fase futura**
> — o núcleo de chamados vem primeiro. Nas telas das fases atuais, a entrada de IA aparece marcada
> como "em breve"/desabilitada.

### 8.3 Componentes base

`AppShell` (menu lateral no desktop; barra superior com gaveta no celular), `MenuLateral` (logo "Mentory · Help Desk", bloco do usuário com iniciais, nome e cargo, itens por perfil, chip "Novo", contador de notificações, "Perfil" no rodapé), `StatusBadge`, `SeveridadeBadge`, `CategoriaChip`, `CardIndicador`, `CardChamado`, `Stepper`, `OpcaoCard` (seleção com rádio), `CampoTexto` com contador, `ZonaUpload`, `Abas` com contador, `Paginacao`, `EstadoVazio`, `Esqueleto` (carregamento), `DialogoConfirmacao` e toasts (`sonner`).

### 8.4 Telas

**Login** (`/login` — RNF01, UJ01, FE01, FA02)
- Painel esquerdo na cor da marca (teal, oculto no celular): logo "Mentory", "Suporte que resolve de verdade.", texto de apoio e três cartões: Resposta rápida, Acompanhamento e Histórico completo.
- Formulário: "Bem-vindo de volta", e-mail corporativo, senha (mostrar/ocultar), link "Esqueci minha senha" (funcional na F7; antes disso, mostra "Contate o TI"), botão "Entrar no sistema", divisor "ou", "Entrar com Google Workspace" (só aparece se `google_sso` for verdadeiro) e "Problemas com acesso? Contate o TI" (`wa.me/<número>` ou `mailto:`).
- FE01: mensagem genérica "E-mail ou senha inválidos", sem dizer qual campo errou; o e-mail continua preenchido. Em `429`: "Muitas tentativas. Aguarde alguns minutos."

**Dashboard** (`/dashboard` — RNF02, RNF03)
- "Bom dia" (5h–12h), "Boa tarde" (12h–18h) ou "Boa noite", seguido do primeiro nome; subtítulo "Seu painel de suporte"; botão "+ Novo Chamado".
- Alerta vermelho quando `urgentes > 0`: "{n} chamado(s) urgente(s) aguardando atenção — esses chamados possuem prioridade máxima e serão atendidos primeiro", com o botão "Ver agora" abrindo a lista filtrada.
- Quatro indicadores (`/resumo`): Abertos, Em andamento, Resolvidos e Urgentes.
- "Chamados recentes" (os 5 últimos): protocolo, título, severidade, categoria, tempo relativo, "→ responsável" e status; link "Ver todos →".
- "Ações rápidas": Abrir novo chamado, Base de conhecimento e Ver histórico.
- Entrada do **Assistente IA** (visão de produto): hero conversacional ("Como podemos ajudar hoje?")
  e card de apoio na coluna direita, marcados "em breve"/desabilitados até a fase de IA.
- "SLA do mês": aparece só a partir da F7.
- ANALISTA e ADMIN (F4): indicadores da fila geral e atalho "Sem responsável".

**Novo Chamado** (`/chamados/novo` — UC02, RF02, RF05, RN04, FE02, FE03)
- Stepper: 1 Categoria → 2 Prioridade → 3 Detalhes. Etapa concluída fica verde com ✓; a ativa usa `--cor-primaria`.
- Etapa 1, "Qual área você precisa de ajuda?": grade das categorias ativas (ícone + nome), 3 colunas no desktop e 2 no celular.
- Etapa 2, "Qual a urgência do problema?": Baixa (Sem impacto imediato), Média (Impacto moderado), Alta (Afeta produtividade) e Urgente (Bloqueio total, com sirene). A etapa se chama "Prioridade" na tela, mas o campo enviado é `severidade`.
- Etapa 3, "Descreva o problema": título obrigatório (placeholder "Ex: Não consigo acessar o sistema de ponto"), descrição obrigatória com contador `0/500` (vermelho quando vazio ou no limite) e anexos opcionais na zona "Clique para adicionar arquivo — PNG, JPG, PDF até 10MB" (visível a partir da F3).
- Botões: Voltar (etapas 2 e 3), Cancelar (pede confirmação, descarta o rascunho e volta ao Dashboard — FE03) e Próximo (desabilitado sem seleção). Na etapa 3, "Enviar chamado".
- FE02: título e descrição ficam destacados em vermelho com a mensagem, e o envio é bloqueado.
- Sucesso: confirmação com o protocolo em destaque ("Chamado TK-0051 aberto!") e os botões "Ver chamado" e "Meus chamados". Se o upload falhar depois da criação, o chamado continua criado e o detalhe permite reenviar o anexo.
- O rascunho fica só em memória (Zustand): sair da tela descarta.

**Meus Chamados** (`/chamados` — UC03, RF03, RF04, RN06, RNF02)
- Título "Meus Chamados", "{total} chamados no total" e botão "+ Novo".
- Busca "Buscar por título ou ID do chamado..." com debounce de 300 ms.
- Abas com contador: Todos, Abertos, Em andamento, Resolvidos e Encerrados. Chips de categoria: "Todas as categorias" e as categorias.
- Card: protocolo em fonte monoespaçada, chip de categoria, chip "Urgente" se CRITICO, título, descrição em até 2 linhas, StatusBadge e SeveridadeBadge à direita; rodapé com "Aberto: dd/MM/yy · Atualizado: dd/MM/yy", responsável (se houver) e "{n} msg ›".
- Paginação de 10 itens; filtros refletidos na URL (`?q=&grupo=&categoria=&page=`), para o botão Voltar do navegador funcionar.
- Estados de carregamento (esqueleto), vazio e erro com "Tentar novamente".
- ANALISTA e ADMIN (F4): título "Chamados", filtros de responsável e severidade e o nome do solicitante no card.

**Detalhe do chamado** (`/chamados/:id` — UC03)
- Cabeçalho: protocolo, título, badges, datas, solicitante e responsável.
- F2: dados e descrição. F3: anexos com download. F4: linha do tempo (histórico + follow-ups), caixa de mensagem, ações por perfil (Triar, Atribuir, Registrar solução) e, para o solicitante com o chamado em CONCLUIDO, o cartão da solução com "Aprovar e encerrar" e "Reprovar" (motivo obrigatório).

**Base de Conhecimento** (`/base-conhecimento` — UC04, RF06, FA01; F5)
- Busca, filtro por categoria e artigos em acordeão (título, trecho e conteúdo completo ao expandir). No fim: "Não resolveu? Abrir chamado", que leva ao wizard.
- ANALISTA e ADMIN: "Publicar na base" a partir de um chamado FECHADO com solução aprovada, com título e conteúdo pré-preenchidos e editáveis.

**Notificações** (`/notificacoes` — RF04; F3)
- Lista com as não lidas em destaque e "Marcar todas como lidas". Clicar abre o chamado e marca como lida. O contador do menu atualiza a cada 30 s (`refetchInterval`) e depois de cada ação.

**Perfil** (`/perfil`)
- Dados do usuário e troca de senha (F1). WhatsApp (F6): consentimento, botão "Vincular WhatsApp" (mostra o código, o link `wa.me` e um QR code gerado no navegador), status do vínculo, "Desvincular" e preferências de e-mail e WhatsApp.

**Administração** (ADMIN)
- `/admin/usuarios` (F1): tabela com busca e filtros e o formulário "Novo usuário" (nome, e-mail, senha, perfil, cargo). FA01 (e-mail duplicado) mostra o erro no campo; FE01 destaca os campos incompletos. Na F4: editar, ativar e desativar.
- `/admin/categorias` (F7): criar, renomear, reordenar, ativar/desativar e escolher o ícone.
- `/admin/integracoes` (F6): status da sessão do WhatsApp e fila do outbox (pendentes, falhas, reenviar).

### 8.5 Responsividade, acessibilidade e desempenho

- Mobile-first (RNF03): abaixo de 768 px o menu vira gaveta, os indicadores ficam em 2×2 e os botões do wizard ocupam a largura toda.
- Navegação por teclado no wizard e nas abas, foco visível, `aria-live` para erros e contraste AA.
- Code splitting por rota. Meta: lista utilizável em menos de 2 s com 10 mil chamados no banco (RNF02).

## 9. Integração com e-mail e WhatsApp (n8n + WAHA) — Fase 6

### 9.1 Responsabilidades

| Backend (Python) | n8n | WAHA |
|---|---|---|
| Regras, permissões, máquina de estados do bot, textos das mensagens, outbox, vínculo, opt-in e opt-out | Receber webhooks, filtrar eventos, chamar a API, enviar pelo WAHA com pausas, enviar e-mail por SMTP, alertar falhas | Manter a sessão do WhatsApp (QR code), enviar e receber mensagens |

### 9.2 Saída: outbox → worker → n8n

- Tabela `eventos_outbox`: `id_evento` (BIGINT identity), `tipo` VARCHAR(60), `canal` ENUM (`WHATSAPP`, `EMAIL`), `destino` VARCHAR(255) (chat_id ou e-mail), `payload` JSONB, `status` ENUM (`PENDENTE`, `PROCESSANDO`, `ENVIADO`, `FALHOU`), `tentativas` SMALLINT, `proxima_tentativa_em`, `bloqueado_ate`, `ultimo_erro`, `criado_em`, `enviado_em`. Índice parcial em `proxima_tentativa_em` para status `PENDENTE` e `PROCESSANDO`.
- O service que muda o estado chama `EventoService.publicar(...)`, que grava `notificacoes` (portal) e `eventos_outbox` (canais externos, conforme opt-in e preferências) **na mesma transação**.
- O `worker` usa a mesma imagem da API (`python -m app.worker`) e, a cada 2 segundos, reserva um lote:

  ```sql
  UPDATE eventos_outbox
     SET status = 'PROCESSANDO', bloqueado_ate = now() + interval '60 seconds'
   WHERE id_evento IN (
         SELECT id_evento FROM eventos_outbox
          WHERE (status = 'PENDENTE' AND proxima_tentativa_em <= now())
             OR (status = 'PROCESSANDO' AND bloqueado_ate < now())
          ORDER BY id_evento
          LIMIT 20
          FOR UPDATE SKIP LOCKED)
  RETURNING *;
  ```

- Cada evento vai por `POST` para `N8N_WEBHOOK_NOTIFICACOES_URL` (timeout de 10 s). Resposta `2xx` → `ENVIADO`. Erro → `tentativas + 1` e backoff exponencial (30 s, 1, 2, 4, 8 min... até 1 h). Depois de 8 tentativas → `FALHOU`, visível em `/admin/integracoes` com opção de reenviar.
- Com `OUTBOX_HABILITADO=false` (padrão quando o perfil `whatsapp` não está ativo), o worker não despacha e os eventos esperam como `PENDENTE`.
- Contrato enviado ao n8n, com os headers `X-Mentory-Token` e `X-Evento-Id`:

  ```json
  {
    "id_evento": 981,
    "tipo": "SOLUCAO_REGISTRADA",
    "canal": "WHATSAPP",
    "destino": "5515999990000@c.us",
    "mensagem": { "texto": "✅ *TK-0041* — solução registrada. Responda *1* para aprovar e encerrar ou *2* para reprovar." }
  }
  ```

  Para e-mail: `"canal": "EMAIL"`, `"destino": "ana.lima@empresa.com.br"` e `"mensagem": { "assunto": "...", "texto": "...", "html": "..." }`.
- O n8n só responde `200` depois de entregar; em erro, responde `5xx` e o worker tenta de novo. A entrega é "pelo menos uma vez"; o n8n descarta `id_evento` repetido com o nó Remove Duplicates.

### 9.3 Entrada: WAHA → n8n → API → n8n → WAHA

1. O WAHA envia os eventos `message` e `session.status` para `http://n8n:5678/webhook/waha-eventos`, com o header `X-Mentory-Token` (header customizado do webhook; alternativa: HMAC SHA-512 no header `X-Webhook-Hmac`).
2. O n8n responde `200` na hora e filtra: descarta `fromMe = true`, grupos (`@g.us`), `status@broadcast` e `@newsletter`.
3. Se `from` terminar em `@lid`, o n8n consulta `GET /api/{session}/lids/{lid}` no WAHA para obter o número (`pn`, que pode vir `null`).
4. O n8n marca a mensagem como lida (`POST /api/sendSeen`) e chama a API:

   `POST /api/integracoes/whatsapp/mensagens` com o header `X-Integracao-Chave`

   ```json
   {
     "message_id": "false_5515999990000@c.us_3EB0C0A1B2",
     "chat_id": "5515999990000@c.us",
     "lid": null,
     "numero": "5515999990000",
     "texto": "1",
     "tem_midia": false,
     "timestamp": 1760630400
   }
   ```

   Resposta: `{ "respostas": [ { "texto": "..." } ] }`, com lista vazia quando a mensagem é repetida (`SET NX` em `wa:msg:{message_id}`).
5. Para cada resposta: `POST /api/startTyping` → espera de 1 a 3 s aleatórios → `POST /api/sendText` (`session`, `chatId`, `text`) → `POST /api/stopTyping`.
6. Se `session.status` vier como `FAILED`, `STOPPED` ou `SCAN_QR_CODE`: e-mail para `ALERTA_EMAIL_ADMIN` e `POST /api/integracoes/whatsapp/sessao`.

A API identifica o usuário por `whatsapp_chat_id`, `whatsapp_lid` ou `whatsapp_numero` (nessa ordem), só entre usuários ativos e vinculados.

### 9.4 Vínculo do WhatsApp (prova de posse + consentimento)

1. No Perfil, o usuário marca o consentimento ("Aceito receber notificações e atender chamados pelo WhatsApp") e clica em "Vincular WhatsApp".
2. A API gera um código de 6 dígitos (Redis, TTL de 10 min, guardado como hash) e devolve o link `https://wa.me/<WHATSAPP_NUMERO_SUPORTE>?text=VINCULAR%20<código>`. A tela mostra o link e um QR code.
3. O usuário envia a mensagem. O bot recebe `VINCULAR <código>`, grava `whatsapp_chat_id`, `whatsapp_lid` e `whatsapp_numero` (quando disponíveis), `whatsapp_opt_in = true` e `whatsapp_consentimento_em`, e responde confirmando.
4. A tela do Perfil consulta o status a cada 3 s até o vínculo acontecer (por no máximo 10 min).

Por que assim: o primeiro contato parte do usuário (menos risco de bloqueio do número); não é preciso converter número em `chatId`, o que evita os problemas do 9º dígito brasileiro e dos identificadores `@lid`; e fica provado que a pessoa controla aquele WhatsApp.

Opt-out a qualquer momento: "SAIR" ou "PARAR" no WhatsApp, ou "Desvincular" no portal → `whatsapp_opt_in = false` e o vínculo é apagado.

### 9.5 Bot de atendimento

Estado no Redis e regras no backend. Comandos aceitos sem diferenciar maiúsculas nem acentos:

| Entrada | Ação |
|---|---|
| `oi`, `olá`, `menu`, `0` | Menu: 1 Abrir chamado · 2 Meus chamados em aberto · 3 Consultar protocolo · 9 Ajuda |
| `1` ou `abrir` | Fluxo guiado: categoria (lista numerada) → prioridade (1 a 4) → título (até 150) → descrição (até 500) → confirmação (1 confirmar, 2 cancelar). Cria o chamado pelo mesmo `ChamadoService.abrir` (RN04), com `canal_origem = WHATSAPP`, e responde com protocolo e link |
| `2` | Até 5 chamados não encerrados, dos mais recentes para os mais antigos |
| `3` ou texto contendo `TK-0041` | Status, responsável e última atualização (só chamados do próprio usuário — RN06) |
| `TK-0041 <mensagem>` | Adiciona um follow-up, se o usuário for participante e o chamado não estiver FECHADO |
| `1` ou `2` logo depois do aviso de solução, `APROVAR TK-0041` ou `REPROVAR TK-0041 <motivo>` | Aprovação ou reprovação da solução (RN02: só o solicitante) |
| `cancelar` | Sai de qualquer fluxo |
| `SAIR` ou `PARAR` | Opt-out |
| Mídia sem texto | "Por enquanto recebo só texto. Para anexar arquivos, use o portal: <link>" |
| Número não vinculado | Só aceita `VINCULAR <código>`; qualquer outra mensagem recebe as instruções de vínculo, sem revelar dados |

- A conversa expira depois de 30 min sem mensagem e volta ao menu.
- Contexto de aprovação: ao enviar `SOLUCAO_REGISTRADA`, grave em `wa:conversa:{chat_id}` o estado `AGUARDANDO_APROVACAO` com o `id_chamado` (vale o aviso mais recente). A confirmação sempre repete o protocolo.
- Os textos ficam em `app/integrations/whatsapp/mensagens.py`, com a formatação do WhatsApp (`*negrito*`, `_itálico_`), e têm testes.
- Minimização de dados (LGPD): as mensagens levam protocolo, título, status e link. Descrição e solução completas ficam no portal; a solução vai resumida em até 300 caracteres para permitir a aprovação.

### 9.6 Eventos e canais

| Evento | Quando | Destinatários | Portal | E-mail | WhatsApp |
|---|---|---|---|---|---|
| `CHAMADO_CRIADO` | Abertura | Solicitante | ✓ | ✓ | ✓ |
| `CHAMADO_URGENTE` | Abertura com CRITICO | ANALISTAs e ADMINs ativos | ✓ | ✓ | ✓ |
| `STATUS_ALTERADO` | Triagem | Solicitante | ✓ | — | — |
| `CHAMADO_ATRIBUIDO` | Atribuição | Solicitante e técnico | ✓ | ✓ | ✓ |
| `FOLLOWUP_ADICIONADO` | Nova mensagem | A outra parte | ✓ | — | ✓ |
| `SOLUCAO_REGISTRADA` | → CONCLUIDO | Solicitante | ✓ | ✓ | ✓ (com 1/2 para aprovar) |
| `SOLUCAO_APROVADA` | → FECHADO | Técnico | ✓ | — | ✓ |
| `SOLUCAO_REJEITADA` | → ATRIBUIDO | Técnico | ✓ | ✓ | ✓ |
| `SENHA_REDEFINICAO` | Esqueci a senha | Usuário | — | ✓ | — |

WhatsApp só para quem está vinculado e com opt-in; e-mail respeita `notificar_email` (exceto a redefinição de senha). Nas fases 3 e 4 só existe o canal Portal; a Fase 6 liga os outros canais sem mexer nos services, porque a interface `EventoService` já nasce prevendo os canais.

### 9.7 Workflows do n8n

Fixe uma versão estável 2.x do n8n. No n8n 2.x, o workflow precisa estar **publicado** para o webhook de produção funcionar, e o nó Code não lê variáveis de ambiente (`N8N_BLOCK_ENV_ACCESS_IN_NODE=true` por padrão). Use **credenciais** (Header Auth e SMTP) e URLs internas fixas (`http://api:8000`, `http://waha:3000`).

1. `waha-entrada.json`: Webhook `POST /webhook/waha-eventos` (Header Auth com `X-Mentory-Token`, responde na hora) → Switch por `event`.
   - `message`: IF dos filtros → IF `@lid` → HTTP (lids) → HTTP `sendSeen` → HTTP para a API (`/mensagens`) → Split Out de `respostas` → Loop Over Items: `startTyping` → Wait de 1 a 3 s → `sendText` → `stopTyping`.
   - `session.status`: IF status crítico → Send Email + HTTP para a API (`/sessao`).
2. `helpdesk-notificacoes.json`: Webhook `POST /webhook/helpdesk-notificacoes` (Header Auth; responde pelo nó Respond to Webhook) → Remove Duplicates (`id_evento`, itens de execuções anteriores) → Switch por `canal`.
   - `WHATSAPP`: `startTyping` → Wait → `sendText` → `stopTyping` → Respond 200.
   - `EMAIL`: Send Email (SMTP) → Respond 200.
   - Erro em qualquer ramo → Respond 502.
3. `alerta-erros.json`: Error Trigger → e-mail para o administrador.

Entregue os JSON exportados (importáveis e sem credenciais) e um `integrations/n8n/README.md` com: criação das credenciais (Header Auth do WAHA com `X-Api-Key`, Header Auth da API com `X-Integracao-Chave`, Header Auth do webhook com `X-Mentory-Token`, SMTP), importação (`n8n import:workflow`), publicação, e um passo a passo nó a nó para refazer à mão se a importação falhar.

### 9.8 WAHA

- Imagem pública `devlikeapro/waha` com versão fixada **igual ou maior que 2026.6.1** (recursos do antigo Plus inclusos, sem custo). Engine `WEBJS`, a mais compatível; `NOWEB` e `GOWS` são opções mais leves.
- Sessão `default`. Na primeira vez, leia o QR code pelo dashboard do WAHA. Volume persistente em `/app/.sessions`.
- Segurança: `WAHA_API_KEY` (pode ser guardada como `sha512:<hash>`) e usuário e senha do dashboard e do Swagger definidos no `.env`. O WAHA **nunca** fica exposto à internet: só na rede interna do Compose, com o dashboard acessado por VPN ou túnel SSH.
- Webhook global: `WHATSAPP_HOOK_URL=http://n8n:5678/webhook/waha-eventos` e `WHATSAPP_HOOK_EVENTS=message,session.status`, mais o header customizado com o token. Confira na documentação do WAHA o formato de `WHATSAPP_HOOK_CUSTOM_HEADERS`; a alternativa é `WHATSAPP_HOOK_HMAC_KEY`.
- Anti-bloqueio: número dedicado (WhatsApp Business), nunca um número pessoal; aquecer o número na primeira semana com volume baixo; só responder ou notificar quem fez opt-in; pausa e "digitando…" antes de cada envio; no máximo cerca de 20 mensagens por minuto.
- Risco assumido: o WAHA usa o protocolo do WhatsApp Web, que não é oficial, então o número pode ser bloqueado. A API oficial (WhatsApp Cloud API, da Meta) cobra por conversa e fica fora do critério de custo zero. Como o transporte está isolado no n8n, uma migração futura não afeta o backend.

## 10. Infraestrutura (Docker Compose)

### 10.1 Serviços

| Serviço | Imagem (fixar versão) | Perfil | Porta em dev | Volume | Healthcheck |
|---|---|---|---|---|---|
| `db` | `postgres:17-alpine` | padrão | `127.0.0.1:5432` (DBeaver) | `pg_data` | `pg_isready` |
| `redis` | `redis:8-alpine` (ou `valkey/valkey:8-alpine`) | padrão | — | `redis_data` | `redis-cli ping` |
| `s3` | `chrislusf/seaweedfs`, single-node com S3 (`weed server -dir=/data -s3 -s3.config=...`) | padrão | `127.0.0.1:8333` | `s3_data` | Status do SeaweedFS |
| `migrate` | Imagem do backend, comando `alembic upgrade head` | padrão | — | — | Executa e termina |
| `api` | `backend/Dockerfile` (Uvicorn) | padrão | `8000` | — | `GET /api/health` |
| `worker` | Imagem do backend, comando `python -m app.worker` | padrão | — | — | `worker:heartbeat` no Redis |
| `web` | `frontend/Dockerfile` (Nginx) | padrão | `8080` | — | `GET /` |
| `n8n` | `docker.n8n.io/n8nio/n8n` (2.x estável) | `whatsapp` | `5678` | `n8n_data` | `GET /healthz` |
| `waha` | `devlikeapro/waha` (≥ 2026.6.1) | `whatsapp` | `3000` (dashboard) | `waha_sessions` | Health check do WAHA |
| `mailpit` | `axllent/mailpit` | só no override de dev | `8025` (UI) e `1025` (SMTP) | — | — |

- `api` e `worker` dependem de `migrate` (`condition: service_completed_successfully`), que depende de `db` saudável.
- O n8n usa o mesmo PostgreSQL, com banco e usuário próprios criados por `infra/postgres/init/01-n8n.sh` (o script só roda na primeira inicialização do volume). Variáveis: `DB_TYPE=postgresdb`, `DB_POSTGRESDB_*`, `N8N_ENCRYPTION_KEY` (guarde junto com o backup; sem ela as credenciais não abrem), `GENERIC_TIMEZONE` e `TZ=America/Sao_Paulo`, `N8N_HOST`, `N8N_PROTOCOL` e `WEBHOOK_URL`.
- As credenciais do S3 nunca são versionadas: `infra/seaweedfs/entrypoint.sh` gera o `s3.json` a partir de `S3_ACCESS_KEY` e `S3_SECRET_KEY` ao iniciar o container.
- Uma rede interna única. Em produção só o `web` (via Traefik) fica acessível; n8n e WAHA, só por VPN.
- Sem o perfil `whatsapp`, o sistema funciona completo, só sem os canais externos. É assim que a avaliação e quem não tem o QR code rodam o projeto. Com ele: `docker compose --profile whatsapp up -d`.

### 10.2 `.env.example`

```dotenv
# ===== Geral =====
COMPOSE_PROJECT_NAME=mentory
# dev ou prod
AMBIENTE=dev
PORTAL_URL=http://localhost:8080
TZ=America/Sao_Paulo
LOG_LEVEL=INFO

# ===== PostgreSQL =====
POSTGRES_DB=helpdesk
POSTGRES_USER=helpdesk
POSTGRES_PASSWORD=troque-me
DATABASE_URL=postgresql+psycopg://helpdesk:troque-me@db:5432/helpdesk

# ===== Redis =====
REDIS_URL=redis://redis:6379/0
REDIS_PREFIXO=mentory:

# ===== S3 (SeaweedFS) =====
S3_ENDPOINT_URL=http://s3:8333
S3_ACCESS_KEY=gere-com-openssl-rand-hex-16
S3_SECRET_KEY=gere-com-openssl-rand-hex-32
S3_REGIAO=us-east-1
S3_BUCKET_ANEXOS=mentory-anexos
S3_BUCKET_BACKUPS=mentory-backups

# ===== Autenticação =====
JWT_SECRET=gere-com-openssl-rand-hex-32
JWT_ACCESS_MINUTOS=30
JWT_REFRESH_DIAS=7
# Use 4 nos testes, para ficarem rápidos
BCRYPT_CUSTO=12
CORS_ORIGINS=http://localhost:5173

# ===== Primeiro administrador (make criar-admin) =====
ADMIN_NOME=Administrador
ADMIN_EMAIL=admin@empresa.com.br
ADMIN_SENHA=troque-me-agora

# ===== Anexos =====
ANEXOS_MAX_MB=10
ANEXOS_MAX_POR_CHAMADO=5

# ===== Integrações (perfil whatsapp) =====
OUTBOX_HABILITADO=false
N8N_WEBHOOK_NOTIFICACOES_URL=http://n8n:5678/webhook/helpdesk-notificacoes
# Token que o worker e o WAHA enviam ao n8n
N8N_WEBHOOK_TOKEN=gere-um-token
# Chave que o n8n envia à API
INTEGRACAO_API_KEY=gere-uma-chave
# Só dígitos, com DDI e DDD
WHATSAPP_NUMERO_SUPORTE=5515999999999
EMAIL_SUPORTE=ti@empresa.com.br
ALERTA_EMAIL_ADMIN=ti@empresa.com.br

# ===== n8n =====
N8N_DB_NAME=n8n
N8N_DB_USER=n8n
N8N_DB_PASSWORD=troque-me
N8N_ENCRYPTION_KEY=gere-com-openssl-rand-hex-32
N8N_HOST=localhost
N8N_PROTOCOL=http
WEBHOOK_URL=http://localhost:5678/

# ===== WAHA =====
WAHA_API_KEY=gere-uma-chave
WAHA_DASHBOARD_USERNAME=admin
WAHA_DASHBOARD_PASSWORD=troque-me
WHATSAPP_SWAGGER_USERNAME=admin
WHATSAPP_SWAGGER_PASSWORD=troque-me
WHATSAPP_DEFAULT_ENGINE=WEBJS
WHATSAPP_HOOK_URL=http://n8n:5678/webhook/waha-eventos
WHATSAPP_HOOK_EVENTS=message,session.status

# ===== SMTP (valores para a credencial SMTP do n8n; em dev, Mailpit) =====
SMTP_HOST=mailpit
SMTP_PORT=1025
SMTP_USUARIO=
SMTP_SENHA=
SMTP_REMETENTE=helpdesk@empresa.com.br

# ===== Google Workspace (Fase 7, opcional) =====
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_DOMINIO_PERMITIDO=empresa.com.br
```

Comentários sempre em linha própria: o `.env` é lido pelo Compose, pelo pydantic-settings e pelo n8n, e cada um trata comentário no fim da linha de um jeito.

### 10.3 Makefile

Alvos mínimos: `up`, `up-whatsapp`, `down`, `logs`, `migrate`, `migration nome=...` (Alembic autogenerate, sempre revisado à mão), `criar-admin`, `seed`, `seed-performance`, `test`, `test-e2e`, `lint`, `format`, `build`, `gen-api`, `backup` e `restore arquivo=...`.

Passos de execução (substituem os do Documento 02 como evidência):

```bash
git clone <URL do repositório> && cd mentory-helpdesk
cp .env.example .env     # troque todos os segredos
make up                  # PostgreSQL, Redis, S3, migrations, API, worker e web
make migrate             # cria ou atualiza as tabelas (idempotente)
make test                # inclui o teste de conexão com o banco
make build               # build do backend e do frontend sem erros
```

### 10.4 Dockerfiles e Nginx

- Backend: `python:3.13-slim`, `uv` copiado da imagem oficial, multi-stage, `uv sync --frozen --no-dev`, usuário não-root e `uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips="*"` (em dev, com `--reload` e bind mount).
- Front-end: `node:24-alpine` roda `npm ci && npm run build`; o estágio final é um `nginx` estável (alpine) servindo `dist/`.
- Nginx: `client_max_body_size 12m` (o padrão de 1 MB barraria anexos de 10 MB); `location /api/` com `proxy_pass http://api:8000` e headers `X-Forwarded-*`; fallback da SPA com `try_files $uri /index.html`; gzip; cache longo para `/assets/`; cabeçalhos de segurança (CSP restrita a `'self'`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`).

### 10.5 Produção

- Servidor Linux com Docker Engine. HTTPS obrigatório (RNF01) via Traefik v3 + Let's Encrypt: `docker-compose.prod.yml` com labels no `web`, rede externa do Traefik configurável (`TRAEFIK_REDE`), HSTS e nenhuma porta publicada nos outros serviços.
- Cookie de refresh com `Secure`; `/api/docs` desligado; Uvicorn com `--workers 2`.
- n8n e dashboard do WAHA só por VPN ou rede interna.
- Backup: `make backup` (e um cron diário no servidor) gera `pg_dump -Fc` e envia ao bucket `mentory-backups`, com retenção de 7 diários e 4 semanais. Documente a restauração e teste-a pelo menos uma vez. Guarde também a `N8N_ENCRYPTION_KEY` e o volume do WAHA.

## 11. Segurança e LGPD

- Senhas: BCrypt com custo 12; mínimo de 8 caracteres e máximo de 72 bytes (limite do BCrypt; a biblioteca `bcrypt` 5.x lança erro acima disso). Senha nunca aparece em log.
- Access token JWT HS256 com `JWT_SECRET` de 32 bytes ou mais; claims `sub`, `perfil`, `exp`, `iat` e `jti`. A cada requisição o usuário é recarregado do banco e, se estiver inativo, recusado.
- Refresh token opaco (aleatório, 256 bits) em cookie `HttpOnly`, `SameSite=Strict`, `Path=/api/auth` e `Secure` em produção. O banco guarda só o hash SHA-256. Rotação a cada uso; se um token já rotacionado for reutilizado, a família inteira é revogada.
- Login: mensagem genérica e limite de 5 tentativas a cada 15 min por IP e por e-mail (Redis) → `429`.
- Autorização: dependências `usuario_atual` e `exigir_perfil(...)`; o escopo é aplicado dentro da consulta no repositório, nunca filtrando depois.
- SQL só via ORM ou `text()` com parâmetros; escape de `%` e `_` nas buscas com `LIKE`.
- Uploads: tipo validado pelo conteúdo (magic bytes, biblioteca `filetype`), não pela extensão; limite de 10 MB conferido durante a leitura em stream; nome aleatório no S3; download com `Content-Disposition` e `X-Content-Type-Options: nosniff`.
- CORS só em dev; em produção, front e API têm a mesma origem.
- Integrações: `X-Integracao-Chave` comparada em tempo constante, e um segredo diferente para cada direção (n8n → API; worker e WAHA → n8n).
- Logs em JSON com `request_id`, usuário e rota, mascarando e-mail, telefone, `chat_id` e tokens.
- LGPD: consentimento explícito e registrado para o WhatsApp; opt-out a qualquer momento; mínimo de dados nas mensagens externas; histórico de status como trilha de auditoria.

## 12. Testes e qualidade

### 12.1 Backend (pytest)

- **Unitários** (`tests/unit/`): services com repositórios falsos em memória. As regras são testadas sem banco.
- **Integração** (`tests/integration/`): API via `TestClient` e PostgreSQL real (banco `helpdesk_test` criado pela fixture, esquema via `alembic upgrade head`, cada teste numa transação desfeita no fim). Redis com `fakeredis` e S3 com `moto`. Atenção: sequências não voltam no rollback, então não fixe ids nos testes.
- **Migrations**: `upgrade head → downgrade base → upgrade head` sem erro (no CI).
- **Conexão** (DoD do Documento 02): `test_conexao_banco` executa `SELECT 1`, lê a versão do PostgreSQL e confere que as 6 tabelas existem.
- **Desempenho (RNF02)**: com o `seed-performance`, `GET /api/chamados` (com busca e filtros) e `GET /api/chamados/resumo` respondem em menos de 2 s (p95 de 20 chamadas). Marcado com `@pytest.mark.performance`; roda no CI noturno e na Sprint Review.
- Cobertura mínima: 90% em `services/` e 80% no total.

### 12.2 Casos obrigatórios (o nome do teste começa pelo código)

| Código | Cenário | Esperado |
|---|---|---|
| TU01 (RN04) | Criar chamado sem categoria, com categoria inexistente ou inativa | Rejeitado (`422`) |
| TU02 (RN04) | Solicitante inexistente ou inativo (teste unitário do service, já que pela API um usuário inativo nem autentica) | Rejeitado |
| TU03 | Chamado válido | Nasce `NOVO`, ligado ao usuário do token, com a severidade informada (ou `BAIXA`) e protocolo `TK-` + id com 4+ dígitos; id 12345 (inserido com `OVERRIDING SYSTEM VALUE`) gera `TK-12345` |
| TU04 | Título ou descrição vazios ou só com espaços; título acima de 150; descrição acima de 500 | Rejeitados (`422`) |
| TU05 (RN07) | E-mail duplicado, inclusive com maiúsculas diferentes | `409 EMAIL_DUPLICADO` |
| TU06 | Senha com menos de 8 caracteres ou mais de 72 bytes | `422`; senha válida gravada como hash `$2b$`, nunca em texto puro |
| TU07 (RN06) | Sem token; CLIENTE lendo chamado de outro; CLIENTE em `/api/usuarios` | `401`; `404` (e o chamado não aparece na lista); `403` |
| TU08 | Filtros por grupo e categoria, busca por título (sem acento) e por protocolo, paginação, contadores, CRITICO primeiro | Conjunto esperado |
| TU09 | Transições fora da tabela 6.3 | `409 TRANSICAO_INVALIDA` |
| TU10 (RN03) | Atribuir sem técnico, a um CLIENTE ou a um usuário inativo | Rejeitado; atribuição válida → `ATRIBUIDO` |
| TU11 (RN01) | Concluir sem solução | Rejeitado; com solução → `CONCLUIDO` e solução `PENDENTE_APROVACAO` |
| TU12 (RN02) | Aprovar sendo o técnico, um ADMIN ou outro cliente | Negado; o solicitante aprova → `FECHADO` |
| TU13 (RN02) | Reprovar sem motivo / com motivo | `422` / volta a `ATRIBUIDO`, solução `REJEITADO` e motivo registrado como follow-up |
| TU14 | Follow-up de quem não participa do chamado ou em chamado `FECHADO` | Negado |
| TU15 (RN05) | Publicar solução não aprovada ou já publicada | `422` / `409` |
| TU16 | Anexo com tipo falsificado, acima de 10 MB ou baixado por outro cliente | `415` / `413` / `404` |
| TU17 | Cada evento da tabela 9.6 | Notificação e outbox para os destinatários e canais certos |
| TU18 | Outbox com o n8n fora do ar | Backoff, `FALHOU` depois de 8 tentativas, reenvio manual funciona |
| TU19 | Vínculo do WhatsApp com código válido, expirado, errado e reutilizado | Só o válido vincula; consentimento registrado |
| TU20 | Bot: mensagem repetida, número não vinculado, `SAIR` | Nenhuma resposta duplicada; só instruções de vínculo; opt-out aplicado |
| TU21 | Bot: abertura guiada e aprovação pelo WhatsApp | Mesmas regras do portal (RN04, RN02) |

### 12.3 Front-end

- Vitest + Testing Library + MSW: o wizard não avança sem seleção; não envia sem título e descrição; contador `0/500`; Cancelar descarta o rascunho; badges com os rótulos certos; rotas protegidas por perfil.
- Playwright (rodando contra o Compose): **UJ01** completa (login → dashboard → novo chamado em 3 etapas → protocolo → Meus Chamados com busca e filtro), FE01, FE02, FE03 e a mesma jornada em viewport de celular (RNF03).

### 12.4 CI e fluxo Git

- Jobs do GitHub Actions: `backend` (ruff, mypy, pytest com serviço PostgreSQL), `frontend` (lint, `tsc --noEmit`, vitest, build), `migrations` (ida e volta) e `e2e` (Compose + Playwright, em PR para `main` e no agendamento noturno).
- Fluxo do Documento 02: `feature/*` → PR para `develop` → PR para `main`; `main` protegida (1 aprovação + CI verde; veja a nota sobre planos do GitHub na seção 3.3). O template de PR tem checklist: requisitos atendidos, testes, migrations e prints de tela.

## 13. Fases de implementação

### Fase 0 — Fundação (Documento 02)

**Entregas**
- Estrutura de pastas da seção 4.2, `AGENTS.md`, `CLAUDE.md`, README (pré-requisitos, passos, solução de problemas e a nota de licença do Docker Desktop), `.gitignore`, `.env.example`, Makefile e CI.
- Compose com `db`, `redis`, `s3`, `migrate`, `api`, `worker` (esqueleto) e `web`, mais o override de dev.
- FastAPI com `create_app`, configuração (`pydantic-settings`), sessão do banco, logs em JSON, `X-Request-ID`, tratamento de erros no formato da seção 7.1, `/api/health` e `/api/health/db`.
- Entidades das 6 tabelas, migration `0001` (seção 5.2) e `docs/der.md` (Mermaid).
- Front-end: Vite + React + TypeScript + Tailwind com os tokens da seção 8.2, `AppShell` e as rotas com telas vazias.

**DoD**
- [ ] `make up` sobe todos os serviços saudáveis; `make migrate` cria as 6 tabelas, FKs, ENUMs, índices e as 7 categorias.
- [ ] `test_conexao_banco` e o teste de ida e volta das migrations passam.
- [ ] `make build` sem erros (backend e front-end) e CI verde.
- [ ] O README reproduz o ambiente do zero numa máquina limpa.

### Fase 1 — Autenticação e cadastro de usuários (UC01, RF01, RN07, RNF01)

**Entregas:** migration 0002; login, refresh, logout, `me` e troca de senha; limite de tentativas; `make criar-admin`; `POST` e `GET /api/usuarios`; `/api/config/publica`; telas de Login, Perfil (dados e senha) e `/admin/usuarios`; proteção de rotas por perfil.

**DoD**
- [ ] TU05, TU06 e TU07 (parte de `401`/`403`) verdes.
- [ ] FA01 (e-mail duplicado) e FE01 (campos incompletos) do UC01 demonstráveis.
- [ ] Senha nunca em texto puro, conferido direto no banco.

### Fase 2 — Abertura e consulta de chamados (Documento 03: UC02, UC03 parcial, RF02, RF05, RN04, RN06, RNF02, RNF03)

**Entregas:** `GET /api/categorias`; `POST` e `GET /api/chamados`, `/resumo` e `/{id}`; Dashboard, Novo Chamado (3 etapas), confirmação com protocolo, Meus Chamados e Detalhe (somente leitura); `make seed` e `make seed-performance`.

**DoD (do Documento 03)**
- [ ] O formulário grava o chamado, que aparece em Meus Chamados e nos indicadores do Dashboard.
- [ ] Busca, filtros por status e categoria e paginação funcionam; o usuário não vê chamados de outro (TU07).
- [ ] TU01 a TU04 e TU08 verdes; build sem erros.
- [ ] Listagem em menos de 2 s com 10 mil chamados, em desktop e celular.
- [ ] Roteiro da Sprint Review executável: login → cadastro de usuário → abertura em 3 etapas → consulta com filtros → tentativas inválidas (e-mail duplicado, chamado sem categoria).

### Fase 3 — Anexos e notificações no portal

**Entregas:** migration 0003; S3 (SeaweedFS) com `StorageService`; envio, lista e download de anexos; zona de upload no wizard e no detalhe; `EventoService` (canal Portal); tela de Notificações e contador no menu.

**DoD**
- [ ] TU16 e TU17 (parte do portal) verdes.
- [ ] Um anexo de 10 MB passa pelo Nginx; o download respeita o escopo.

### Fase 4 — Ciclo de vida (RF03, RN01, RN02, RN03, UC03 completo)

**Entregas:** migration 0004; triagem, atribuição, follow-ups, solução, aprovação e reprovação, histórico; visão de ANALISTA e ADMIN (fila e filtros); `PATCH /api/usuarios` (ativar e desativar = exclusão lógica); eventos da tabela 9.6 no canal Portal.

**DoD**
- [ ] TU09 a TU14 verdes.
- [ ] Fluxo completo de NOVO a FECHADO demonstrável com três usuários (cliente, analista, admin).
- [ ] UJ01 no E2E atualizada com o acompanhamento.

### Fase 5 — Base de Conhecimento (RF06, RN05, UC04, FA01)

**Entregas:** migration 0005 (full-text); busca e listagem em acordeão; publicação a partir de solução aprovada; "Abrir chamado" a partir do artigo.

**DoD**
- [ ] TU15 verde.
- [ ] Digitar "configuracao" encontra artigos com "configuração".
- [ ] FA01 (autoatendimento) demonstrável.

### Fase 6 — Canais externos: e-mail e WhatsApp (n8n + WAHA)

**Entregas:** migration 0006; outbox e worker; endpoints de integração (seção 9.3); vínculo e preferências no Perfil; bot (seção 9.5); serviços `n8n` e `waha` no perfil `whatsapp`; workflows e READMEs em `integrations/`; tela `/admin/integracoes`.

**DoD**
- [ ] TU17 a TU21 verdes.
- [ ] Com o perfil `whatsapp`: vincular um número, abrir chamado pelo WhatsApp, receber o aviso de solução e aprovar respondendo "1".
- [ ] E-mails aparecem no Mailpit.
- [ ] Derrubar o n8n por 5 minutos não perde nenhuma notificação.

### Fase 7 — Complementos e produção

**Entregas:** migration 0007; Esqueci minha senha (FA02: token de 30 min, uso único, enviado por e-mail); SLA do mês no Dashboard (metas por severidade, padrão da seção 14); administração de categorias; Google Workspace opcional (OIDC com Authlib, só para usuários já cadastrados e do domínio permitido); `docker-compose.prod.yml` com Traefik; backup e restauração; revisão de segurança (seção 11) e de acessibilidade.

**DoD**
- [ ] E2E da redefinição de senha verde.
- [ ] Restauração de backup testada.
- [ ] Checklist da seção 11 conferido.
- [ ] Deploy documentado no README.

### Fase 8 — Assistente de IA (Mentory AI, RAG) — visão final do produto

Esta é a **visão final do produto** (ADR 2026-10-17): o item de menu "Assistente IA", o hero
conversacional e o card de apoio deixam de ser "em breve" e passam a funcionar. O detalhe técnico
está na **seção 16**; a arquitetura espelha, em Python, o desenho validado do plugin
`aiservicedesk` (provider abstraction, fallback de modelo e de provedor, orçamento de tempo,
degradação e RAG sobre a Base de Conhecimento). O núcleo de chamados (F0–F7) vem antes — e já veio.

**Entregas:** migration `0009` (`ia_config`, `ia_conversas`, `ia_mensagens`, `ia_uso`;
`base_conhecimento.embedding` para o RAG); camada `app/ia/` (contratos neutros + providers +
registry + política de fallback); `IaService` (fachada) e `OrquestradorIa` (laço de ferramentas);
RAG sobre a Base de Conhecimento (embedding + busca semântica, com _fallback_ para o full-text da
F5); ferramentas seguras (buscar na base, consultar/abrir chamado — reusando os services, nunca SQL
solto); `POST /api/ia/conversas` e `POST /api/ia/conversas/{id}/mensagens` (SSE opcional); tela do
Assistente (hero conversacional + chat) e `/admin/ia` (provedor, modelo, chave, cadeia de fallback,
teste de conexão, consumo). Chave do provedor cifrada no banco, nunca em log/resposta.

**DoD**
- [ ] Com um provedor configurado (ex.: Gemini via endpoint OpenAI-compatible), o assistente
      responde uma dúvida citando artigos reais da Base de Conhecimento (RAG).
- [ ] Fallback de modelo (429/503 do Gemini) e de provedor (cadeia) exercitados em teste, com
      orçamento de tempo respeitado; degradação de imagem/ferramentas sem derrubar a conversa.
- [ ] Nenhuma regra de negócio na ferramenta: abrir/consultar chamado passa pelos services (RN04,
      RN06) e pelas permissões do usuário autenticado.
- [ ] A chave do provedor nunca aparece em log, resposta HTTP ou mensagem de erro; `/admin/ia`
      valida a conexão com uma chamada mínima.
- [ ] `make lint`/`make test` e o front verdes; a tela do Assistente sai do estado "em breve".

## 14. Decisões em aberto (padrões adotados até o PO validar)

| Tema | Padrão adotado | Motivo ou alternativa |
|---|---|---|
| Significado de `PENDENTE` | Chamado triado, aguardando atribuição | Os documentos não definem; no protótipo aparece como "Aberto" |
| Visão do ANALISTA | Vê todos os chamados (fila), com filtros "Atribuídos a mim" e "Sem responsável" | Alternativa: só os atribuídos e os sem responsável |
| Indicador "Resolvidos" | Só `CONCLUIDO` (equivalência do Documento 01) | `FECHADO` aparece em "Encerrados" |
| Encerramento automático | Não existe | Fecharia sem a aprovação expressa exigida pela RN02 |
| Quem abre chamado | Qualquer perfil, sempre para si | Abrir em nome de outra pessoa fica fora do escopo |
| Anexos | Até 5 por chamado, 10 MB cada (configurável) | O documento define só o limite por arquivo |
| Metas de SLA | CRITICO 4 h · ALTA 8 h · MEDIA 24 h · BAIXA 72 h (horas corridas) | Ajustáveis em `sla_politicas`; horário comercial fica para depois |
| Google Workspace | Opcional, só para usuários já cadastrados | O UC01 exige cadastro prévio pelo ADMIN |
| Ícones das categorias | Emojis no banco, como no protótipo | Alternativa: nomes de ícones do `lucide` |
| Estado efêmero | Redis 8 | Valkey 8 é substituto direto, com licença BSD |
| Armazenamento S3 | SeaweedFS | Garage (AGPLv3, mais leve) ou AWS S3: só configuração |
| Notificações "em tempo real" | Consulta a cada 30 s | SSE fica como melhoria futura |

## 15. Relatório ao fim de cada fase

```markdown
## Relatório — Fase N: <nome>
**Requisitos atendidos:** RF.., RNF.., RN.., UC.., TU..
**O que foi feito:** (tópicos curtos)
**Como verificar:** (comandos e roteiro de cliques)
**Resultados:** lint ✔/✘ · testes X ok / Y falhas · cobertura de services X% · build ✔/✘ · RNF02 p95 = X ms (quando aplicável)
**Decisões registradas em DECISOES.md:** (lista)
**Pendências e riscos:** (lista)
**Próxima fase:** (resumo)
```

---

## 16. Assistente de IA (Mentory AI, RAG) — Fase 8

> Esta seção descreve a **visão final do produto**. Vale a regra de sempre: um recorte por vez,
> backend antes do front, e nada de regra de negócio em controller, componente de UI ou provedor.

### 16.1 Princípios

- **IA é um canal de atendimento, não um atalho que fura regra.** Abrir, consultar e responder
  chamado pela IA passa **pelos mesmos services** (RN04, RN06, RN01–RN03) e pelas permissões do
  usuário autenticado. A IA nunca executa SQL solto nem contorna o escopo do perfil.
- **Uma única fronteira conhece o protocolo do fornecedor.** O resto do sistema fala com `IaService`;
  trocar OpenAI ↔ Gemini ↔ Groq ↔ Ollama é só configuração. Providers são **sem estado**: a config
  chega por argumento (testáveis sem tocar no banco).
- **Degradar em vez de falhar.** Sem suporte a imagem ou a ferramentas, a conversa continua com o
  texto. Trocar de provedor nunca derruba o atendimento.
- **Segredo é segredo.** A chave do provedor é cifrada no banco (`core/seguranca`), decifrada só em
  memória, e **nunca** aparece em log, resposta HTTP ou mensagem de erro (redigir antes de truncar).
- **Minimização e rastreio (LGPD).** Guardar o mínimo da conversa; gravar métricas de token desde o
  início (base dos relatórios de consumo). Respostas citam a fonte (artigo da base) quando houver.

### 16.2 Camadas (`app/ia/`)

Espelha o desenho validado do `aiservicedesk` (ver `/home/ubuntu/ai-assistant`), em Python:

```text
app/ia/
├── contratos.py        # IaRequest, IaResposta, IaMensagem, ParteConteudo, DefinicaoFerramenta, PedidoFerramenta (neutros)
├── config.py           # IaConfig (provider, api_url, model, api_key, timeout, max_output_tokens); __repr__ oculta a chave
├── erros.py            # ErroIa: classifica a falha e decide o fallback (reason + deve_tentar_outro_modelo/provedor)
├── provedores/
│   ├── base.py         # ProvedorIa (Protocol): get_chave/rotulo/url_padrao, suporta_imagens/ferramentas, gerar()
│   ├── openai_compat.py# Provedor OpenAI-compatible (httpx): OpenAI, Gemini, Groq, OpenRouter, Ollama, vLLM, LM Studio
│   ├── groq.py · openrouter.py · cloudflare.py  # composição sobre o openai_compat (default model + capacidades + rótulo)
│   └── anthropic.py    # protocolo próprio (quando houver chave)
├── registro.py         # RegistroProvedores: catálogo; adicionar provedor = classe + 1 linha
├── fallback.py         # PoliticaFallbackModelo: modelos Gemini free quando a API Gemini responde 429/503
├── rag.py              # RagService: embedding da pergunta + busca semântica na base (fallback full-text F5)
└── ferramentas/        # FerramentaBuscarBase, FerramentaConsultarChamado, FerramentaAbrirChamado (reusam os services)
```

Serviços de orquestração em `app/services/ia/`:

- **`IaService`** — fachada. `gerar(IaRequest)` percorre a **cadeia de provedores** (config + cadeia
  de fallback); em cada provedor, aplica a **degradação** e o **fallback de modelo** por dentro.
- **`OrquestradorIa`** — laço de ferramentas: oferece as ferramentas, executa as que o modelo pedir
  (validando permissão no Python), devolve o resultado e segue até o modelo responder em texto ou
  bater o teto de rodadas (então força uma resposta final sem ferramentas).
- **`RagService`** — monta o contexto: recupera os artigos mais relevantes da Base de Conhecimento e
  injeta no prompt de sistema; a resposta cita os artigos usados.

### 16.3 Fallback (dois níveis, por motivo da falha)

A decisão vem da **classificação do erro** em `ErroIa.motivo`:

| Motivo | Troca de MODELO? | Troca de PROVEDOR? | Exemplo |
|---|---|---|---|
| `limite_de_taxa` (429) | sim | sim | cota/minuto estourada |
| `erro_servidor` (5xx) | sim | sim | Gemini 503 "high demand" |
| `tempo_esgotado` (timeout) | sim | sim | provedor lento |
| `inacessivel` (rede) | **não** | sim | host fora do ar (trocar modelo na mesma URL não adianta) |
| `nao_autorizado` (401/403) | não | **não** | credencial recusada → é defeito de config, tem de aparecer |
| `erro_cliente` (400) | não | **não** | requisição malformada |

- **Fallback de modelo** (`PoliticaFallbackModelo`): só para a **Gemini Developer API**
  (`generativelanguage.googleapis.com` via `openai_compat`). Tenta o modelo configurado primeiro;
  depois, uma lista de modelos Gemini com camada gratuita. **Nada persistido muda.**
- **Fallback de provedor**: percorre a cadeia configurada em `/admin/ia`.
- **Orçamento de tempo**: o conjunto de tentativas de modelo cabe em `timeout × 2` (não `timeout`
  por modelo); o 1º candidato sai com o prazo cheio, os demais com o tempo restante, descartados se
  sobrar menos que ~5 s. Evita que o fallback vire bomba de latência.
- **Streaming (SSE, opcional)**: depois de emitir texto, **não** troca de modelo/provedor (evita
  resposta "costurada"); conexão que morre sem `[DONE]` vira `finish_reason = interrompido`.

### 16.4 Dados (migration 0009)

- `ia_config`: provedor, `api_url`, `model`, `api_key_cifrada`, `timeout`, `max_output_tokens` e a
  **cadeia de fallback** (JSONB). Chave cifrada; nunca serializada.
- `ia_conversas` / `ia_mensagens`: histórico por usuário (papel, conteúdo, `tool_calls`, tokens,
  `finish_reason`), com retenção mínima.
- `ia_uso`: métricas de consumo (tokens de entrada/saída, duração, provedor, modelo) por chamada.
- `base_conhecimento.embedding`: vetor do artigo para o RAG. Em dev, sem servidor de embeddings
  dedicado, o RAG cai para a **busca full-text `pt_br_unaccent` da F5** — degradação, não falha.

### 16.5 API e segurança

- `POST /api/ia/conversas` (cria) · `POST /api/ia/conversas/{id}/mensagens` (envia; SSE opcional) —
  autenticado; o escopo do usuário vale dentro das ferramentas.
- `GET`/`PUT /api/admin/ia` (ADMIN): provedor, modelo, chave, cadeia de fallback; `POST
  /api/admin/ia/testar` faz uma chamada mínima ("ping") que prova credencial, URL, modelo e rede.
- Config pública (`/api/config/publica`) ganha `ia_habilitada` (só liga a tela do Assistente quando
  há provedor configurado) — mesmo padrão do `google_sso`.

### 16.6 Recortes (ver ROADMAP, F8)

F8.1 camada de provedores + fallback (sem UI) · F8.2 orquestrador + ferramentas seguras ·
F8.3 RAG sobre a Base de Conhecimento · F8.4 API de conversa + persistência · F8.5 `/admin/ia`
(config + teste + consumo) · F8.6 tela do Assistente (hero + chat) e saída do estado "em breve".

---

## Apêndice A — Mensagens para iniciar cada fase

- **Fase 0:** `Leia docs/PROMPT_IMPLEMENTACAO.md inteiro, além de docs/requisitos e docs/prototipo. Depois execute somente a Fase 0, seguindo as regras da seção 2, e termine com o relatório da seção 15.`
- **Fases seguintes:** `Execute a Fase N de docs/PROMPT_IMPLEMENTACAO.md. Antes de escrever código, liste o plano em até 10 itens. No fim, entregue o relatório da seção 15 e pare.`
- **Correção:** `Estes itens do DoD da Fase N falharam: <lista>. Corrija sem avançar de fase e entregue o relatório de novo.`

## Apêndice B — Requisitos citados nos documentos

Descrições resumidas a partir de como os códigos aparecem nos Documentos 01 a 03. Confiram com o levantamento de requisitos original do grupo.

| Código | Assunto | Telas e endpoints |
|---|---|---|
| RF01 | Cadastro de usuários | `/admin/usuarios` · `POST /api/usuarios` |
| RF02 | Registro de chamado (com anexos) | Novo Chamado · `POST /api/chamados` · anexos |
| RF03 | Tratamento e acompanhamento: atribuição, soluções, aprovação | Detalhe · triagem, atribuição, follow-ups, soluções |
| RF04 | Consulta e acompanhamento: Meus Chamados e Notificações | Meus Chamados · Dashboard · Notificações |
| RF05 | Classificação: categoria e severidade | Wizard, etapas 1 e 2 |
| RF06 | Base de Conhecimento | `/base-conhecimento` |
| RNF01 | Segurança: HTTPS e autenticação | Login · Traefik · JWT |
| RNF02 | Resposta em até 2 s | Dashboard · listagem |
| RNF03 | Layout responsivo (desktop e celular) | Todas as telas |
| UC01 | Cadastrar usuários (perfis de acesso) | Administração de usuários |
| UC02 | Registrar e classificar chamado | Novo Chamado |
| UC03 | Acompanhar chamado | Meus Chamados · Detalhe · Notificações |
| UC04 | Consultar Base de Conhecimento | Base de Conhecimento |
| UJ01 | Abrir chamado e acompanhar o atendimento | Login → Dashboard → Novo Chamado → Meus Chamados |
| FA01 / FA02 | Autoatendimento pela base / Esqueci minha senha | Base de Conhecimento / Login |
| FE01 / FE02 / FE03 | Credenciais inválidas / Campos obrigatórios / Cancelar ou Voltar | Login / Wizard / Wizard |
