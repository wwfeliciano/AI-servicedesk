# Rastreabilidade

Liga cada código dos Documentos 01 a 03 (e do prompt) ao que o implementa e ao que o testa. Uma
linha só muda para `implementado` quando o código e o teste existem.

Estados: `pendente` · `em_andamento` · `implementado`.

## Requisitos funcionais

| Código | Assunto | Fase | Endpoints | Telas | Testes | Estado |
|---|---|---|---|---|---|---|
| RF01 | Cadastro de usuários | F1 | `POST`/`GET /api/usuarios` | `/admin/usuarios` | TU05, TU06 | implementado |
| RF02 | Registro de chamado (com anexos) | F2, F3 | `POST /api/chamados`, anexos | Novo Chamado | TU01–TU04, TU16 | implementado |
| RF03 | Tratamento e acompanhamento | F4 | triagem, atribuição, follow-ups, soluções | Detalhe | TU09–TU14 | implementado |
| RF04 | Consulta e notificações | F2, F3 | `GET /api/chamados`, `/resumo`, notificações | Meus Chamados, Dashboard, Notificações | TU08, TU17 | implementado |
| RF05 | Classificação: categoria e severidade | F2 | `GET /api/categorias`, `POST /api/chamados` | Wizard, etapas 1 e 2 | TU01, TU03 | implementado |
| RF06 | Base de Conhecimento | F5 | `/api/base-conhecimento` | `/base-conhecimento` | TU15, `baseConhecimento.test` | implementado |

## Requisitos não funcionais

| Código | Assunto | Fase | Onde | Testes | Estado |
|---|---|---|---|---|---|
| RNF01 | Segurança: HTTPS e autenticação | F1, F7 | JWT HS256, cookie de refresh (rotação + revogação de família), limite de tentativas (Redis), Traefik (F7) | TU07, `test_autenticacao` (RNF01 limite → 429) | em_andamento |
| RNF02 | Resposta em até 2 s | F2 | índices (trigram/status/categoria/data), consulta única com contadores (`count FILTER`) | `@pytest.mark.performance` (10k) + medição ao vivo p95 ≈ 25–29 ms | implementado |
| RNF03 | Layout responsivo | F0.5, F2 | `AppShell` (sidebar/gaveta, breakpoints 390/768/1440), telas de chamados responsivas | Playwright em viewport de celular | implementado |

## Regras de negócio

| Código | Enunciado resumido | Fase | Onde é garantida | Testes | Estado |
|---|---|---|---|---|---|
| RN01 | Concluir exige solução registrada | F4 | `CicloVidaService.concluir` | TU11 (`test_ciclo_vida_f42`) | implementado |
| RN02 | FECHADO exige aprovação do solicitante | F4 | `CicloVidaService.responder_solucao` | TU12, TU13 (`test_ciclo_vida_f42`) | implementado |
| RN03 | ATRIBUIDO exige técnico responsável | F0.3 (CHECK), F4 | CHECK `ck_chamados_rn03_tecnico`, `CicloVidaService.atribuir` | TU10 (`test_ciclo_vida`) | implementado |
| RN04 | Chamado ligado a categoria ativa e solicitante ativo | F2 | `ChamadoService.abrir` + FKs | TU01, TU02 (`test_chamados`) | implementado |
| RN05 | Só solução aprovada vai para a base | F5 | `BaseConhecimentoService.publicar` | TU15 (`test_base_conhecimento`) | implementado |
| RN06 | Só autenticado; CLIENTE vê só os seus | F1, F2 | `usuario_atual` + `exigir_perfil` + escopo no repositório | TU07 (401/403 em `test_autenticacao`/`test_usuarios`; 404 fora do escopo em `test_chamados_consulta`) | implementado |
| RN07 | E-mail único | F0.3 (UNIQUE), F1 | `UsuarioService.cadastrar` + `uq_usuarios_email` | TU05 (`test_usuarios`) | implementado |

## Casos de uso, jornada e fluxos

