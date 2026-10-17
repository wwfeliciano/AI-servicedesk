# Status de desenvolvimento

Andamento do projeto, recorte a recorte. Mais recente primeiro. O plano está em
[ROADMAP.md](ROADMAP.md).

## Situação atual (17/10/2026)

- **Etapa vigente:** F0 — Fundação. Último recorte: **F0.3 — Banco** (concluído).
  Próximo: **F0.4 — Qualidade e CI** (ruff/mypy/pytest com cobertura, GitHub Actions, template
  de PR), aguardando o pedido do usuário.
- **No ar:** `db`, `redis`, `s3` (MinIO), `mailpit`, `api` e `worker`, todos `healthy` (`make ps`).
  API em `http://127.0.0.1:8100` (dev). Banco com o esquema `0001` aplicado (`make migrate`).
- **Repositório:** Git local na branch `develop`, sem remoto.

## Pendências

- Definir o remoto do GitHub (público ou privado com GitHub Education — seção 3.3 do prompt).

## Decisões aprovadas, ainda não implementadas

Vão para [DECISOES.md](DECISOES.md) quando o código existir.

- **Backend antes do front-end** em cada etapa (pedido do usuário, 16/10/2026). Na F0, o front-end
  base é o último recorte (F0.5).
- **Etapas quebradas em recortes** (F0.1, F0.2...), no formato do GRH, com commit e relatório por
  recorte.

---

## F0.3 — Banco (17/10/2026)

- **Alembic** adicionado às dependências do backend (`alembic>=1.14,<1.15`, resolvido
  `1.14.1`); `uv.lock` atualizado. `alembic.ini` com `script_location = app/migrations` e
  `file_template` `%(rev)s_%(slug)s`; a `DATABASE_URL` vem de `app.core.config`, não do `.ini`.
  `env.py` com modos offline e online, `target_metadata = Base.metadata` e importação das
  entidades para o `--autogenerate`; respeita uma `sqlalchemy.url` já fixada (os testes injetam
  a URL do host).
- **Entidades** em `app/entities/` (um módulo por tabela + `enums.py` + `__init__`): `Usuario`,
  `Categoria`, `Chamado`, `FollowUp`, `Solucao`, `BaseConhecimento`. PKs `Identity(always=True)`
  (`categorias` em `INT`), `TIMESTAMPTZ`, ENUMs nativos referenciados com `create_type=False`,
  `protocolo` com `Computed(persisted=True)` (somente leitura), CHECKs, FKs `ON DELETE RESTRICT`,
  índice único parcial `uq_solucoes_uma_pendente` e índice trigram `ix_chamados_titulo_trgm`
  sobre `f_unaccent(lower(titulo))`.
- **Migration `0001_esquema_inicial`** produz exatamente o SQL da seção 5.2: extensões
  `pg_trgm`/`unaccent`, função `IMMUTABLE f_unaccent`, os 4 tipos ENUM, as 6 tabelas (com a
  coluna gerada, CHECKs e índices) e as 7 categorias (TI, RH, Financeiro, Acesso, Hardware,
  Software, Outro). `downgrade()` reverte tudo, inclusive `DROP TYPE`, `DROP FUNCTION` e
  `DROP EXTENSION`.
- **Compose:** serviço `migrate` (imagem do backend, `alembic upgrade head`, one-shot,
  `depends_on db healthy`, 0,25 CPU/256 MB, sem porta); `api` e `worker` agora dependem de
  `migrate` com `service_completed_successfully`. `Dockerfile` copia o `alembic.ini` para a
  imagem.
- **Makefile:** `make migrate` (`docker compose run --rm migrate`) e
  `make migration nome=...` (`alembic revision --autogenerate`, para revisão manual).
- **Testes (10 no total, 2 novos):** `test_conexao_banco` (PostgreSQL real: 6 tabelas, 4 ENUMs e
  7 categorias) e `test_migrations_ida_e_volta` (`upgrade → downgrade base → upgrade`). Ambos
  pulam se o banco não estiver no ar. A URL do host é montada a partir do `.env` da raiz
  (`db:5432` → `127.0.0.1:PORTA_DB`). Sem ids fixos (as sequências `IDENTITY` não voltam).
