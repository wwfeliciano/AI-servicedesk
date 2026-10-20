# Mentory Help Desk

Portal corporativo de chamados com três perfis (CLIENTE, ANALISTA e ADMIN): abertura em 3 etapas,
acompanhamento, ciclo de vida com aprovação da solução, Base de Conhecimento e notificações por
portal, e-mail e WhatsApp.

Projeto acadêmico — CEUNSP, Ciência da Computação, Análise e Projeto de Sistemas.

> **Situação:** Fases 0 a 6 concluídas (~97%). No ar: banco, Redis, MinIO, Mailpit, API, worker, o
> `web` (SPA React/Nginx) e os serviços de integração **n8n** e **WAHA**. Já funcionam
> autenticação, abertura/consulta de chamados, anexos, notificações, o ciclo de vida completo, a
> Base de Conhecimento (busca full-text) e os canais externos (e-mail/WhatsApp via outbox → n8n →
> WAHA/SMTP, com bot e vínculo pelo WhatsApp). Próxima etapa: **F7** (esqueci a senha, SLA do mês,
> login com Google e itens de produção). Andamento em
> [docs/DEVELOPMENT_STATUS.md](docs/DEVELOPMENT_STATUS.md).

## Pré-requisitos

- Linux com Docker Engine e Compose v2 (o servidor do projeto é ARM64; todas as imagens têm build
  para ARM64 e x86-64).
- `make` e `openssl`.

Docker Desktop só é gratuito para uso pessoal, projetos open source não comerciais e empresas com
menos de 250 funcionários e menos de US$ 10 milhões de receita anual. Fora disso, use Docker
Engine no Linux/WSL2, Rancher Desktop ou Podman Desktop.

## Como subir

```bash
make env     # cria o .env com segredos aleatórios (não sobrescreve um existente)
make up      # valida o Compose, sobe os serviços e espera ficarem saudáveis
make migrate # aplica as migrations (serviço migrate); cria as 6 tabelas e as 7 categorias
make ps      # estado dos serviços
make help    # todos os atalhos
```

Primeiro administrador (lê `ADMIN_NOME`, `ADMIN_EMAIL` e `ADMIN_SENHA` do `.env`; idempotente, não
duplica). Exige a imagem do backend atualizada (`make build`):

```bash
make criar-admin
```

Dados de desenvolvimento (só com `AMBIENTE=dev`; dados fictícios, senha padrão `mentory-dev-123`):

```bash
make seed              # 1 admin + 3 analistas + 10 clientes e ~60 chamados variados (idempotente)
make seed-performance  # 200 usuários e 10.000 chamados em lote, para medir o RNF02
make test-performance  # roda o teste de desempenho do RNF02 (lista ≤ 2 s), sob demanda
```

A tela de login consome `GET /api/config/publica` (rota pública: canais de suporte, disponibilidade
do login com Google e versão da API).

Qualidade e build do backend (usam o `uv` no host):

```bash
make lint      # ruff check, ruff format --check e mypy strict
make format    # aplica o ruff format no backend
make test      # pytest com cobertura (--cov=app, term-missing); inclui test_conexao_banco com PostgreSQL real
make build     # build das imagens Docker (api e worker)
make migration nome=descricao   # gera uma migration por autogenerate (revisar à mão)
```

Front-end (SPA React + Vite + Tailwind 4; usam o `npm` no host):

```bash
make front-install  # npm ci
make front-dev      # Vite em 127.0.0.1:5173, com proxy /api → 127.0.0.1:8100
make front-lint     # ESLint + typecheck (tsc --noEmit)
make front-test     # Vitest
make front-build    # build de produção (tsc -b && vite build)
make front-gen-api  # regenera src/api/schema.ts a partir do OpenAPI (API no ar)
```

Serviços em desenvolvimento (portas só em `127.0.0.1`, configuráveis no `.env`):

| Serviço | Endereço no host | Uso |
|---|---|---|
| Web (SPA React/Nginx) | `http://127.0.0.1:8180` | Portal; faz proxy de `/api` para a API |
| API (FastAPI) | `http://127.0.0.1:8100` | `GET /api/health` e `/api/health/db`; docs em `/api/docs` |
| PostgreSQL 17 | `127.0.0.1:5442` | DBeaver: banco, usuário e senha do `.env` |
| MinIO (S3) | `http://127.0.0.1:9100` | API S3 dos anexos (F3) |
| Console do MinIO | `http://127.0.0.1:9101` | usuário `S3_ACCESS_KEY`, senha `S3_SECRET_KEY` |
| Mailpit | `http://127.0.0.1:8125` | caixa de e-mails de teste (SMTP em 1125) |
| n8n | `http://127.0.0.1:5678` | automação dos canais externos (F6); ver `integrations/n8n/` |
| WAHA | `http://127.0.0.1:3000` | WhatsApp HTTP API (F6); sessão/QR, ver `integrations/waha/` |