| Código | Assunto | Fase | Estado |
|---|---|---|---|
| UC01 | Cadastrar usuários | F1 | implementado |
| UC02 | Registrar e classificar chamado | F2 | implementado |
| UC03 | Acompanhar chamado | F2, F4 | implementado |
| UC04 | Consultar Base de Conhecimento | F5 | implementado |
| UJ01 | Abrir chamado e acompanhar | F2, F4 | implementado (fluxo NOVO→FECHADO; E2E Playwright na F7) |
| FA01 | Autoatendimento pela base | F5 | pendente |
| FA02 | Esqueci minha senha | F7 | implementado |
| FE01 | Credenciais inválidas / campos incompletos | F1 | implementado |
| FE02 | Campos obrigatórios no wizard | F2 | implementado |
| FE03 | Cancelar / Voltar no wizard | F2 | implementado |

## Fundação (Documento 02)

| Item do DoD | Recorte | Teste | Estado |
|---|---|---|---|
| Banco no ar via `docker compose up` | F0.1 | healthcheck `pg_isready` (`make up` espera `healthy`) | implementado |
| API no ar com `/api/health` e `/api/health/db` | F0.2 | `test_conexao.py` (health, X-Request-ID, formato de erro) | implementado |
| Formato único de erro e `X-Request-ID` | F0.2 | `test_conexao.py` | implementado |
| Build do backend sem erros | F0.2 | `make build` | implementado |
| Esquema das 6 tabelas, ENUMs, índices e 7 categorias (seção 5.2) | F0.3 | migration `0001_esquema_inicial`; `test_conexao_banco` (`docs/der.md`) | implementado |
| Conexão validada por teste automatizado | F0.3 | `test_conexao_banco` | implementado |
| Migration cria 6 tabelas, FKs e ENUMs | F0.3 | `test_migrations_ida_e_volta` | implementado |
| CI verde (ruff, mypy, pytest com cobertura e PostgreSQL) | F0.4 | `.github/workflows/ci.yml` (job `backend`); cobertura `--cov=app` em `pyproject.toml` | implementado |
| Template de PR e fluxo de branches (seção 12.4) | F0.4 | `.github/pull_request_template.md`; notas de proteção no `README.md` | implementado |
| Build do front-end sem erros | F0.5 | `npm run build` (tsc -b + vite build); `make front-build` | implementado |
| Front-end base: identidade, AppShell, rotas vazias, serviço `web` (Nginx) | F0.5 | `frontend/` (tokens 8.2, `AppShell`, `router`, `Dockerfile`+`nginx.conf`); `basico.test.tsx` (Vitest) | implementado |

## Autenticação (F1)

| Item | Recorte | Endpoint / onde | Teste | Estado |
|---|---|---|---|---|
| Tabela `tokens_refresh` (seção 5.4) | F1.1 | migration `0002_autenticacao`; entidade `TokenRefresh` | `test_migrations_ida_e_volta` (0001↔0002) | implementado |
| Login com contrato da seção 7.3 e cookie de refresh | F1.1 | `POST /api/auth/login` | `test_autenticacao` (contrato + cookie) | implementado |
| Mensagem genérica no login (FE01) | F1.1 | `AuthService.login` | `test_autenticacao` (FE01, inativo genérico) | implementado |
| Refresh com rotação; reuso revoga a família | F1.1 | `POST /api/auth/refresh` | `test_autenticacao` (rotação, reuso derruba família) | implementado |
| Logout revoga o refresh e apaga o cookie | F1.1 | `POST /api/auth/logout` | `test_autenticacao` (logout revoga) | implementado |
| Usuário atual recarregado do banco; recusa inativo | F1.1 | `GET /api/auth/me`, `usuario_atual` | `test_autenticacao` (me, sem token → 401) | implementado |
| Troca de senha (atual + nova); revoga sessões | F1.1 | `PUT /api/auth/senha` | `test_autenticacao` (troca ok, atual errada) | implementado |
| TU06: senha 8..72 bytes; hash `$2b$`, nunca em claro | F1.1 | `core/seguranca` (bcrypt) | `test_autenticacao` (TU06 curta/>72, hash gravado) | implementado |
| TU07 (401/403): sem token → 401; `exigir_perfil` → 403 | F1.1 | `usuario_atual`, `exigir_perfil` | `test_autenticacao` (sem token, ADMIN nega CLIENTE) | implementado |
| RNF01: limite de 5 tentativas / 15 min por IP e e-mail → 429 | F1.1 | `core/rate_limit` (Redis) | `test_autenticacao` (limite → 429) | implementado |
| Cadastro de usuário (ADMIN); RN07/TU05 e TU06 | F1.2 | `POST /api/usuarios`, `UsuarioService.cadastrar` | `test_usuarios` (201, TU05 duplicado/caixa, TU06 curta/hash) | implementado |
| Lista paginada com filtros `q`/`perfil`/`ativo` e detalhe | F1.2 | `GET /api/usuarios`, `GET /api/usuarios/{id}` | `test_usuarios` (filtros, page_size, detalhe/404) | implementado |
| TU07 nas rotas de usuários: sem token → 401; CLIENTE → 403 | F1.2 | router `/api/usuarios` com `exigir_perfil(ADMIN)` | `test_usuarios` (401, 403) | implementado |
| Config pública da tela de login | F1.2 | `GET /api/config/publica` (público) | `test_usuarios` (contrato público) | implementado |
| `make criar-admin` idempotente a partir do `.env` | F1.2 | `app/cli.py` (`criar-admin`) | `test_usuarios` (cria e não duplica) | implementado |
| Telas de Login, Perfil e `/admin/usuarios`; rotas por perfil | F1.3 | `pages/LoginPage`, `PerfilPage`, `AdminUsuariosPage`, `RequirePerfil`, `api/client` (retry 401) | `login.test.tsx`, `adminUsuarios.test.tsx` (MSW) | implementado |
| Sessão persiste writes (commit por requisição) — AJ-001 | F1.3 | `app/core/database.obter_sessao` | `test_sessao.py` (commit/rollback) | implementado |

