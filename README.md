# Mentory Help Desk

Portal corporativo de chamados com três perfis (CLIENTE, ANALISTA e ADMIN): abertura em 3 etapas,
acompanhamento, ciclo de vida com aprovação da solução, Base de Conhecimento e notificações por
portal, e-mail e WhatsApp.

Projeto acadêmico — CEUNSP, Ciência da Computação, Análise e Projeto de Sistemas.

> **Situação:** organização concluída (E0). A Fundação (F0) ainda não começou; os passos para subir
> o ambiente entram aqui na F0.1. Andamento em [docs/DEVELOPMENT_STATUS.md](docs/DEVELOPMENT_STATUS.md).

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
├── backend/              API FastAPI (a partir da F0.2)
├── frontend/             SPA React (a partir da F0.5)
├── infra/                Postgres, Nginx (a partir da F0.1)
└── integrations/         n8n e WAHA (F6)
```
