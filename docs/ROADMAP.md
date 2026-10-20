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
| F0 | Fundação: infraestrutura, API base, banco e CI | Doc 02 | concluído |
| F1 | Autenticação e cadastro de usuários | UC01, RF01, RN07, RNF01 | concluído |
| F2 | Abertura e consulta de chamados | UC02, UC03, RF02, RF05, RN04, RN06, RNF02, RNF03 | concluído |
| F3 | Anexos e notificações no portal | RF02, RF04 | concluído |
| F4 | Ciclo de vida do chamado | RF03, RN01, RN02, RN03, UC03 | concluído |
| F5 | Base de Conhecimento | RF06, RN05, UC04, FA01 | concluído |
| F6 | Canais externos: e-mail e WhatsApp (n8n + WAHA) | — | concluído |
| F7 | Complementos e produção | FA02, UJ01 | próximo |
| F8 | Assistente de IA (Mentory AI, RAG) | visão de produto | futuro |

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
| F0.5 | Front-end base: Vite + React + Tailwind com os tokens da seção 8.2, `AppShell` fiel ao protótipo, rotas com telas vazias, serviço `web` (Nginx) | concluído |

**DoD da F0** (seção 13 do prompt): `make up` sobe tudo saudável; `make migrate` cria as 6 tabelas,
FKs, ENUMs, índices e as 7 categorias; `test_conexao_banco` e ida e volta passam; `make build` sem
erros e CI verde; README reproduz o ambiente do zero. **F0 concluída** com a F0.5 (17/10/2026).

> **F0.5 (17/10/2026):** retomada após a F1.1/F1.2. O `frontend/` residual foi refeito na
> **identidade do esboço** (ADR 2026-10-17): marca teal, IBM Plex Sans, sidebar branca, tema claro
> e escuro. Entrega: tokens em Tailwind 4, `AppShell` (sidebar + topbar + gaveta mobile), alternância
> de tema persistida, rotas protegidas por perfil (stub) com telas vazias, Login fora do shell e o
> serviço `web` (Nginx). O assistente de IA aparece como item "em breve" (visão de produto). Front
> verde: lint, typecheck, Vitest e build.

## F1 — Autenticação e cadastro de usuários

| Recorte | Entrega | Estado |
|---|---|---|
| F1.1 | Migration 0002 (`tokens_refresh`), login, refresh, logout, `me`, troca de senha, limite de tentativas | concluído |
| F1.2 | `make criar-admin`, `POST` e `GET /api/usuarios`, `/api/config/publica` (TU05, TU06, TU07) | concluído |
| F1.3 | Telas de Login, Perfil e `/admin/usuarios`; rotas protegidas por perfil | concluído |

## F2 — Abertura e consulta de chamados

| Recorte | Entrega | Estado |
|---|---|---|
| F2.1 | `GET /api/categorias`, `POST /api/chamados` com RN04 (TU01–TU04) | concluído |
| F2.2 | `GET /api/chamados` com busca, filtros, contadores e paginação; `/resumo` e `/{id}`; RN06 (TU07, TU08) | concluído |
| F2.3 | `make seed` e `make seed-performance`; medição do RNF02 | concluído |
| F2.4 | Telas: Dashboard, Novo Chamado (3 etapas), confirmação, Meus Chamados, Detalhe | concluído |

## F3 — Anexos e notificações no portal

| Recorte | Entrega | Estado |
|---|---|---|
| F3.1 | Migration 0003 (anexos, notificacoes); `StorageService` (MinIO/boto3); `POST`/`GET` de anexos e download, com escopo e validação (≤5, 10 MB, PNG/JPG/PDF) — TU16 | concluído |
| F3.2 | `EventoService` (canal Portal): eventos na abertura; `GET /api/notificacoes` e `/contagem`, `POST /{id}/lida` e `/lidas` — TU17 (portal) | concluído |
| F3.3 | Front: zona de upload no wizard e no detalhe; tela de Notificações e contador no menu (polling 30 s) | concluído |

## F4 — Ciclo de vida do chamado

| Recorte | Entrega | Estado |
|---|---|---|
| F4.1 | Migration 0004 (`historico_chamado`, `data_conclusao`/`data_fechamento`); `CicloVidaService` com triagem (NOVO→PENDENTE) e atribuição (→ATRIBUIDO, RN03); histórico — TU09, TU10 | concluído |
| F4.2 | Solução (ATRIBUIDO→CONCLUIDO, RN01), resposta do solicitante (aprovar→FECHADO RN02 / reprovar→ATRIBUIDO); follow-ups; `PATCH /api/usuarios` (ativar/desativar) — TU11–TU14 | concluído |
| F4.3 | Front: detalhe com linha do tempo e ações por perfil, cartão da solução; fila de ANALISTA/ADMIN (filtros); `/admin/usuarios` editar/ativar | concluído |

## F5 — Base de Conhecimento

| Recorte | Entrega | Estado |
|---|---|---|
| F5.1 | Migration 0005 (busca full-text `pt_br_unaccent`); `GET /api/base-conhecimento` (busca + filtro por categoria) e `/{id}`; `POST`/`PATCH` a partir de solução aprovada (RN05) — TU15 | concluído |
| F5.2 | Front: tela `/base-conhecimento` (busca, filtro, acordeão), "Abrir chamado" a partir do artigo; publicar a partir de chamado com solução aprovada (ANALISTA/ADMIN) | concluído |