## Abertura e consulta de chamados (F2)

| Item | Recorte | Endpoint / onde | Teste | Estado |
|---|---|---|---|---|
| Categorias ativas ordenadas (RF05) | F2.1 | `GET /api/categorias`, `CategoriaRepository.listar_ativas` | `test_chamados` (7 ordenadas, exige auth) | implementado |
| Abertura com RN04 (categoria ativa + solicitante ativo do token) | F2.1 | `POST /api/chamados`, `ChamadoService.abrir` | `test_chamados` (TU01 409, TU02 não cria) | implementado |
| TU03: NOVO + protocolo gerado + severidade + `status_grupo` | F2.1 | `POST /api/chamados`, coluna gerada `protocolo` | `test_chamados` (TU03, padrão BAIXA) | implementado |
| TU04: título/descrição 1..150/1..500 após strip → 422 | F2.1 | `ChamadoCriar` (Pydantic) | `test_chamados` (vazios e > 500) | implementado |
| Lista com busca/filtros/contadores/paginação; escopo (RN06) | F2.2 | `GET /api/chamados`, `ChamadoRepository.listar/contadores` | `test_chamados_consulta` (TU07 404, TU08 busca/filtros/contadores/paginação) | implementado |
| Resumo (indicadores) e detalhe por id no escopo | F2.2 | `GET /api/chamados/resumo`, `GET /api/chamados/{id}` | `test_chamados_consulta` (resumo, detalhe/404) | implementado |
| Seeds de dev (~60 chamados) e de performance (10k); RNF02 | F2.3 | `app/seeds.py`, `make seed`/`seed-performance` | `test_seeds` (quantidades, idempotência, `performance` ≤ 2 s) | implementado |
| Telas: Dashboard, Novo Chamado (3 etapas), Meus Chamados, Detalhe | F2.4 | `pages/DashboardPage`, `NovoChamadoPage`, `ChamadosPage`, `ChamadoDetalhePage`, `api/chamados` | `novoChamado.test.tsx`, `chamadosLista.test.tsx` (MSW) | implementado |

## Anexos e notificações (F3)

