# Mentory Help Desk

Portal corporativo de chamados com três perfis (CLIENTE, ANALISTA e ADMIN): abertura em 3 etapas,
acompanhamento, ciclo de vida com aprovação da solução, Base de Conhecimento e notificações por
portal, e-mail e WhatsApp.

Projeto acadêmico — CEUNSP, Ciência da Computação, Análise e Projeto de Sistemas.

> **Situação:** Fase 0 em andamento. Sobem banco, Redis, MinIO, Mailpit, a API e o worker; o
> esquema do banco (6 tabelas, ENUMs, índices e as 7 categorias) é aplicado por `make migrate`
> (F0.3 concluída).
> Andamento em [docs/DEVELOPMENT_STATUS.md](docs/DEVELOPMENT_STATUS.md).

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

Qualidade e build do backend (usam o `uv` no host):

```bash
make lint      # ruff check, ruff format --check e mypy strict
make test      # pytest (inclui test_conexao_banco com PostgreSQL real)
make build     # build das imagens Docker (api e worker)
make migration nome=descricao   # gera uma migration por autogenerate (revisar à mão)
```

Serviços em desenvolvimento (portas só em `127.0.0.1`, configuráveis no `.env`):

| Serviço | Endereço no host | Uso |
|---|---|---|
| API (FastAPI) | `http://127.0.0.1:8100` | `GET /api/health` e `/api/health/db`; docs em `/api/docs` |
| PostgreSQL 17 | `127.0.0.1:5442` | DBeaver: banco, usuário e senha do `.env` |
| MinIO (S3) | `http://127.0.0.1:9100` | API S3 dos anexos (F3) |
| Console do MinIO | `http://127.0.0.1:9101` | usuário `S3_ACCESS_KEY`, senha `S3_SECRET_KEY` |
| Mailpit | `http://127.0.0.1:8125` | caixa de e-mails de teste (SMTP em 1125) |

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
├── frontend/             SPA React (a partir da F0.5)
├── infra/                init do Postgres, gerador do .env (Nginx na F0.5)
├── docker-compose.yml    serviços base · docker-compose.override.yml: dev
├── Makefile · .env.example
└── integrations/         n8n e WAHA (F6)
```