- **Documentação:** `docs/der.md` (Mermaid das 6 tabelas e invariantes), `docs/DECISOES.md`
  (ADR 2026-10-17 com as diferenças da seção 5.3 e o Alembic como ferramenta de migration),
  `docs/ROADMAP.md` (F0.3 concluído), `docs/RASTREABILIDADE.md` (itens do DoD do banco) e
  `README.md` (`make migrate`).
- **Validação:**
  - `make lint` ok (ruff check, ruff format --check, mypy `strict`, 21 arquivos);
  - `make migrate` aplicou o esquema; conferidas 6 tabelas, 4 ENUMs, FKs, índices e 7 categorias;
  - ida e volta (`alembic upgrade head → downgrade base → upgrade head`) limpa, com os ENUMs e a
    função removidos no `downgrade`;
  - `make test` 10 passaram (inclui `test_conexao_banco` e a ida e volta);
  - `docker compose config` ok; serviço `migrate` roda e sai com código 0; `git diff --check`
    limpo.

## Pendências e riscos

- O `--autogenerate` relata duas diferenças cosméticas e esperadas no `chamados.protocolo`:
  `NOT NULL` (o Alembic não altera a nulabilidade de coluna gerada) e a representação da
  unicidade do protocolo (índice único, como no SQL). Não afetam o esquema; a migration escrita
  à mão é a fonte da verdade.

---

## F0.2 — API base (17/10/2026)

- `backend/` com FastAPI, estrutura em camadas iniciada (`app/core`, `app/controllers`).
  Dependências com `uv` (projeto não-empacotado, `package = false`): FastAPI, Uvicorn,
  pydantic-settings, SQLAlchemy 2.0 síncrono + psycopg 3, redis e Typer; dev: Ruff, mypy, pytest,
  pytest-cov, httpx e fakeredis. `uv.lock` commitado.
- `app/main.py` (`create_app`): middleware de `X-Request-ID` (recebe ou gera; devolve no header e
  propaga para os logs), handlers de erro e router de health. OpenAPI em `/api/docs` e
  `/api/openapi.json`, desligados em produção.
- `app/core`: `config.py` (pydantic-settings, lê o `.env`, só os campos usados na F0.2,
  `extra="ignore"`); `logging.py` (logs JSON em stdout com `request_id`); `database.py` (engine e
  sessão síncronos; `Base` declarativa — a API nunca aplica migration); `redis.py`
  (`criar_cliente_redis` e `chave()` com o prefixo); `errors.py` (formato único da seção 7.1:
  `ErroAPI`, conversão dos erros do Pydantic/HTTP e mensagens em PT-BR).
- `app/controllers/health.py`: `GET /api/health` (vida da API) e `GET /api/health/db`
  (`SELECT 1`; `503 BANCO_INDISPONIVEL` quando o banco não responde).
- `app/worker.py`: esqueleto rodado por `python -m app.worker`; mantém `worker:heartbeat` no Redis
  (TTL de 30 s), base para o despacho do outbox na F6. Encerra em `SIGTERM`/`SIGINT`.
- `backend/Dockerfile` multi-stage (uv + `python:3.13.16-slim`, `uv sync --frozen --no-dev`,
  usuário não-root) e `.dockerignore`.
- `docker-compose.yml`: serviços `api` (healthcheck `GET /api/health`, depende de `db` e `redis`
  saudáveis, 0,5 CPU/512 MB) e `worker` (healthcheck pela chave `worker:heartbeat`, 0,25 CPU/256 MB).
  Override de dev: API em `127.0.0.1:8100`, `--reload` e `./backend/app` montado só leitura. A
  dependência de `migrate` (`service_completed_successfully`) entra na F0.3 junto com o Alembic.
- `Makefile`: `lint` (ruff check + format --check + mypy), `test` (pytest) e `build`.
- **Testes (8):** health, header `X-Request-ID` gerado, `X-Request-ID` recebido e propagado,
  `/api/health/db` ok (sessão substituída), `/api/health/db` → 503 no formato único, rota
  inexistente no formato único (mensagem PT-BR) e heartbeat do worker (fakeredis).