| Item | Recorte | Endpoint / onde | Teste | Estado |
|---|---|---|---|---|
| Migration 0003 (`anexos`, `notificacoes`) com CHECKs e índice parcial | F3.1 | `0003_anexos_notificacoes`; entidades `Anexo`/`Notificacao` | ida e volta das migrations | implementado |
| `StorageService` (MinIO/boto3); buckets no startup | F3.1 | `core/storage.py`; lifespan em `main` | `test_anexos` (storage em memória) | implementado |
| TU16: upload (PNG/JPG/PDF por magic bytes), lista e download no escopo | F3.1 | `POST`/`GET /api/chamados/{id}/anexos`, `GET /api/anexos/{id}/download`, `AnexoService` | `test_anexos` (ok, 415, 413, limite 5, escopo 404) | implementado |
| B9 (≤5 por chamado, ≤10 MB) e B10 (PNG/JPEG/PDF) | F3.1 | `AnexoService.anexar` | `test_anexos` | implementado |
| Notificações: eventos, lista/contagem, marcar lidas (TU17) | F3.2 | `EventoService`, `GET /api/notificacoes` e `/contagem`, `POST /{id}/lida` e `/lidas` | `test_notificacoes` (criado/urgente, escopo, marcar, 404, 401) | implementado |
| Zona de upload (wizard/detalhe) e tela de Notificações + contador no menu (30s) | F3.3 | `ZonaUpload`, `NovoChamadoPage`, `ChamadoDetalhePage`, `NotificacoesPage`, `MenuLateral`, `api/anexos`, `api/notificacoes` | `zonaUpload.test.tsx`, `notificacoes.test.tsx` (MSW) | implementado |

## Ciclo de vida (F4)

| Item | Recorte | Endpoint / onde | Teste | Estado |
|---|---|---|---|---|
| Migration 0004 (`historico_chamado`, datas) + backfill NOVO | F4.1 | `0004_ciclo_de_vida`; entidade `HistoricoChamado` | ida e volta das migrations | implementado |
| TU09 — Triagem NOVO→PENDENTE (ANALISTA/ADMIN; ajusta categoria/severidade) | F4.1 | `POST /api/chamados/{id}/triagem`, `CicloVidaService.triar` | `test_ciclo_vida` (PENDENTE, severidade, CLIENTE 403, só de NOVO 409) | implementado |
| TU10 — Atribuição →ATRIBUIDO com RN03 | F4.1 | `POST /api/chamados/{id}/atribuicao`, `CicloVidaService.atribuir` | `test_ciclo_vida` (admin→analista; RN03 cliente/inativo 409; analista só a si) | implementado |
| Histórico (linha do tempo) e técnicos para atribuição | F4.1 | `GET /api/chamados/{id}/historico`, `GET /api/usuarios/tecnicos` | `test_ciclo_vida` (histórico; /tecnicos 403/200) | implementado |
| Solução (RN01), aprovação/reprovação (RN02), follow-ups, `PATCH /api/usuarios` | F4.2 | `POST /{id}/solucoes`, `POST /api/solucoes/{id}/resposta`, `GET`/`POST /{id}/followups`, `PATCH /api/usuarios/{id}` | `test_ciclo_vida_f42` (TU11–TU14, PATCH) | implementado |
| Front: linha do tempo, ações por perfil, cartão da solução, fila, /admin editar/ativar | F4.3 | `ChamadoDetalhePage`, `ChamadosPage`, `AdminUsuariosPage`, `api/chamados`, `api/usuarios` | `chamadoDetalhe.test.tsx`, `adminUsuarios.test.tsx` (MSW) | implementado |

## Base de Conhecimento (F5)

| Item | Recorte | Endpoint / onde | Teste | Estado |
|---|---|---|---|---|
| Migration 0005 (busca full-text `pt_br_unaccent`, coluna gerada + GIN) | F5.1 | `0005_busca_base_conhecimento` | ida e volta das migrations | implementado |
| TU15 / RN05: publicar só de solução aprovada; não duplica | F5.1 | `POST /api/base-conhecimento`, `BaseConhecimentoService.publicar` | `test_base_conhecimento` (aprovada, 409 duplicado/não aprovada) | implementado |
| Busca full-text (sem acento) + filtro por categoria; leitura autenticada | F5.1 | `GET /api/base-conhecimento`, `BaseConhecimentoRepository.listar` | `test_base_conhecimento` (q=configuracao, filtro) | implementado |
| Escrita só ANALISTA/ADMIN; editar artigo | F5.1 | `router_escrita`, `PATCH /{id}` | `test_base_conhecimento` (403, editar) | implementado |
| Tela em acordeão (busca `q`, filtro por categoria) | F5.2 | `BaseConhecimentoPage`, `api/baseConhecimento` | `baseConhecimento.test` (acordeão, busca, filtro) | implementado |
| "Abrir chamado" pelo artigo (prefill da categoria/título no wizard) | F5.2 | `NovoChamadoPage` (query `?categoria=&titulo=`) | `baseConhecimento.test` (href do link) | implementado |
| Publicar a partir de chamado com solução aprovada (ANALISTA/ADMIN) | F5.2 | `ChamadoDetalhePage` → `POST /api/base-conhecimento` | TU15 (backend) | implementado |
| Editar artigo (ANALISTA/ADMIN) | F5.2 | `BaseConhecimentoPage` → `PATCH /{id}` | `baseConhecimento.test` (CLIENTE não vê; ANALISTA edita) | implementado |

