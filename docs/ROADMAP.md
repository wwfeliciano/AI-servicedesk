# Roadmap

Etapas do projeto, quebradas em recortes pequenos. Cada recorte vira código, testes e documentação,
e só começa quando o usuário pede. O detalhe técnico de cada etapa está na seção 13 de
[`PROMPT_IMPLEMENTACAO.md`](PROMPT_IMPLEMENTACAO.md).

Registros vizinhos, cada um com propósito próprio:

- [DEVELOPMENT_STATUS.md](DEVELOPMENT_STATUS.md): o andamento, recorte a recorte;
- [DECISOES.md](DECISOES.md): decisões tomadas e implementadas;
- [AJUSTES_IDENTIFICADOS.md](AJUSTES_IDENTIFICADOS.md): defeitos e ajustes encontrados no uso;
- [RASTREABILIDADE.md](RASTREABILIDADE.md): requisitos → endpoints, telas e testes.

## Estados

- `futuro`: previsto, ainda não pedido;
- `próximo`: candidato ao próximo recorte;
- `em_andamento`: em desenvolvimento;
- `concluído`: código, testes e documentação entregues e validados;
- `adiado`: deixado para depois de propósito.

## Resumo

| Etapa | Assunto | Requisitos | Estado |
|---|---|---|---|
| E0 | Organização do repositório e da documentação | — | concluído |
| F0 | Fundação: infraestrutura, API base, banco e CI | Doc 02 | em_andamento |
| F1 | Autenticação e cadastro de usuários | UC01, RF01, RN07, RNF01 | futuro |
| F2 | Abertura e consulta de chamados | UC02, UC03, RF02, RF05, RN04, RN06, RNF02, RNF03 | futuro |
| F3 | Anexos e notificações no portal | RF02, RF04 | futuro |
| F4 | Ciclo de vida do chamado | RF03, RN01, RN02, RN03, UC03 | futuro |
| F5 | Base de Conhecimento | RF06, RN05, UC04, FA01 | futuro |
| F6 | Canais externos: e-mail e WhatsApp (n8n + WAHA) | — | futuro |
| F7 | Complementos e produção | FA02, UJ01 | futuro |

Em cada etapa, o backend vem antes do front-end.

---

## E0 — Organização

Estrutura de documentação no mesmo formato do projeto GRH, antes de qualquer código validado.

| Recorte | Entrega | Estado |
|---|---|---|
| E0.1 | `AGENTS.md`, `docs/INSTRUCOES_AGENTES.md`, `ROADMAP`, `DEVELOPMENT_STATUS`, `DECISOES`, `AJUSTES_IDENTIFICADOS`, `RASTREABILIDADE`, `docs/telas/`, `README.md` e `.gitignore` | concluído |

## F0 — Fundação (Documento 02)

| Recorte | Entrega | Estado |
|---|---|---|
| F0.1 | Infraestrutura: `docker-compose.yml` (db, redis, s3/MinIO), override de dev, `.env.example`, `Makefile`, portas em `127.0.0.1` e limites de recursos | concluído |
| F0.2 | API base: `create_app`, configuração, logs JSON, `X-Request-ID`, formato único de erro, `/api/health` e `/api/health/db`; Dockerfile do backend; serviços `api` e `worker` (esqueleto com heartbeat) | concluído |
| F0.3 | Banco: entidades das 6 tabelas, migration `0001_esquema_inicial`, serviço `migrate`, `docs/der.md`, `test_conexao_banco` e ida e volta das migrations | concluído |
| F0.4 | Qualidade e CI: ruff, mypy, pytest com cobertura, GitHub Actions, template de PR | concluído |
| F0.5 | Front-end base: Vite + React + Tailwind com os tokens da seção 8.2, `AppShell` fiel ao protótipo, rotas com telas vazias, serviço `web` (Nginx) | próximo |

**DoD da F0** (seção 13 do prompt): `make up` sobe tudo saudável; `make migrate` cria as 6 tabelas,
FKs, ENUMs, índices e as 7 categorias; `test_conexao_banco` e ida e volta passam; `make build` sem
erros e CI verde; README reproduz o ambiente do zero.

## F1 — Autenticação e cadastro de usuários

| Recorte | Entrega | Estado |
|---|---|---|
| F1.1 | Migration 0002 (`tokens_refresh`), login, refresh, logout, `me`, troca de senha, limite de tentativas | futuro |
| F1.2 | `make criar-admin`, `POST` e `GET /api/usuarios`, `/api/config/publica` (TU05, TU06, TU07) | futuro |
| F1.3 | Telas de Login, Perfil e `/admin/usuarios`; rotas protegidas por perfil | futuro |

## F2 — Abertura e consulta de chamados

| Recorte | Entrega | Estado |
|---|---|---|
| F2.1 | `GET /api/categorias`, `POST /api/chamados` com RN04 (TU01–TU04) | futuro |
| F2.2 | `GET /api/chamados` com busca, filtros, contadores e paginação; `/resumo` e `/{id}`; RN06 (TU07, TU08) | futuro |
| F2.3 | `make seed` e `make seed-performance`; medição do RNF02 | futuro |
| F2.4 | Telas: Dashboard, Novo Chamado (3 etapas), confirmação, Meus Chamados, Detalhe | futuro |

## F3 a F7

Os recortes são definidos ao iniciar cada etapa, a partir da seção 13 do prompt.