- **Validação:**
  - `make lint` ok (ruff check, ruff format --check, mypy `strict`); `make test` 8 passaram;
  - `docker compose config` ok; `make build` sem erros;
  - `make up`: `db`, `redis`, `s3`, `mailpit`, `api` e `worker` ficaram `healthy`;
  - `GET /api/health` → `200 {"status":"ok"}` com `X-Request-ID`; `GET /api/health/db` →
    `200 {"status":"ok","db":"ok"}`; `X-Request-ID` enviado é devolvido; rota inexistente →
    `404 {"codigo":"NAO_ENCONTRADO","mensagem":"Recurso não encontrado."}`; logs saíram em JSON;
    `worker:heartbeat` presente no Redis com TTL dentro de 30 s.
- O `test_conexao_banco` com PostgreSQL real e as 6 tabelas, e o serviço `migrate`, entram na F0.3.

## F0.1 — Infraestrutura (16/10/2026)

- `docker-compose.yml` base com `db` (PostgreSQL 17.11), `redis` (8.8.3) e `s3` (MinIO
  RELEASE.2026-09-22 pelo digest do Chainguard), na rede interna `interna`, com volumes, healthcheck,
  `restart: unless-stopped` e limites de CPU e memória (total de 2,75 CPU e 1,9 GB).
- `docker-compose.override.yml` (dev): portas só em `127.0.0.1` (PostgreSQL 5442, MinIO 9100 e
  9101, Mailpit 8125 e 1125) e o Mailpit v1.31.6.
- Redis com `maxmemory 200mb` e `volatile-lru`: só estado efêmero com TTL (seção 5.5).
- `infra/postgres/init/01-n8n.sh`: cria o banco e o usuário do n8n na primeira inicialização do
  volume (usado na F6).
- `.env.example` completo (seção 10.2, adaptado ao MinIO e às portas); `infra/gerar-env.sh` cria o
  `.env` com segredos aleatórios e a `DATABASE_URL` coerente, sem sobrescrever nem exibir.
- `Makefile`: `help`, `env`, `config`, `up` (valida e espera `healthy`), `down`, `ps` e `logs`.
- Decisões registradas: MinIO no lugar do SeaweedFS; portas de dev em `127.0.0.1`.
- **Validação:**
  - `docker compose config` ok; os 4 serviços `healthy` em cerca de 10 s;
  - PostgreSQL 17.11 aarch64, extensões `pg_trgm` e `unaccent` disponíveis, fuso
    `America/Sao_Paulo`, banco `n8n` criado pelo script;
  - Redis responde com a política `volatile-lru`;
  - MinIO: criar bucket, gravar, ler e remover objeto ok; sem credencial, 403; health 200;
  - Mailpit UI 200; nenhuma porta fora de `127.0.0.1`; consumo em repouso de cerca de 95 MB.
- Sem testes automatizados neste recorte: o primeiro (`test_conexao_banco`) entra na F0.3.

## E0.1 — Organização do repositório (16/10/2026)

- Documentação no formato do projeto GRH: `AGENTS.md`, `docs/INSTRUCOES_AGENTES.md`,
  `docs/ROADMAP.md`, este arquivo, `docs/DECISOES.md`, `docs/AJUSTES_IDENTIFICADOS.md`,
  `docs/RASTREABILIDADE.md`, `docs/telas/` e `README.md`.
- Pacote do grupo copiado para `docs/`: `PROMPT_IMPLEMENTACAO.md`, `requisitos/` (Documentos 01 a
  03) e `prototipo/` (6 capturas).
- Ambiente preparado no servidor: `make` pelo apt; `uv` 0.13.1 em `~/.local/bin`; Python 3.13.16
  gerenciado pelo uv; imagens fixadas baixadas e conferidas para ARM64.
- Um rascunho de API feito antes da organização foi apagado a pedido do usuário; a F0 recomeçou do
  zero pela F0.1.