## Canais externos (F6)

| Item | Recorte | Endpoint / onde | Teste | Estado |
|---|---|---|---|---|
| Migration 0006 (ENUMs canais, colunas WhatsApp/e-mail, `canal_origem`, tabela `eventos_outbox`) | F6.1 | `0006_canais_externos` | ida e volta das migrations | implementado |
| Outbox transacional: `EventoService` grava `eventos_outbox` na mesma transação (matriz 9.6) | F6.1 | `EventoService`, `OutboxRepository.enfileirar` | `test_canais_externos` (TU17) | implementado |
| Preferências por canal: e-mail respeita `notificar_email`; WhatsApp exige vínculo + opt-in | F6.1 | `EventoService._enfileirar_email/_whatsapp` | `test_canais_externos` (sem WA; e-mail off) | implementado |
| Textos das mensagens (LGPD: protocolo/título/status/link; solução ≤ 300) | F6.1 | `app/integrations/mensagens.py` | `test_canais_externos` (indireto via payload) | implementado |
| Despacho do outbox (worker → n8n), `/admin/outbox` e reenvio | F6.2 | `worker.despachar_lote`, `DespachanteN8N`, `GET/POST /api/admin/outbox` | `test_outbox_despacho`, `test_outbox_contrato` | implementado |
| Vínculo do WhatsApp, preferências e tela `/perfil` | F6.3 | `PerfilService`, `POST /api/perfil/whatsapp/vinculo`, `GET/DELETE /api/perfil/whatsapp`, `PATCH /api/perfil/preferencias`, `PerfilPage` | `test_perfil`, `perfilWhatsapp.test` | implementado |
| Bot (núcleo): endpoint com chave, dedup, identificação, VINCULAR, menu, meus chamados, status (RN06), opt-out | F6.4 | `BotService`, `POST /api/integracoes/whatsapp/mensagens`, `app/integrations/whatsapp/*` | `test_bot_whatsapp` | implementado |
| Bot: fluxo guiado de abertura (`canal_origem=WHATSAPP`), aprovação da solução (RN02), sessão e `/admin/integracoes` | F6.4b | `BotService`, `POST /api/integracoes/whatsapp/sessao`, `GET /api/admin/integracoes`, `AdminIntegracoesPage` | `test_bot_whatsapp`, `adminIntegracoes.test` | implementado |
| Infra n8n + WAHA (compose), workflows e READMEs | F6.5 | `docker-compose.yml` (n8n/waha), `integrations/n8n/*`, `integrations/waha/*` | `docker compose config`; saúde ao vivo (n8n `/healthz`, waha `/ping`) | implementado |

## Complementos e produção (F7)

| Item | Recorte | Endpoint / onde | Teste | Estado |
|---|---|---|---|---|
| FA02 — redefinição de senha por e-mail (migration 0007, token hash/uso único) | F7.1 | `POST /api/auth/esqueci-senha`, `POST /api/auth/redefinir-senha`, `AuthService.solicitar_redefinicao/redefinir`, `EsqueciSenhaPage`, `RedefinirSenhaPage` | `test_redefinicao_senha`, `redefinicaoSenha.test` | implementado |
| Resposta genérica no esqueci-senha (não revela a conta) | F7.1 | `AuthService.solicitar_redefinicao` | `test_redefinicao_senha` (silencioso) | implementado |
| SLA do mês (sla_politicas, prazo_sla, `GET /api/sla/mes`) | F7.2 | `0008_sla`, `SlaRepository`, `SlaService`, `GET /api/sla/mes`, cartão no `DashboardPage` | `test_sla`, `dashboardSla.test` | implementado |
| Login com Google Workspace (UJ01) | F7.3 | — | — | pendente |
| Produção (compose prod, Traefik, HTTPS) | F7.4 | — | — | pendente |