Para abrir de outra máquina, use um túnel SSH (`ssh -L 9101:127.0.0.1:9101 ubuntu@servidor`) ou o
encaminhamento de portas do VS Code.

`make down` para os serviços e preserva os volumes (dados do banco e do MinIO).

### Solução de problemas

- **Porta em uso:** troque `PORTA_*` no `.env` e rode `make up` de novo.
- **Serviço `unhealthy`:** `make logs s=<serviço>`.
- **Banco do n8n não criado:** o script de `infra/postgres/init/` só roda quando o volume
  `pg_data` é criado pela primeira vez.

## Stack

Python 3.13 (FastAPI, SQLAlchemy 2.0, Alembic) · React 19 + TypeScript (Vite, Tailwind 4) ·
PostgreSQL 17 · Redis 8 · MinIO (API S3) · n8n + WAHA · Docker Compose. Detalhes e licenças na
seção 3 do [prompt de implementação](docs/PROMPT_IMPLEMENTACAO.md).

## Integração contínua e fluxo de branches

O workflow `.github/workflows/ci.yml` (GitHub Actions) roda em cada `pull_request` e nos `push`
para `develop` e `main`. O job `backend` sobe um serviço PostgreSQL 17, instala o `uv` (versão
fixada) e o Python 3.13, e executa `ruff check`, `ruff format --check`, `mypy` (strict),
`alembic upgrade head` e `pytest` com cobertura. As ações são fixadas por versão (sem `@latest`).

Fluxo do Documento 02 (seção 12.4): `feature/*` → PR para `develop` → PR para `main`. O repositório
usa o template de PR em `.github/pull_request_template.md`.

Proteção de branch pretendida no GitHub (configuração manual no repositório, documentação apenas):

- **`main` protegida:** PR obrigatório, pelo menos **1 aprovação** e **build verde** (o job `backend`
  do CI como *required status check*); sem push direto; sem `force-push`.
- **`develop`:** recebe os PRs das `feature/*`; CI verde exigido antes do merge.
- Proteção com revisão obrigatória em repositório privado exige GitHub Pro/Team; alternativa sem
  custo é repositório público ou o GitHub Education (seção 3.3 do prompt).

## Documentação

| Documento | Para quê |
|---|---|
| [AGENTS.md](AGENTS.md) | Regras permanentes do projeto (para pessoas e agentes de código) |
| [docs/INSTRUCOES_AGENTES.md](docs/INSTRUCOES_AGENTES.md) | Como trabalhar em cada recorte; ambiente, imagens e portas |
| [docs/PROMPT_IMPLEMENTACAO.md](docs/PROMPT_IMPLEMENTACAO.md) | Especificação completa: arquitetura, dados, API, telas e fases |
| [docs/requisitos/](docs/requisitos/) | Documentos 01, 02 e 03 do grupo |
| [docs/prototipo/](docs/prototipo/) | Capturas do protótipo (referência visual) |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Etapas e recortes, com estado |
| [docs/DEVELOPMENT_STATUS.md](docs/DEVELOPMENT_STATUS.md) | Andamento, recorte a recorte |
| [docs/DECISOES.md](docs/DECISOES.md) | Decisões implementadas (ADR curto) |
| [docs/RASTREABILIDADE.md](docs/RASTREABILIDADE.md) | RF/RNF/RN/UC → endpoints, telas e testes |
| [docs/AJUSTES_IDENTIFICADOS.md](docs/AJUSTES_IDENTIFICADOS.md) | Defeitos e ajustes encontrados |
| [docs/telas/](docs/telas/) | Comportamento das telas e histórico de mudanças |

## Estrutura

```text
helpdeskai/
├── AGENTS.md · CLAUDE.md · README.md
├── docs/                 documentação (acima)
├── backend/              API FastAPI (app/core, controllers; worker) — banco e migrations na F0.3
├── frontend/             SPA React (Vite + Tailwind 4; servida pelo Nginx no serviço web)
├── infra/                init do Postgres, gerador do .env
├── docker-compose.yml    serviços base · docker-compose.override.yml: dev
├── Makefile · .env.example
└── integrations/         n8n e WAHA (F6)
```
