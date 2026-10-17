# Rastreabilidade

Liga cada código dos Documentos 01 a 03 (e do prompt) ao que o implementa e ao que o testa. Uma
linha só muda para `implementado` quando o código e o teste existem.

Estados: `pendente` · `em_andamento` · `implementado`.

## Requisitos funcionais

| Código | Assunto | Fase | Endpoints | Telas | Testes | Estado |
|---|---|---|---|---|---|---|
| RF01 | Cadastro de usuários | F1 | `POST /api/usuarios` | `/admin/usuarios` | TU05, TU06 | pendente |
| RF02 | Registro de chamado (com anexos) | F2, F3 | `POST /api/chamados`, anexos | Novo Chamado | TU01–TU04, TU16 | pendente |
| RF03 | Tratamento e acompanhamento | F4 | triagem, atribuição, follow-ups, soluções | Detalhe | TU09–TU14 | pendente |
| RF04 | Consulta e notificações | F2, F3 | `GET /api/chamados`, `/resumo`, notificações | Meus Chamados, Dashboard, Notificações | TU08, TU17 | pendente |
| RF05 | Classificação: categoria e severidade | F2 | `GET /api/categorias`, `POST /api/chamados` | Wizard, etapas 1 e 2 | TU01, TU03 | pendente |
| RF06 | Base de Conhecimento | F5 | `/api/base-conhecimento` | `/base-conhecimento` | TU15 | pendente |

## Requisitos não funcionais

| Código | Assunto | Fase | Onde | Testes | Estado |
|---|---|---|---|---|---|
| RNF01 | Segurança: HTTPS e autenticação | F1, F7 | JWT, cookie de refresh, Traefik | TU07 | pendente |
| RNF02 | Resposta em até 2 s | F2 | índices, consulta única com contadores | `@pytest.mark.performance` | pendente |
| RNF03 | Layout responsivo | F0.5, F2 | `AppShell`, telas | Playwright em viewport de celular | pendente |

## Regras de negócio

| Código | Enunciado resumido | Fase | Onde é garantida | Testes | Estado |
|---|---|---|---|---|---|
| RN01 | Concluir exige solução registrada | F4 | `CicloVidaService.concluir` | TU11 | pendente |
| RN02 | FECHADO exige aprovação do solicitante | F4 | `CicloVidaService.responder_solucao` | TU12, TU13 | pendente |
| RN03 | ATRIBUIDO exige técnico responsável | F0.3 (CHECK), F4 | CHECK `ck_chamados_rn03_tecnico`, `CicloVidaService.atribuir` | TU10 | pendente |
| RN04 | Chamado ligado a categoria ativa e solicitante ativo | F2 | `ChamadoService.abrir` + FKs | TU01, TU02 | pendente |
| RN05 | Só solução aprovada vai para a base | F5 | `BaseConhecimentoService.publicar` | TU15 | pendente |
| RN06 | Só autenticado; CLIENTE vê só os seus | F1, F2 | `usuario_atual` + escopo no repositório | TU07 | pendente |
| RN07 | E-mail único | F0.3 (UNIQUE), F1 | `UsuarioService.cadastrar` + `uq_usuarios_email` | TU05 | pendente |

## Casos de uso, jornada e fluxos

| Código | Assunto | Fase | Estado |
|---|---|---|---|
| UC01 | Cadastrar usuários | F1 | pendente |
| UC02 | Registrar e classificar chamado | F2 | pendente |
| UC03 | Acompanhar chamado | F2 (parcial), F4 | pendente |
| UC04 | Consultar Base de Conhecimento | F5 | pendente |
| UJ01 | Abrir chamado e acompanhar | F2, F4 (E2E) | pendente |
| FA01 | Autoatendimento pela base | F5 | pendente |
| FA02 | Esqueci minha senha | F7 | pendente |
| FE01 | Credenciais inválidas / campos incompletos | F1 | pendente |
| FE02 | Campos obrigatórios no wizard | F2 | pendente |
| FE03 | Cancelar / Voltar no wizard | F2 | pendente |

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
| Build do front-end sem erros | F0.5 | `make build` | pendente |