## F6 — Canais externos (e-mail e WhatsApp via n8n + WAHA)

| Recorte | Entrega | Estado |
|---|---|---|
| F6.1 | Backend: migration `0006_canais_externos` (colunas de WhatsApp/e-mail em `usuarios`, `canal_origem` em `chamados`, ENUMs `canal_notificacao`/`status_outbox`/`canal_origem`, tabela `eventos_outbox`); entidade `EventoOutbox`; `OutboxRepository`; `EventoService` passa a gravar também no outbox (e-mail/WhatsApp conforme a matriz 9.6 e as preferências), na mesma transação | concluído |
| F6.2 | Worker: laço de despacho do outbox (reserva em lote com `FOR UPDATE SKIP LOCKED`, `POST` ao n8n, backoff/retentativas, `OUTBOX_HABILITADO`); `GET /api/admin/outbox` e reenvio | concluído |
| F6.3 | Vínculo do WhatsApp (perfil): consentimento, código no Redis, link `wa.me`, status/desvínculo e `PATCH /api/perfil/preferencias`; tela `/perfil` (WhatsApp) | concluído |
| F6.4 | Bot de atendimento (núcleo): `POST /api/integracoes/whatsapp/mensagens` (auth por chave, dedup); identificação por chat_id/lid/numero; textos (`app/integrations/whatsapp/mensagens.py`) e estado da conversa (Redis); `VINCULAR`, menu, meus chamados, status por protocolo (RN06), opt-out, mídia e não-vinculado | concluído |
| F6.4b | Bot: fluxo guiado de abertura (*1*, com `canal_origem=WHATSAPP`), aprovação/reprovação da solução pelo WhatsApp, `POST /api/integracoes/whatsapp/sessao` e tela `/admin/integracoes` | concluído |
| F6.5 | Infra n8n + WAHA (compose), workflows exportados e READMEs; ligação ponta a ponta com Mailpit em dev | concluído — fecha a F6 |

## F7 — Complementos e produção

| Recorte | Entrega | Estado |
|---|---|---|
| F7.1 | Redefinição de senha por e-mail (FA02): migration `0007` (`tokens_redefinicao_senha`), `POST /api/auth/esqueci-senha` e `POST /api/auth/redefinir-senha`, evento `SENHA_REDEFINICAO` (e-mail via outbox), telas `/esqueci-senha` e `/redefinir-senha` | concluído |
| F7.2 | SLA: migration `0008` (`sla_politicas` + `chamados.prazo_sla`), cálculo do prazo na abertura, `GET /api/sla/mes` e cartão "SLA do mês" no Dashboard | concluído |
| F7.3 | Login com Google Workspace (UJ01, opcional): `GET /api/auth/google/login` e `/callback`, botão no Login (só com `google_sso`) | próximo |
| F7.4 | Produção: `docker-compose.prod.yml` (labels do Traefik, sem portas publicadas), HTTPS e checklist de deploy | futuro |

## F8 — Assistente de IA (Mentory AI, RAG)

Visão final do produto (ADR 2026-10-17): o item "Assistente IA" sai do estado "em breve". Detalhe
técnico na **seção 16** do prompt; a arquitetura espelha, em Python, o desenho do plugin
`aiservicedesk` (provider abstraction, fallback de modelo e de provedor, orçamento de tempo,
degradação, RAG). Depende de chave de provedor (ex.: Gemini) — ver `DECISOES_PENDENTES.md`.

| Recorte | Entrega | Estado |
|---|---|---|
| F8.1 | Camada `app/ia/` sem UI: contratos neutros (`IaRequest`/`IaResposta`/`IaMensagem`/ferramentas), `IaConfig` (chave oculta), `ErroIa` (classificação + decisão de fallback), `ProvedorIa` (Protocol), `ProvedorOpenAiCompat` (httpx; cobre Gemini/OpenAI/Groq/OpenRouter/Ollama), registro, `PoliticaFallbackModelo` (Gemini free no 429/503), `IaService` (cadeia de provedores + orçamento de tempo + degradação) | futuro |
| F8.2 | `OrquestradorIa` (laço de ferramentas) + ferramentas seguras (buscar na base, consultar/abrir chamado) **reusando os services** (RN04/RN06 e permissões); teto de rodadas com resposta final forçada | futuro |
| F8.3 | RAG: `base_conhecimento.embedding` (migration 0009, parte), `RagService` (embedding + busca semântica) com _fallback_ para o full-text `pt_br_unaccent` da F5; respostas citam os artigos | futuro |
| F8.4 | Migration 0009 (`ia_config`, `ia_conversas`, `ia_mensagens`, `ia_uso`); `POST /api/ia/conversas` e `/{id}/mensagens` (SSE opcional); persistência do histórico e das métricas de token | futuro |
| F8.5 | `/admin/ia` (ADMIN): provedor, modelo, chave cifrada, cadeia de fallback, `POST /api/admin/ia/testar` (ping) e consumo; `ia_habilitada` em `/api/config/publica` | futuro |
| F8.6 | Front: tela do Assistente (hero conversacional + chat, com citação dos artigos) e saída do estado "em breve"; item de menu ativo | futuro |

Os recortes são definidos ao iniciar cada etapa, a partir da seção 13 do prompt.
