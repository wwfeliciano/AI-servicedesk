# Status de desenvolvimento

Andamento do projeto, recorte a recorte. Mais recente primeiro. O plano está em
[ROADMAP.md](ROADMAP.md).

## Andamento geral (estimativa)

**≈ 99% do sistema concluído** (18/10/2026). Estimativa por etapa, ponderada pelo esforço relativo
(F4 e F6 são as mais pesadas); cada etapa conta backend + front:

| Etapa | Peso | Concluído | Contribuição |
|---|---|---|---|
| E0 — Organização | 3% | 100% | 3% |
| F0 — Fundação (infra, API, banco, CI, front base) | 15% | 100% | 15% |
| F1 — Autenticação e cadastro | 14% | 100% | 14% |
| F2 — Abertura e consulta de chamados | 20% | 100% | 20% |
| F3 — Anexos e notificações | 12% | 100% | 12% |
| F4 — Ciclo de vida do chamado | 16% | 100% | 16% |
| F5 — Base de Conhecimento | 9% | 100% (backend + front) | 9% |
| F6 — Canais externos (e-mail/WhatsApp) | 7% | 100% | 7% |
| F7 — Complementos e produção | 4% | ~65% (esqueci a senha + SLA; falta Google e produção) | 2.5% |
| **Total** | **100%** | | **≈ 99%** |

O que já funciona ponta a ponta: login/sessão, cadastro e gestão de usuários (ADMIN), abertura de
chamado em 3 etapas, Dashboard, lista com busca/filtros/paginação e detalhe — tudo na stack real,
com o RNF02 medido. Falta: anexos, notificações, ciclo de vida (triagem/atribuição/solução/
aprovação), Base de Conhecimento, canais externos e os itens de produção (HTTPS/SLA/Google/esqueci
a senha). A estimativa é de esforço, não de linhas; os recortes seguintes incluem regras de negócio
mais densas (F4) e integrações (F6).

> **F8 — Assistente de IA (Mentory AI, RAG):** fase **nova**, batizada em 18/10/2026, é a **visão
> final do produto** (ADR 2026-10-17). Fica **fora do peso de 100% do core de chamados** (F0–F7):
> o percentual acima mede a entrega do núcleo. O plano técnico está na **seção 16** do prompt e os
> recortes F8.1–F8.6 no [ROADMAP](ROADMAP.md); depende de chave de provedor (B23–B28 em
> `DECISOES_PENDENTES.md`). Arquitetura espelhada, em Python, do plugin `aiservicedesk`
> (`/home/ubuntu/ai-assistant`): provider abstraction, fallback de modelo e de provedor, orçamento
> de tempo, degradação e RAG sobre a Base de Conhecimento.

## Situação atual (17/10/2026)

- **Etapa vigente:** F7 — Complementos e produção. Último recorte: **F7.2 — SLA do mês**
  (concluído, 18/10/2026). Próximo: **F7.3** (login com Google Workspace, opcional).
- **F0, F1, F2, F3, F4, F5 e F6 concluídas:** fundação, autenticação/cadastro, abertura/consulta,
  anexos/notificações, ciclo de vida, Base de Conhecimento e canais externos (e-mail/WhatsApp).
- **No ar:** `db`, `redis`, `s3` (MinIO), `mailpit`, `api`, `worker` e `web`. Banco no esquema
  `0003` (tabelas `anexos` e `notificacoes`). Front em `http://127.0.0.1:8180` (Nginx, faz proxy de
  `/api`); API em `http://127.0.0.1:8100`. Imagens `migrate`/`api`/`worker`/`web` reconstruídas com
  a F3.1; o serviço `api` recebeu as variáveis S3 e cria os buckets no startup.
- **Repositório:** Git local na branch `develop`, sem remoto. CI em `.github/workflows/ci.yml`
  (GitHub Actions) pronto para rodar quando houver remoto.

## Pendências

- Definir o remoto do GitHub (repositório público, GitHub Pro; sem credenciais no código). Decisão
  do usuário; push só com autorização a cada vez.
- Imagens `api` e `web` já reconstruídas e no ar (F1 + F1.3); `make criar-admin` executado (admin
  criado). Os testes continuam rodando no host (uv/npm) e passam.
- `frontend/` deixou de ser resíduo: foi **refeito e validado** na F0.5 (identidade do esboço).
  Resta o `.kiro/` (settings locais do editor) — ver [DECISOES_PENDENTES.md](DECISOES_PENDENTES.md).

## Decisões aprovadas, ainda não implementadas

Vão para [DECISOES.md](DECISOES.md) quando o código existir.

- **Backend antes do front-end** em cada etapa (pedido do usuário, 16/10/2026). Na F0, o front-end
  base é o último recorte (F0.5).
- **Etapas quebradas em recortes** (F0.1, F0.2...), no formato do GRH, com commit e relatório por
  recorte.
- **Identidade visual herdada do esboço (ex-HelpFlow)** — ADR 2026-10-17 em `DECISOES.md`: marca
  teal (Brand 600 `#066873`), IBM Plex Sans, sidebar branca, tema claro+escuro. Aprovada pelo
  usuário (17/10/2026); a implementação entra na F0.5 (refaz o `frontend/` residual). Protótipo de
  referência: `docs/design/mentory/index.html`. O **assistente de IA/RAG** é visão de produto e
  fica "em breve" — núcleo de chamados primeiro.

---

## F7.2 — SLA do mês (18/10/2026)

- **Migration 0008 (`0008_sla`):** tabela `sla_politicas` (`severidade` PK, `prazo_horas` > 0),
  **seed** com as metas da decisão B20 — CRITICO 4 h · ALTA 8 h · MEDIA 24 h · BAIXA 72 h (horas
  corridas); coluna `chamados.prazo_sla` (prazo-alvo).
- **Prazo na abertura:** `ChamadoService.abrir` grava `prazo_sla = data_criacao + prazo_horas` da
  severidade (via `SlaRepository`). Chamados anteriores à F7.2 ficam sem prazo (contam no total do
  SLA, mas não como "no prazo").
- **SLA do mês:** `SlaRepository.sla_do_mes` conta os chamados **concluídos no mês** (por
  `data_conclusao`) e, entre eles, os que respeitaram o prazo (`data_conclusao <= prazo_sla`);
  devolve `total`, `no_prazo` e `percentual`. `GET /api/sla/mes` (autenticado).
- **Front:** `api/sla.ts` e o cartão **"SLA do mês"** no Dashboard (percentual grande, barra de
  progresso e "N de M concluídos no prazo"; estados de carregamento, erro e vazio).
- **Testes:** backend `tests/test_sla.py` (3): a abertura grava o prazo (8 h para ALTA); o SLA do
  mês dá 50% com um no prazo e um fora; exige autenticação (401). Front `dashboardSla.test.tsx` (2):
  mostra 75% e o estado vazio.
- **Validação:** `make lint` ok; `make test` **148 passaram**; front typecheck/lint ok, **36
  testes**, build ok; migration 0008 aplicada no dev; imagens `migrate`/`api`/`web` reconstruídas.
  **Ao vivo via `127.0.0.1:8180`**: `sla_politicas` seeada (4/8/24/72); um chamado ALTA nasceu com
  `prazo_sla` a 8 h; `GET /api/sla/mes` respondeu `{total, no_prazo, percentual}`.

## Pendências e riscos

- Faltam os recortes F7.3 (login com Google, opcional) e F7.4 (produção). O horário comercial no SLA
  fica fora do escopo (B20).

---

## F7.1 — Redefinição de senha por e-mail (18/10/2026)

- **Migration 0007 (`0007_redefinicao_senha`):** tabela `tokens_redefinicao_senha` (token como
  **hash SHA-256**, `expira_em`, `usado_em`, índice único no hash). As tabelas de SLA ficaram para a
  F7.2 (migration 0008), para manter cada recorte isolado.
- **`AuthService`:** `solicitar_redefinicao(email)` é **silencioso** (só gera para usuário ativo;
  token opaco de 256 bits, guardado como hash, expira em **30 min**; enfileira o e-mail) e
  `redefinir(token, senha_nova)` valida (não usado / não expirado → `TOKEN_INVALIDO` 400), troca a
  senha, **marca o token como usado** (uso único) e **revoga todas as sessões**.
- **Evento `SENHA_REDEFINICAO`:** o `EventoService` enfileira o e-mail no outbox **ignorando
  `notificar_email`** (exceção da matriz 9.6 — é um e-mail transacional de segurança), com o link
  `/redefinir-senha?token=...`.
- **Endpoints públicos:** `POST /api/auth/esqueci-senha` (resposta **genérica**, não revela se o
  e-mail existe — FA02) e `POST /api/auth/redefinir-senha`.
- **Front:** `/esqueci-senha` (formulário + confirmação genérica) e `/redefinir-senha?token=...`
  (nova senha + confirmação; trata link ausente); o Login ganhou o link **"Esqueci minha senha"**
  funcional.
- **Testes:** backend `tests/test_redefinicao_senha.py` (4): esqueci silencioso (e-mail inexistente
  não gera outbox), fluxo completo (token do outbox → redefine → login com a nova / 401 com a antiga
  → reuso 400), token inválido 400, senha fraca 422. Front `redefinicaoSenha.test.tsx` (3).
- **Validação:** `make lint` ok; `make test` **145 passaram**; front typecheck/lint ok, **34
  testes**, build ok; migration 0007 aplicada no dev; imagens `api`/`web` reconstruídas. **Ao vivo
  via `127.0.0.1:8180`**: `esqueci-senha` devolveu a resposta genérica e gravou um
  `SENHA_REDEFINICAO`/EMAIL no outbox com token de 64 hex; `redefinir-senha` com o token funcionou;
  login seguiu OK e o **reuso do token** deu **400**.

## Pendências e riscos

- Em dev o e-mail fica no outbox (`OUTBOX_HABILITADO=false`); com a integração ligada ele cai no
  Mailpit. Faltam os recortes F7.2 (SLA), F7.3 (Google) e F7.4 (produção).

---

## F6.5 — Infra n8n + WAHA (18/10/2026) — fecha a F6

- **Serviços no compose base:** `n8n` (`n8nio/n8n:2.34.4`, Community; usa o Postgres do projeto —
  banco/usuário criados pelo `infra/postgres/init/01-n8n.sh` —, SMTP apontando para o Mailpit em
  dev, `N8N_WEBHOOK_TOKEN`/`INTEGRACAO_API_KEY`, volume `n8n_data`) e `waha`
  (`devlikeapro/waha:arm-2026.4.3`, pública/Apache-2.0; `WHATSAPP_API_KEY`, dashboard/Swagger,
  engine e webhook para o n8n, volume `waha_data`). Ambos na rede interna, `restart: unless-stopped`,
  limites de 1 CPU / 1 GB e **sem portas publicadas na internet** (o Traefik exige autorização).
- **Dev:** `docker-compose.override.yml` publica `127.0.0.1:${PORTA_N8N:-5678}` e
  `127.0.0.1:${PORTA_WAHA:-3000}`; `.env.example` ganhou `PORTA_N8N`/`PORTA_WAHA` (as demais vars
  n8n/WAHA/SMTP já existiam).
- **Workflows (`integrations/n8n/workflows/`, sem credenciais):** `notificacoes.json` (saída:
  webhook → valida `X-Mentory-Token` → remove `id_evento` repetido → roteia `WHATSAPP`/`EMAIL`) e
  `waha-eventos.json` (entrada: webhook → filtra `fromMe`/grupos → `POST
  /api/integracoes/whatsapp/mensagens` → responde pelo WAHA). READMEs em `integrations/n8n/` e
  `integrations/waha/` (variáveis, importação, sessão/QR, número dedicado, licenças e segurança).
- **Validação:** `docker compose config` ok; os dois JSON são válidos; **ao vivo** (só local, sem
  publicar): `n8n` **healthy** (`/healthz` 200, banco `n8n` criado e migrations do n8n rodaram) e
  `waha` **healthy** (`/ping` 200). O healthcheck do WAHA usa `/ping` (a raiz exige a API key → 401).

## Pendências e riscos

- A publicação de n8n/WAHA pelo Traefik e a sessão real do WhatsApp (leitura do QR com o número
  dedicado) dependem de autorização e de credenciais de produção (SMTP inclusive), ainda não
  fornecidas. Em dev, o e-mail cai no Mailpit.

---

## F6.4b — Bot: fluxo guiado, aprovação e `/admin/integracoes` (18/10/2026)

- **Fluxo guiado de abertura (`1`)**: máquina de estados na conversa do Redis —
  categoria (lista numerada) → prioridade (1–4) → título (≤150) → descrição (≤500) → confirmação
  (`1` abre, `2` cancela); `cancelar` sai a qualquer momento. O chamado é criado pelo mesmo
  `ChamadoService.abrir` (RN04), agora com **`canal_origem = WHATSAPP`** (coluna da migration 0006).
- **Aprovação/reprovação da solução pelo WhatsApp (RN02)**: `APROVAR TK-0051` /
  `REPROVAR TK-0051 <motivo>` (o motivo é obrigatório na reprovação); e o atalho `1`/`2` quando a
  conversa está em `AGUARDANDO_APROVACAO` (armado quando o solicitante consulta um chamado CONCLUIDO
  seu). Aplica via `CicloVidaService.responder_solucao`, só para o solicitante.
- **Sessão do WAHA**: `POST /api/integracoes/whatsapp/sessao` (chave) guarda o último `status` no
  Redis (`wa:sessao`); `GET /api/admin/integracoes` (ADMIN) devolve esse status.
- **Tela `/admin/integracoes` (ADMIN)**: cartão com o **status da sessão do WhatsApp** (cor por
  estado, atualização a cada 15 s) e a **fila do outbox** (filtro por status com contadores, lista e
  botão **Reenviar** nos `FALHOU`). Item de menu "Integrações" e rota protegida por perfil.
- **Compose**: `ChamadoRepository.criar`/`ChamadoService.abrir` passaram a aceitar `canal_origem`.
- **Testes:** backend `tests/test_bot_whatsapp.py` subiu para **13** (fluxo guiado completo com
  `canal_origem=WHATSAPP`, cancelar, aprovar pelo `1`, reprovar por comando, sessão + admin). Front
  `adminIntegracoes.test.tsx` (2): mostra sessão e fila; reenfileira um `FALHOU`.
- **Validação:** `make lint` ok; `make test` **141 passaram**; front 31 testes, build ok; imagens
  `api`/`web` reconstruídas. **Ao vivo via `127.0.0.1:8180`** (simulando o n8n): `POST …/sessao`
  (`WORKING`) → `GET /api/admin/integracoes` devolve `WORKING`; e o fluxo guiado completo abriu o
  chamado **TK-10068 com `canal_origem = WHATSAPP`**. O vínculo de teste do admin foi desfeito.

## Pendências e riscos

- Falta só a **F6.5** (infra n8n + WAHA no compose, workflows exportados e o ligamento ponta a ponta
  — e-mail no Mailpit em dev). As credenciais de SMTP de produção ainda não foram fornecidas.

---

## F6.4 — Bot de atendimento do WhatsApp: núcleo (18/10/2026)

- **Endpoint `POST /api/integracoes/whatsapp/mensagens`** (seção 9.3): autenticado pela **chave**
  `X-Integracao-Chave` (≠ usuário logado; chave errada → 401); recebe `{message_id, chat_id, lid,
  numero, texto, tem_midia}` e devolve `{respostas: [{texto}]}`. **Deduplicação** por `SET NX` em
  `wa:msg:{message_id}` (a mesma mensagem não é processada de novo).
- **Identificação do usuário** por `whatsapp_chat_id` → `whatsapp_lid` → `whatsapp_numero`, só entre
  ativos (`UsuarioRepository.buscar_por_whatsapp`).
- **`BotService`** (regras no backend; o n8n é só transporte): normaliza o texto (sem acento/caixa)
  e roteia — `VINCULAR <código>` completa o vínculo consumindo o código do Redis
  (`VinculoWhatsApp.consumir`) e gravando `chat_id/lid/numero` + consentimento; número não vinculado
  recebe as instruções; `menu`/`oi`/`0` → menu; `9` → ajuda; `2` → meus chamados em aberto;
  `3`/`TK-0051` → status **do próprio** (RN06); `SAIR`/`PARAR` → opt-out (desvincula); mídia sem
  texto → aviso. O fluxo guiado de abertura (`1`) e a aprovação da solução são a F6.4b.
- **Textos em `app/integrations/whatsapp/mensagens.py`** (formatação do WhatsApp, LGPD) e estado da
  conversa em `app/integrations/whatsapp/estado.py` (`wa:conversa:{chat_id}`, TTL 30 min; base do
  fluxo guiado).
- **Compose:** os serviços `api` e `worker` passaram a receber `INTEGRACAO_API_KEY`,
  `OUTBOX_HABILITADO` e as URLs/token do n8n.
- **Testes (`tests/test_bot_whatsapp.py`, 8):** chave inválida (401), não-vinculado recebe
  instruções, dedup, `VINCULAR` completa o vínculo (código gerado pelo Perfil, mesmo Redis), código
  inválido, `2` lista os em aberto, status por protocolo (próprio), `SAIR` faz opt-out.
- **Validação:** `make lint` ok; `make test` **136 passaram**; imagem `api` reconstruída; **ao vivo
  via `127.0.0.1:8180`** (simulando o n8n): chave errada → 401; número novo → instruções; `VINCULAR
  <código>` (gerado no Perfil) → "WhatsApp vinculado"; `menu` depois → o menu. O vínculo de teste do
  admin foi desfeito ao final.

---

## F6.3 — Vínculo do WhatsApp no Perfil (17/10/2026)

- **Prova de posse + consentimento (seção 9.4):** `POST /api/perfil/whatsapp/vinculo` exige o
  consentimento (`422 CONSENTIMENTO_OBRIGATORIO` sem ele), gera um **código de 6 dígitos** e guarda
  no Redis o mapa `sha256(codigo) → id_usuario` com **TTL de 10 min** (chave `wa:vinculo:{hash}`,
  helper `core/vinculo_whatsapp.py`); devolve o código, o link `https://wa.me/<número>?text=VINCULAR
  %20<código>` e `expira_em_segundos`. O vínculo efetivo (gravar `whatsapp_chat_id`) é do bot, F6.4.
- **Status e opt-out:** `GET /api/perfil/whatsapp` (vinculado, número, opt-in, e-mail) e
  `DELETE /api/perfil/whatsapp` (apaga o vínculo e desliga o opt-in).
- **Preferências:** `PATCH /api/perfil/preferencias` (`notificar_email`, `whatsapp_opt_in`);
  `GET /api/auth/me` passou a expor `notificar_email`, `whatsapp_opt_in` e `whatsapp_vinculado`.
- **`PerfilService`** (não conhece HTTP): `gerar_vinculo`, `status`, `desvincular`,
  `atualizar_preferencias`; `UsuarioRepository` ganhou `atualizar_preferencias` e
  `desvincular_whatsapp`.
- **Front:** `api/perfil.ts` e a **seção WhatsApp** na `/perfil`: caixa de consentimento → "Vincular
  WhatsApp" → mostra o **código**, o **link wa.me** e um **QR code gerado no navegador**
  (`qrcode.react`, pinado em 4.2.0); enquanto aguarda, consulta o status a cada **3 s**
  (`refetchInterval`); estado "vinculado" com **Desvincular**; e as preferências de e-mail/WhatsApp.
- **Testes:** backend `tests/test_perfil.py` (6): consentimento obrigatório (422), código de 6
  dígitos + link + TTL 600, status padrão, preferências refletem no `/auth/me`, desvincular (opt-out)
  e exige autenticação (401). Front `perfilWhatsapp.test.tsx` (2): consentimento habilita o botão e
  gera código + link; estado vinculado permite desvincular.
- **Validação:** `make lint` ok; `make test` **128 passaram**; front typecheck/lint ok, **29 testes**,
  build ok; imagens `api`/`web` reconstruídas. **Ao vivo via `127.0.0.1:8180`**: sem consentimento →
  422; com consentimento → código `######` + link `wa.me/…?text=VINCULAR …` + TTL 600; a chave no
  Redis está como **sha256** (TTL ~590 s); `/auth/me` expõe as preferências; `DELETE` desvincula.

## Pendências e riscos

- O bot de atendimento (que consome `VINCULAR <código>` e completa o vínculo), as telas de
  `/admin/integracoes` e a infra n8n + WAHA são os recortes F6.4–F6.5. Em dev o e-mail cai no
  Mailpit; as credenciais de SMTP de produção ainda não foram fornecidas.

---

## F6.2 — Worker despacha o outbox ao n8n + `/admin/outbox` (17/10/2026)

- **`OutboxRepository` (despacho):** `reservar_lote` (o `UPDATE … FOR UPDATE SKIP LOCKED
  RETURNING` da seção 9.2: marca `PROCESSANDO` e `bloqueado_ate = now()+60s`, sem colidir com outro
  worker); `marcar_enviado` (→ ENVIADO + `enviado_em`); `registrar_falha` (conta a tentativa,
  reagenda com backoff 30 s → 1 h e, na 8ª, vira `FALHOU`); `listar`/`contar_por_status` e
  `reenfileirar` (reenvio manual).
- **Despachante (`app/integrations/despacho.py`):** `montar_contrato` monta `{id_evento, tipo,
  canal, destino, mensagem}` (seção 9.2) e o `DespachanteN8N` faz `POST` ao n8n com timeout 10 s e
  os headers `X-Mentory-Token`/`X-Evento-Id`; 2xx → sucesso, senão `ErroDespacho`.
- **Worker:** mantém o heartbeat (10 s) e, **só quando `OUTBOX_HABILITADO=true`**, a cada 2 s
  reserva um lote e despacha: cada evento vira ENVIADO ou tem a falha registrada (backoff/FALHOU),
  cada um no seu commit. Com a integração desligada, o laço só mantém o heartbeat.
- **Admin:** `GET /api/admin/outbox` (filtro por `status`, paginação e contadores por status) e
  `POST /api/admin/outbox/{id}/reenviar` — ambos **só ADMIN** (`OutboxService`).
- **Dependências:** `httpx` passou a ser dependência de **runtime** (o worker usa no despacho);
  antes era só de dev. Lock regenerado e imagens `api`/`worker` reconstruídas.
- **Testes (`tests/test_outbox_despacho.py` 9 + `tests/test_outbox_contrato.py` 4):** reserva marca
  PROCESSANDO e não repega dentro do bloqueio; `marcar_enviado`; backoff e `FALHOU` na 8ª; ciclo
  reserva→enviar/falhar (OK/erro); admin lista com contadores, 403 para CLIENTE, reenviar e 404.
  O contrato segue a seção 9.2 e o despachante só liga com `OUTBOX_HABILITADO` + URL.
- **Validação:** `make lint` ok; `make test` **122 passaram**; imagens reconstruídas; **ao vivo via
  `127.0.0.1:8180`**: `GET /api/admin/outbox` devolve os contadores; com `OUTBOX_HABILITADO=true` e
  o n8n indisponível, o worker tentou despachar e o evento foi para `PENDENTE` com `tentativas=1` e
  o erro de rede em `ultimo_erro` (backoff); `POST …/reenviar` voltou o evento a `PENDENTE`/`0`.

## Pendências e riscos

- O vínculo do WhatsApp, o bot, as telas de `/perfil` (WhatsApp) e `/admin/integracoes`, e a infra
  n8n + WAHA (com os workflows) são os recortes F6.3–F6.5. Em dev o e-mail cairá no Mailpit; as
  credenciais de SMTP de produção ainda não foram fornecidas.

---

## F6.1 — Canais externos: backend e outbox transacional (17/10/2026)

- **Migration 0006 (`0006_canais_externos`):** ENUMs `canal_notificacao` (WHATSAPP/EMAIL),
  `status_outbox` (PENDENTE/PROCESSANDO/ENVIADO/FALHOU) e `canal_origem` (PORTAL/WHATSAPP); colunas
  de WhatsApp e e-mail em `usuarios` (`whatsapp_chat_id`/`whatsapp_lid` únicos, `whatsapp_numero`,
  `whatsapp_opt_in` padrão false, `whatsapp_consentimento_em`, `notificar_email` padrão true);
  `canal_origem` em `chamados` (padrão PORTAL); tabela `eventos_outbox` (seção 9.2) com índice
  parcial da fila. Downgrade completo (inclui `DROP TYPE`).
- **Entidade `EventoOutbox`** e colunas novas em `Usuario`/`Chamado`; registradas no metadata.
- **`OutboxRepository.enfileirar`:** grava um evento `PENDENTE` na transação corrente (sem commit).
- **Textos em `app/integrations/mensagens.py`:** construtores `wa_*`/`email_*` que devolvem o
  `payload` de cada mensagem (WhatsApp `{texto}`; e-mail `{assunto, texto, html}`), com minimização
  de dados (LGPD): protocolo, título, status e link; a solução vai resumida a ≤ 300 caracteres.
- **`EventoService` (matriz 9.6):** além da notificação de portal, agora **enfileira o outbox** de
  e-mail e WhatsApp, **na mesma transação**, respeitando as preferências — e-mail só com
  `notificar_email`; WhatsApp só com `whatsapp_chat_id` + `whatsapp_opt_in`. Cobre
  `CHAMADO_CRIADO`, `CHAMADO_URGENTE`, `CHAMADO_ATRIBUIDO`, `FOLLOWUP_ADICIONADO`,
  `SOLUCAO_REGISTRADA` (com 1/2 no WhatsApp) e `SOLUCAO_REJEITADA`; a triagem (`STATUS_ALTERADO`)
  continua só portal.
- **Config:** `OUTBOX_HABILITADO` (padrão **false**), `N8N_WEBHOOK_NOTIFICACOES_URL`,
  `N8N_WEBHOOK_TOKEN` e `INTEGRACAO_API_KEY` (já no `.env.example`). Enquanto o worker não despacha
  (F6.2), os eventos ficam `PENDENTE`.
- **Testes (`tests/test_canais_externos.py`, 5 — TU17):** e-mail + WhatsApp quando vinculado; só
  e-mail sem vínculo; nenhum evento com `notificar_email=false` e sem WhatsApp; a triagem não gera
  outbox; abertura CRITICO alerta o técnico no outbox.
- **Validação:** `make lint` ok; `make test` **109 passaram** (migration 0006 aplicada no banco de
  teste via `alembic upgrade head`); 0006 aplicada no dev (rebuild `migrate`/`api`); **ao vivo via
  `127.0.0.1:8180`** abrir um chamado gravou uma linha `CHAMADO_CRIADO`/`EMAIL` `PENDENTE` no
  `eventos_outbox` e o chamado nasceu com `canal_origem = PORTAL`.

## Pendências e riscos

- O despacho do outbox (worker → n8n → WAHA/SMTP), o vínculo do WhatsApp, o bot e as telas de
  `/perfil` (WhatsApp) e `/admin/integracoes` são os recortes F6.2–F6.5. As credenciais de SMTP
  ainda não foram fornecidas; em dev o destino será o Mailpit.

---

## F5.2 — Front da Base de Conhecimento (17/10/2026) — fecha a F5

- **Módulo de API (`api/baseConhecimento.ts`):** `listarArtigos` (busca `q` + filtro `id_categoria`
  + paginação), `obterArtigo`, `publicarArtigo` e `editarArtigo`, tipados do schema regenerado.
- **Tela `BaseConhecimentoPage` (reescrita):** busca com debounce refletida na URL (`?q=`), chips de
  categoria (`?categoria=`), **lista em acordeão** (abre/fecha o conteúdo do artigo) e paginação.
  Cada artigo aberto traz **"Não resolveu? Abrir chamado"** (link para o wizard com a categoria e o
  título pré-preenchidos) e, para **ANALISTA/ADMIN**, **"Editar"** (modal → `PATCH`).
- **Prefill do wizard (`NovoChamadoPage`):** lê `?categoria=` e `?titulo=` e popula o rascunho uma
  vez, só quando ele ainda está vazio (não sobrescreve o que o usuário começou); o título vira
  "Dúvida: &lt;título do artigo&gt;".
- **"Publicar na base" no detalhe do chamado (`ChamadoDetalhePage`):** para ANALISTA/ADMIN, quando
  existe uma **solução aprovada**, aparece um cartão com a ação; o modal pré-preenche o título (do
  chamado) e o conteúdo (descrição da solução) e chama `POST /api/base-conhecimento` (RN05 validada
  no backend).
- **Ajuste de contrato:** o schema `CategoriaResumo` da base colidia no OpenAPI com o de chamados
  (nomes qualificados pelo módulo). Renomeado para **`ArtigoCategoria`** no controller; schema
  regenerado e o front atualizado.
- **Testes (`src/test/baseConhecimento.test.tsx`, 5, MSW):** lista + acordeão + prefill do "Abrir
  chamado"; busca repassa `q`; filtro repassa `id_categoria`; CLIENTE não vê "Editar";
  ANALISTA/ADMIN edita (`PATCH`).
- **Validação:**
  - `make front-lint`/`typecheck` ok; **27 testes** do front passam; `npm run build` ok (o `tsc -b`
    pegou a colisão de nome que o `--noEmit` não pegava); `make lint` ok e `make test` **104
    passaram** no backend.
  - web reconstruído; **ao vivo via `127.0.0.1:8180`** (proxy): o artigo da F5.1 aparece na lista;
    busca `q=solucao` (sem acento) acha 1; filtro `id_categoria=1` (TI) acha 1 e `=2` (RH) acha 0;
    a rota SPA `/base-conhecimento` serve HTML (200).

## F5.1 — Base de Conhecimento: backend e busca full-text (17/10/2026)

- **Migration 0005:** configuração de busca `pt_br_unaccent` (cópia de `portuguese`, mapeamento via
  `unaccent` + `portuguese_stem` → busca **sem acento**); coluna gerada `busca` (tsvector) em
  `base_conhecimento` (título peso A, conteúdo peso B) e índice **GIN**. Downgrade completo. A
  entidade ganhou a coluna `busca` (read-only, `Computed`).
- **Repositório:** `BaseConhecimentoRepository` com busca full-text
  (`busca @@ websearch_to_tsquery('pt_br_unaccent', :q)` ordenada por `ts_rank`), **filtro por
  categoria** derivada pelo join `base → solucoes → chamados → categorias`, listar/obter/criar e
  `existe_por_solucao`.
- **Service (RN05):** `BaseConhecimentoService.publicar` só aceita a partir de uma **solução
  APROVADA** (`409 SOLUCAO_NAO_APROVADA`) e **uma por solução** (`409 DUPLICADO`); `editar`
  (título/conteúdo), `buscar` e `obter`.
- **Endpoints:** leitura por qualquer autenticado — `GET /api/base-conhecimento` (`q`,
  `id_categoria`, paginação) e `GET /api/base-conhecimento/{id}`; escrita por ANALISTA/ADMIN —
  `POST` (publicar) e `PATCH /{id}` (editar), em router à parte com o guard de perfil.
- **Testes (`tests/test_base_conhecimento.py`, 6 — TU15):** leitura exige auth; publica de solução
  aprovada e não duplica (409); RN05 recusa solução não aprovada (409); escrita só ANALISTA/ADMIN
  (403); busca **sem acento** (`q=configuracao` acha "Configuração") + filtro por categoria; editar.
- **Validação:**
  - `make lint` ok; `make test` **104 passaram**, 3 deselected, cobertura 90,5%;
  - migration 0005 aplicada no dev (config `pt_br_unaccent` criada); **ao vivo via `127.0.0.1:8180`**:
    publicou um artigo a partir de uma solução aprovada (categoria TI derivada pelo join) e a busca
    `q=solucao` (sem acento) encontrou "Solução de conexão VPN".

## Pendências e riscos

- A tela da Base de Conhecimento (acordeão, busca, filtro), o "Abrir chamado" a partir do artigo e o
  "Publicar na base" a partir de um chamado com solução aprovada foram entregues na F5.2.

---

## F4.3 — Front do ciclo de vida (17/10/2026) — fecha a F4

- **Camada de API:** `api/chamados.ts` ganhou `triar`, `atribuir`, `concluir`, `responderSolucao`,
  `listarHistorico`, `listarSolucoes`, `listarFollowups`, `adicionarFollowup` e `listarTecnicos`;
  `api/usuarios.ts` ganhou `atualizarUsuario` (PATCH).
- **Detalhe do chamado (UC03):** reescrito com dados + descrição; **linha do tempo** (histórico) e
  **follow-ups** (lista + caixa de mensagem); **ações por perfil** para ANALISTA/ADMIN — Triar (se
  NOVO), Atribuir/Reatribuir (modal com select de técnicos), Registrar solução (modal) — exibidas
  conforme o status; **cartão da solução** para o solicitante quando CONCLUIDO (Aprovar e encerrar /
  Reprovar com motivo). Anexos (lista, download, upload). Chamado **FECHADO** some com as ações e a
  caixa de mensagem. As queries são invalidadas após cada ação.
- **Meus Chamados:** para ANALISTA/ADMIN o título vira "Chamados" e o card mostra o **solicitante**
  (a fila já vem do backend pelo escopo do perfil).
- **/admin/usuarios:** coluna "Ações" com **Editar** (modal nome/cargo/perfil, com erros de campo) e
  **Ativar/Desativar** (PATCH, exclusão lógica). O contador de notificações no menu já existia (F3.3).
- **Testes (Vitest + MSW, 3 novos):** `chamadoDetalhe.test` (solicitante vê o cartão da solução e
  aprova → chamada à API; técnico vê "Registrar solução" em ATRIBUIDO) e `adminUsuarios` (toggle de
  `ativo` via PATCH). MSW ganhou handlers de histórico/follow-ups/soluções/técnicos.
- **Correção:** um import duplicado de `useState` na `AdminUsuariosPage` passava no `tsc --noEmit`
  mas quebrava o `tsc -b` do build; removido.
- **Validação:**
  - Front: `typecheck`, `lint`, `test` (22) e `build` verdes;
  - **ao vivo via `127.0.0.1:8180`** (imagem `web` reconstruída): `/usuarios/tecnicos`, histórico e
    as rotas do SPA respondem; o fluxo de ciclo de vida já fora validado de ponta a ponta no backend
    (F4.1/F4.2). **DoD da F4 fechado** (TU09–TU14; fluxo NOVO→FECHADO com três perfis).

## Pendências e riscos

- Os filtros extras da fila (responsável, severidade) ficaram de fora do recorte mínimo; podem
  entrar como melhoria. A próxima etapa é a F5 (Base de Conhecimento).

---

## F4.2 — Ciclo de vida: solução, aprovação, follow-ups e PATCH usuário (17/10/2026)

- **Conclusão (RN01):** `POST /api/chamados/{id}/solucoes` — técnico responsável ou ADMIN registra
  a **solução** (obrigatória) e o chamado vai de ATRIBUIDO → CONCLUIDO; a solução nasce
  `PENDENTE_APROVACAO`, preenche `data_conclusao` e grava o histórico ("Solução registrada").
  Evento `SOLUCAO_REGISTRADA` ao solicitante.
- **Resposta do solicitante (RN02):** `POST /api/solucoes/{id}/resposta` — **só o solicitante**.
  Aprovar → FECHADO + `data_fechamento` + solução `APROVADO` (evento `SOLUCAO_APROVADA`). Reprovar
  (**motivo obrigatório**) → ATRIBUIDO + solução `REJEITADO` + o **motivo vira follow-up** (evento
  `SOLUCAO_REJEITADA`).
- **Follow-ups:** `GET`/`POST /api/chamados/{id}/followups` — participantes (solicitante, técnico
  responsável e ADMIN); um terceiro recebe `404`. Chamado **FECHADO bloqueia** novo follow-up
  (`409 TRANSICAO_INVALIDA`).
- **`PATCH /api/usuarios/{id}` (ADMIN):** nome, cargo, perfil e `ativo` (exclusão lógica). Salvaguarda:
  o ADMIN **não desativa nem rebaixa a si mesmo** (`422`).
- **Camadas:** `SolucaoRepository`, `FollowUpRepository`; `CicloVidaService.concluir`,
  `responder_solucao`/`responder_por_solucao`, `listar/adicionar_followup`, `solucoes`;
  `UsuarioService.atualizar`; `EventoService` ganhou os eventos de solução.
- **Testes (`tests/test_ciclo_vida_f42.py`, 14):** TU11 (conclui; exige descrição → 422; CLIENTE →
  403), TU12 (aprovar → FECHADO + `data_fechamento` + APROVADO), TU13 (reprovar → ATRIBUIDO +
  REJEITADO + motivo vira follow-up; exige motivo), só o solicitante responde (403), TU14 (follow-up
  por participantes; terceiro 404; FECHADO bloqueia 409), PATCH (desativa/reativa; admin não a si;
  exige ADMIN).
- **Validação:**
  - `make lint` ok; `make test` **98 passaram**, 3 deselected, cobertura 90,7% (~10 s);
  - **ao vivo via `127.0.0.1:8180`:** fluxo completo **NOVO → PENDENTE → ATRIBUIDO → CONCLUIDO →
    FECHADO** com o histórico registrando as 5 transições (DoD da F4: fluxo demonstrável).

## Pendências e riscos

- Backend do ciclo de vida completo. Falta a **F4.3** (front): linha do tempo e ações por perfil no
  detalhe, cartão da solução (aprovar/reprovar), fila de ANALISTA/ADMIN com filtros e
  `/admin/usuarios` editar/ativar.

---

## F4.1 — Ciclo de vida: triagem e atribuição (17/10/2026)

- **Migration 0004:** tabela `historico_chamado` (linha do tempo das transições;
  `status_anterior` nulo na criação, `id_autor` nulo = sistema) e colunas
  `chamados.data_conclusao`/`data_fechamento`. **Backfill** de um evento `NOVO` por chamado
  existente (10.063 no dev). Entidade `HistoricoChamado` registrada; downgrade completo.
- **Transições (seção 6.3):** `CicloVidaService`:
  - **Triagem** NOVO → PENDENTE (ANALISTA/ADMIN; pode ajustar categoria ativa e severidade;
    `TRANSICAO_INVALIDA` se não estiver em NOVO);
  - **Atribuição** NOVO/PENDENTE/ATRIBUIDO → ATRIBUIDO com **RN03** (o responsável precisa ser
    ANALISTA/ADMIN **ativo** → `RN03_TECNICO_INVALIDO`); ANALISTA só atribui a si, ADMIN a qualquer.
  - Cada transição grava `historico_chamado` e atualiza `data_atualizacao` na mesma transação.
- **Histórico na abertura:** `ChamadoService.abrir` passou a registrar o evento `NOVO` ("Chamado
  criado"), coerente com o backfill — a linha do tempo começa na criação.
- **Eventos (canal Portal):** `STATUS_ALTERADO` (ao solicitante na triagem/atribuição) e
  `CHAMADO_ATRIBUIDO` (ao técnico), via `EventoService`.
- **Endpoints:** `POST /api/chamados/{id}/triagem`, `POST /api/chamados/{id}/atribuicao`,
  `GET /api/chamados/{id}/historico` (respeita o escopo do perfil) e
  `GET /api/usuarios/tecnicos` (ANALISTA/ADMIN; router à parte, sem o guard de ADMIN, declarado
  antes de `/{id}`). Erros: `403` sem permissão, `404` inexistente/fora do escopo, `409` transição
  inválida / RN03 / categoria inativa.
- **Testes (`tests/test_ciclo_vida.py`, 9 — TU09/TU10):** triagem NOVO→PENDENTE e ajuste de
  severidade; CLIENTE não tria (403); triar fora de NOVO (409); ADMIN atribui a analista; RN03
  recusa técnico CLIENTE e técnico inativo (409); analista só a si (403/ok); `/tecnicos` (CLIENTE
  403, ANALISTA 200).
- **Validação:**
  - `make lint` ok; `make test` **87 passaram**, 3 deselected, cobertura 91,5% (~8 s);
  - migration 0004 aplicada no dev (backfill 10.063); **ao vivo via `127.0.0.1:8180`:** abrir →
    histórico `NOVO`; triagem → PENDENTE; atribuição → ATRIBUIDO; `/historico` e `/tecnicos` ok.

## Pendências e riscos

- Solução (CONCLUIDO), aprovação/reprovação (FECHADO/ATRIBUIDO), follow-ups e `PATCH /api/usuarios`
  (ativar/desativar) são a F4.2. O front do ciclo de vida (linha do tempo, ações, fila) é a F4.3.

---

## F3.3 — Front de anexos e notificações (17/10/2026) — fecha a F3

- **Camada de API:** `api/anexos.ts` (`listarAnexos`, `enviarAnexo` via `fetch` multipart com o
  token em memória, `baixarAnexo` via `fetch` autenticado + download por blob) e
  `api/notificacoes.ts` (`listar`, `contarNaoLidas`, `marcarLida`, `marcarTodasLidas`).
- **`ZonaUpload`:** componente reutilizável (arrastar/soltar ou clicar) que valida **no cliente**
  tipo (PNG/JPG/PDF) e tamanho (≤ 10 MB), espelhando B9/B10; mostra erro e entrega os arquivos
  válidos ao pai.
- **Anexos no Novo Chamado (etapa 3):** o rascunho (Zustand) passou a guardar `File[]`; a tela lista
  os arquivos escolhidos (removíveis, respeitando o limite de 5). Após criar o chamado, os anexos
  são enviados; **se algum falhar, o chamado continua criado** e a confirmação avisa para reenviar
  no detalhe (FE do DoD da F3).
- **Anexos no Detalhe:** lista os anexos com botão de download (fetch autenticado) e uma
  `ZonaUpload` que envia na hora (invalida a lista); desabilita ao atingir 5.
- **Tela de Notificações (`/notificacoes`):** lista as do usuário (não lidas destacadas), "Marcar
  todas como lidas", e clicar numa notificação marca como lida e abre o chamado; estados de
  carregando e vazio.
- **Contador no menu:** o `MenuLateral` busca `GET /api/notificacoes/contagem` com
  `refetchInterval` de **30 s** (polling, decisão B11) e mostra um badge dinâmico; as ações
  invalidam a contagem.
- **Testes (Vitest + MSW, 6 novos):** `zonaUpload.test` (aceita PNG; rejeita tipo e > 10 MB via
  drop) e `notificacoes.test` (lista, marcar todas, vazio). MSW ganhou handlers de notificações.
- **Validação:**
  - Front: `typecheck`, `lint`, `test` (19) e `build` verdes;
  - **ao vivo via `127.0.0.1:8180`** (imagem `web` reconstruída): rotas do SPA servem;
    `/api/notificacoes` e `/contagem` respondem; o upload/download de anexos já fora validado contra
    o MinIO real na F3.1. **DoD da F3 fechado** (TU16, TU17-portal, anexo de 10 MB pelo Nginx,
    download no escopo).

## Pendências e riscos

- O ciclo de vida (triagem, atribuição, solução, aprovação) e o histórico/follow-ups são a F4, que
  também completa o UC03 e habilita a linha do tempo no detalhe.

---

## F3.2 — Notificações no portal (17/10/2026)

- **Eventos (canal Portal, RF04):** `EventoService.chamado_criado` transforma a abertura de chamado
  em notificações: `CHAMADO_CRIADO` para o solicitante e, quando a severidade é **CRITICO**,
  `CHAMADO_URGENTE` para cada ANALISTA/ADMIN ativo (`UsuarioRepository.ids_tecnicos_ativos`), exceto
  o próprio solicitante. O `ChamadoService.abrir` recebe o `EventoService` por injeção (opcional) e
  dispara após criar — sem acoplar a regra de chamado ao canal de notificação.
- **Endpoints:** `GET /api/notificacoes` (lista do usuário, não lidas primeiro, paginada + contador
  `nao_lidas`), `GET /api/notificacoes/contagem` (badge do menu), `POST /api/notificacoes/{id}/lida`
  e `POST /api/notificacoes/lidas` (204). Escopo: cada usuário vê/marca só as suas; marcar a de
  outro → `404`. Rotas fixas `/contagem` e `/lidas` antes da paramétrica.
- **Camadas:** `NotificacaoRepository` (criar, listar, contar não lidas, marcar uma/todas com
  escopo) e `NotificacaoService` (lista/contagem/marcar; `ErroNotificacao`). Usa o índice parcial
  da migration 0003.
- **Testes (`tests/test_notificacoes.py`, 8 — TU17 portal):** abertura gera `CHAMADO_CRIADO` ao
  solicitante; contagem; CRITICO gera `CHAMADO_URGENTE` ao analista; escopo (cada um vê só as suas);
  marcar uma e todas; marcar a de outro → 404; sem token → 401.
- **AJ-003 (make test rápido):** a suíte estava em ~8 min porque, a cada `TestClient`, o lifespan
  tentava criar os buckets no MinIO e o boto3 ficava ~10 s em timeout (o host `s3` não resolve fora
  da rede do Compose). Correção: o `conftest` roda com `AMBIENTE=test`, e o lifespan **pula** a
  criação de buckets nesse ambiente. `make test` caiu para **~8 s**. Além disso, os testes
  genuinamente pesados (upload de 10 MB, ida e volta das migrations) ganharam o marcador `lento`,
  excluído do run padrão (`addopts -m 'not performance and not lento'`), com os alvos
  `make test-lento` e `make test-tudo`.
- **Validação:**
  - `make lint` ok; `make test` **78 passaram**, 3 deselected, cobertura 91,8% em **~8 s**;
  - **ao vivo via `127.0.0.1:8180`:** abrir chamado gerou `CHAMADO_CRIADO` (contagem 1 → marcar
    lida 204 → contagem 0).

## Pendências e riscos

- A zona de upload de anexos nas telas (wizard/detalhe) e a tela de Notificações com contador no
  menu (polling 30 s) são a F3.3, que fecha a F3.

---

## F3.1 — Backend de anexos (17/10/2026)

- **Migration 0003 (`anexos`, `notificacoes`):** `anexos` guarda só os metadados (o binário vai
  para o S3); `chave_objeto` única, `mime_type` restrito a PNG/JPEG/PDF (CHECK, B10),
  `tamanho_bytes` 1..10 MB (CHECK, B9), `sha256`. `notificacoes` com índice parcial
  `(id_usuario, data_criacao DESC) WHERE lida_em IS NULL`. Downgrade dropa as duas. Entidades
  `Anexo`/`Notificacao` registradas no `Base.metadata`.
- **Storage (seção 5.6):** `core/storage.py` com `StorageService` (Protocol) e `S3StorageService`
  (boto3, `addressing_style=path`, `signature_version=s3v4`, checksums `when_required` para o
  MinIO; `abrir_stream` em blocos de 64 KB; `garantir_buckets` idempotente). `StorageMemoria` para
  testes. A API cria os buckets no **startup** (lifespan), de forma resiliente (não derruba se o
  MinIO estiver fora) e pulada em `AMBIENTE=test`.
- **Service (RF02, RN06, B9/B10):** `AnexoService.anexar/listar/obter_para_download` valida o
  **escopo do chamado** (CLIENTE só os seus → 404 fora do escopo), o **tipo por magic bytes**
  (PNG/JPEG/PDF, ignora o content-type declarado), o **tamanho** (≤ 10 MB) e o **limite de 5 por
  chamado**; calcula o `sha256` e a chave `chamados/{id}/{uuid4}.{ext}`. `escopo_solicitante` do
  `ChamadoService` virou público e é reusado.
- **Endpoints:** `POST /api/chamados/{id}/anexos` (multipart), `GET /api/chamados/{id}/anexos` e
  `GET /api/anexos/{id}/download` (`StreamingResponse`, `Content-Disposition`). Erros: tipo → 415,
  grande/vazio → 413, limite → 409, fora do escopo → 404.
- **Config/infra:** `boto3` e `python-multipart` nas deps; config S3
  (`s3_endpoint_url/access_key/secret_key/regiao/buckets`) e limites de anexo; o serviço `api` do
  Compose recebeu as variáveis S3. `mypy` com override para `boto3`/`botocore` (sem stubs).
- **Testes (`tests/test_anexos.py`, 6 — TU16):** upload ok + lista + download com conteúdo
  idêntico; JPEG e PDF aceitos; tipo inválido (texto com content-type mentido) → 415; acima de 10
  MB → 413; sexto anexo → 409 (B9); anexar no chamado de outro → 404 (RN06). Usam `StorageMemoria`.
- **Validação:**
  - `make lint` ok (ruff + mypy strict, 52 arquivos);
  - `make test` 72 passaram, 1 deselected, cobertura 92,6% (a suíte ficou longa pelo upload de
    10 MB; pode ser isolada depois);
  - **Ao vivo via `127.0.0.1:8180` contra o MinIO real** (migration 0003 aplicada; imagens
    reconstruídas): upload de PNG → download com bytes idênticos, tipo inválido → 415; o objeto foi
    gravado no bucket `mentory-anexos` (`chamados/{id}/{uuid}.png`) e o metadado no banco.

## Pendências e riscos

- Notificações (eventos na abertura, lista/contagem, marcar lidas) são a F3.2; a zona de upload nas
  telas e a tela de Notificações são a F3.3. O DoD da F3 (TU16 ✓, TU17, anexo de 10 MB pelo Nginx)
  fecha ao concluir a F3.2/F3.3.

---

## F2.4 — Telas de chamados (17/10/2026) — fecha a F2

- **Camada `api/chamados.ts`:** `listarCategorias`, `listarChamados` (q/grupo/categoria/página),
  `obterResumo`, `obterChamado` e `abrirChamado`, tipadas pelo schema regenerado do OpenAPI.
- **Dashboard (RNF02/RNF03):** saudação por horário + primeiro nome, botão "Novo Chamado", alerta
  vermelho condicional quando há urgentes (link para a lista filtrada), 4 `CardIndicador` do
  `/resumo`, "Chamados recentes" (5 últimos, com tempo relativo e link para o detalhe) e "Ações
  rápidas".
- **Novo Chamado (UC02, RF02, RF05, FE02, FE03):** wizard de 3 etapas (`Stepper` + `OpcaoCard`):
  Categoria (grade de categorias ativas) → Prioridade (Baixa/Média/Alta/Urgente, com sirene no
  Urgente; o campo enviado é `severidade`) → Detalhes (título + descrição com contador `0/500`).
  Rascunho em memória (Zustand, `stores/rascunhoChamado.ts`); **FE02** destaca título/descrição
  vazios e bloqueia o envio; **Voltar** e **Cancelar** (descarta o rascunho e volta ao Dashboard,
  FE03). Sucesso abre a **tela de confirmação com o protocolo** (ex.: `TK-0051`) e os botões "Ver
  chamado" e "Meus chamados".
- **Meus Chamados (UC03, RF04, RN06):** título + total, busca com **debounce de 300 ms**
  (`useDebounce`), abas com contadores (Todos/Abertos/Em andamento/Resolvidos/Encerrados), chips de
  categoria, `CardChamado` (protocolo mono, categoria, severidade, status, rodapé com datas,
  responsável e nº de mensagens), **paginação** e **filtros refletidos na URL**
  (`?q&grupo&categoria&page`, para o Voltar do navegador). Estados de carregando, vazio e erro.
- **Detalhe (UC03):** `GET /api/chamados/{id}` com cabeçalho (protocolo, categoria, título,
  `StatusBadge`/`SeveridadeBadge`), dados (solicitante, responsável, datas), descrição e nota de
  que histórico/ações chegam na F4. **404** tratado (chamado inexistente ou fora do escopo).
- **Testes (Vitest + MSW, 4 novos):** `novoChamado.test` (percorre as 3 etapas e mostra `TK-0051`;
  FE02 bloqueia o envio) e `chamadosLista.test` (lista com contadores; estado vazio). MSW ganhou
  handlers de categorias, `/resumo` e lista.
- **Validação:**
  - Front: `typecheck`, `lint`, `test` (13) e `build` verdes;
  - **Ao vivo via `127.0.0.1:8180`** (imagem `web` reconstruída): rotas do SPA servem (200),
    `/resumo`, lista (10.061 chamados do seed) e categorias respondem; o Dashboard mostra os
    indicadores e o alerta de urgentes, e o wizard abre chamado com protocolo.

## Pendências e riscos

- Anexos no wizard e no detalhe, e as notificações, são a F3. Histórico, follow-ups e ações por
  perfil (triagem/atribuição/solução) são a F4. O ambiente de dev segue com o volume de carga do
  RNF02 (dados fictícios).

---

## F2.3 — Seeds e medição do RNF02 (17/10/2026)

- **`app/seeds.py`:** `semear_dev` (idempotente pelo e-mail) cria 1 Admin Demo, 3 analistas
  (Rafael Mendes, Sofia Nunes, Thiago Oliveira) e 10 clientes (entre eles **Ana Lima, Analista de
  Marketing**, como no protótipo) e **~60 chamados variados** (distribuição NOVO 18 / PENDENTE 12 /
  ATRIBUIDO 14 / CONCLUIDO 10 / FECHADO 6; técnico setado nos ATRIBUIDO+ para respeitar o CHECK
  RN03). A idempotência dos chamados verifica os chamados **dos clientes do seed** (ignora dados
  avulsos). `semear_performance` insere em lote (SQL em massa, `ON CONFLICT DO NOTHING`): 200
  usuários de carga e 10.000 chamados (NOVO/PENDENTE, sem técnico). Tudo fictício, `@empresa.com.br`,
  senha padrão `mentory-dev-123` (seção 5.7, AGENTS.md §8).
- **CLI + Makefile:** comandos `seed` e `seed-performance` com **guarda de ambiente** (`_exigir_dev`
  bloqueia se `AMBIENTE=prod`); alvos `make seed`, `make seed-performance` e `make test-performance`.
  O run padrão de testes passou a **excluir** o marcador `performance` (`addopts -m 'not
  performance'`), que roda sob demanda.
- **Testes (`tests/test_seeds.py`, 4):** quantidades do dev (3 analistas, 10 clientes, Ana Lima e
  Rafael Mendes presentes, 60 chamados), idempotência (2ª execução não duplica), performance em
  volume reduzido e o teste marcado `@pytest.mark.performance` do RNF02.
- **Medição do RNF02 (ao vivo, 10.061 chamados):** `GET /api/chamados` respondeu em **p95 ≈ 25–29
  ms** (lista, busca por título e filtro por grupo) e `/resumo` em **~10 ms** — bem abaixo do limite
  de **2 s**. Os índices da migration 0001 (trigram no título, índices por status/categoria/data)
  sustentam o desempenho.
- **Validação:**
  - `make lint` ok; `make test` 66 passaram, 1 deselected (performance), cobertura 92,79%;
  - `make test-performance` 1 passou (semeia 10k no banco de teste e afere ≤ 2 s);
  - `make seed` criou 14 usuários e 60 chamados e é idempotente; `make seed-performance` inseriu
    200 usuários e 10.000 chamados em ~13 s.

## Pendências e riscos

- O ambiente de dev ficou com volume de carga (216 usuários, 10.061 chamados) da medição do RNF02 —
  dados fictícios; podem ser limpos a pedido. As telas da F2 (Dashboard, Novo Chamado, Meus
  Chamados, Detalhe) são a F2.4.

---

## F2.2 — Consulta de chamados (17/10/2026)

- **Lista (UC03, RF03/RF04, RN06, RNF02):** `GET /api/chamados` com busca `q`, filtros `grupo` e
  `id_categoria`, contadores e paginação. `ChamadoRepository.listar` aplica o **escopo por perfil**
  (CLIENTE só os seus; ANALISTA/ADMIN todos), a busca por **título** (trigram
  `f_unaccent(lower(...)) LIKE`, com escape de `% _ \`) **ou protocolo** (`id_chamado` via regex
  `^(tk-?)?0*(\d+)$`), e a **ordenação da seção 6.5** (CRITICO ainda não resolvido primeiro, depois
  `data_criacao` desc). `qtd_mensagens` é 0 até a F4 (tabela de follow-ups).
- **Contadores (seção 6.5):** `count(*) FILTER (WHERE ...)` numa única consulta; respeitam `q` e
  categoria, mas **ignoram** o filtro de grupo.
- **Resumo (RF04):** `GET /api/chamados/resumo` com abertos/em_andamento/resolvidos/encerrados e
  urgentes (CRITICO ainda não resolvido), no escopo do perfil.
- **Detalhe (RN06):** `GET /api/chamados/{id}` no escopo; fora do escopo ou inexistente →
  `404 NAO_ENCONTRADO` (não revela o chamado de outro — seção 6.4). A rota fixa `/resumo` é
  declarada **antes** da paramétrica `/{id}` (seção 7.1).
- **Service/Schemas:** `ChamadoService.listar/resumo/obter` com `_escopo_solicitante` (RN06);
  `ChamadoLista` (items + total + page + page_size + `contadores`), `ContadoresChamados` e
  `ResumoSaida`. O item da lista reusa `ChamadoSaida` (F2.1).
- **Testes (10 novos):** `tests/test_chamados_consulta.py` — sem token `401`; CLIENTE só os seus;
  **TU07** (CLIENTE pede chamado de outro → `404`); ANALISTA vê todos; **TU08** (busca por título e
  por protocolo, filtro por grupo e categoria, contadores que ignoram o grupo mas respeitam a
  busca, paginação); ordenação CRITICO primeiro; `/resumo`.
- **Validação:**
  - `make lint` ok (ruff + mypy strict, 44 arquivos);
  - `make test` 63 passaram, cobertura 93,34%;
  - **Ao vivo via `127.0.0.1:8180`:** lista com contadores, `/resumo`, detalhe de `TK-0001`, busca
    `q=vpn` e id inexistente → `404`.

## Pendências e riscos

- Os filtros extras de ANALISTA/ADMIN (`responsavel`, `severidade`, `id_solicitante`) e a visão de
  fila são da F4. Seeds e a medição formal do RNF02 (≤ 2 s) são a F2.3. A tela de Meus Chamados é a
  F2.4.

---

## F2.1 — Backend de abertura de chamados (17/10/2026)

- **Abertura (UC02, RF02, RF05, RN04):** camadas `CategoriaRepository` (ativas por `ordem`;
  `buscar_ativa_por_id`) e `ChamadoRepository` (cria + `refresh` para pegar `protocolo`/status/datas
  gerados) → `services/chamado_service.py` (`abrir`, `listar_categorias`, `ErroChamado`) →
  `controllers/categorias.py` e `controllers/chamados.py`.
- **RN04 (TU01, TU02):** o chamado só nasce com **categoria ativa** e **solicitante ativo**; o
  solicitante vem **sempre do token** (nunca do corpo). Categoria inexistente/inativa →
  `409 CATEGORIA_INVALIDA`; solicitante inativo não cria (a dependência `usuario_atual` já barra com
  `401`, e o service tem a checagem como segunda barreira). Estado inicial **NOVO**; `protocolo`
  gerado pelo banco (`TK-####`).
- **Validação (TU04):** `ChamadoCriar` valida `titulo` (1..150) e `descricao` (1..500) **após
  `strip`**; vazios ou acima do limite → `422 VALIDACAO` com o campo. `severidade` opcional (padrão
  `BAIXA`).
- **Contrato (seção 7.3):** `ChamadoSaida` com `categoria` e `solicitante` aninhados,
  `status_grupo` (mapa da seção 6.1: NOVO/PENDENTE→abertos etc.), `tecnico_responsavel` nulo e
  `qtd_mensagens` 0 na abertura. `GET /api/categorias` (autenticado) devolve as ativas ordenadas.
- **Endpoints:** `GET /api/categorias` (autenticado, qualquer perfil) e `POST /api/chamados`
  (autenticado, para o próprio usuário). Registrados no `main`; dependência `obter_chamado_service`
  e override no `conftest` (sessão transacional).
- **Testes (13 novos):** `tests/test_chamados.py` — GET categorias (exige auth; 7 ordenadas),
  TU01 (sem categoria `422`; inexistente/inativa `409`), TU02 (solicitante inativo não cria),
  TU03 (NOVO + `status_grupo` abertos + severidade informada e padrão BAIXA + protocolo `TK-####`),
  TU04 (título/descrição vazios e descrição > 500 → `422`).
- **Validação:**
  - `make lint` ok (ruff + mypy strict, 44 arquivos em `app`);
  - `make test` 53 passaram, cobertura total 92,68% (serviços novos cobertos; a branch
    `SOLICITANTE_INATIVO` fica como rede de segurança, já que `usuario_atual` barra antes);
  - **Ao vivo via `127.0.0.1:8180`:** categorias ordenadas (TI, RH, …), `POST` criou **TK-0001**
    (NOVO/abertos, solicitante do token), categoria inválida `409`; persistido no banco (admin e
    chamado intactos — os testes rodam em `helpdesk_test`, AJ-002).

## Pendências e riscos

- Lista, busca, filtros, contadores, `/resumo`, `/{id}` e o escopo por perfil (RN06) são da F2.2.
  A tela de Novo Chamado (wizard 3 etapas) é da F2.4.

---

## F1.3 — Telas de autenticação (17/10/2026) — fecha a F1

- **Schema da API:** `src/api/schema.ts` regenerado do OpenAPI real (`make front-gen-api`), com os
  contratos de auth, usuários e config pública.
- **Camada de auth (seção 8.1):** `api/client.ts` injeta o access token (em memória) por middleware
  e, em `401` fora das rotas `/api/auth/*`, tenta `POST /api/auth/refresh` (cookie) uma vez e repete
  a requisição; se falhar, limpa a sessão. `stores/sessao.ts` guarda usuário + token com estado
  `verificando/autenticado/anonimo`. `api/auth.ts` (login, logout, `restaurarSessao`, `trocarSenha`)
  e `api/usuarios.ts` (listar, cadastrar, config pública). `App.tsx` restaura a sessão no mount.
- **Rotas protegidas de verdade:** `RequirePerfil` aguarda a restauração (tela de carregamento),
  manda anônimo para `/login` guardando a origem e barra perfil sem permissão. O `AppShell` ganhou
  o botão **Sair** (logout + toast).
- **Login (RF01/FE01, UJ01):** React Hook Form + Zod; mensagem genérica de erro (FE01) e `429`
  vindos do backend; "Entrar com Google Workspace" só quando `google_sso`; atalho de suporte por
  `wa.me`/`mailto` da config pública; estados de carregamento.
- **Perfil:** dados do usuário (da sessão/`/api/auth/me`) e troca de senha (`PUT /api/auth/senha`)
  com validação (nova ≥ 8, confirmação) e erro de campo para senha atual incorreta.
- **/admin/usuarios (UC01):** lista paginada com busca (`q`) e filtro de perfil (`GET /api/usuarios`,
  `placeholderData`), e modal de cadastro (`POST /api/usuarios`) com erro no campo para
  `EMAIL_DUPLICADO` e senha fraca; sucesso dá toast e invalida a lista.
- **Testes (Vitest + MSW + user-event):** 9 no total — login (sucesso grava sessão, FE01 genérico,
  validação de campos) e admin (lista, `EMAIL_DUPLICADO` no campo). `setup.ts` com MSW e polyfill de
  `matchMedia`. Dependências novas: `@hookform/resolvers`, `msw`, `@testing-library/user-event`.
- **Defeito encontrado e corrigido (AJ-001):** na validação ao vivo, `obter_sessao` não fazia
  `commit()` — nenhum endpoint de escrita persistia (refresh, cadastro e o bloqueio de e-mail
  duplicado quebravam na stack real, embora os testes passassem). Corrigido em
  `app/core/database.py` (commit no sucesso, rollback no erro) com regressão em `tests/test_sessao.py`.
- **Validação:**
  - Front: `typecheck`, `lint`, `test` (9) e `build` verdes;
  - Backend: `make lint` ok, `make test` 42 passaram (cobertura 91%);
  - **Ao vivo via `127.0.0.1:8180`** (imagens `api`/`web` reconstruídas): login do admin, refresh
    renova o token, `me`, cadastro `201`, e-mail duplicado `409 EMAIL_DUPLICADO`, lista cresce.

## Pendências e riscos

- Sem autenticação Google (F7) e sem "esqueci a senha" (F7): o Login mostra só os caminhos
  previstos. As demais telas (Dashboard, Chamados, Base) seguem vazias até a F2+.

---

## F0.5 — Fundação do front-end (17/10/2026) — fecha a F0

- **Identidade (ADR 2026-10-17):** o `frontend/` residual foi refeito na identidade do esboço
  ("01 — Foundations"): marca teal (Brand 600 `#066873`), **IBM Plex Sans**, sidebar branca, tema
  **claro e escuro**. `src/index.css` com `@theme inline` do Tailwind 4 apontando para variáveis
  que trocam por `data-theme`; fontes auto-hospedadas (`@fontsource/ibm-plex-sans` e `-mono`).
- **Tema:** `stores/tema.ts` (preferência claro/escuro/sistema com persistência em localStorage) +
  `lib/useTema.ts` (aplica `data-theme` no `<html>` e acompanha `prefers-color-scheme`); botão
  `ControleTema` no AppShell e no Login. Respeita `prefers-reduced-motion`.
- **AppShell (seção 8.3):** `MenuLateral` (sidebar branca, bloco do usuário, itens por perfil, chip
  "Novo", item **"Assistente IA — em breve"** desabilitado, link do Perfil), topbar com breadcrumb e
  gaveta no mobile. Componentes restyle para os novos tokens: `StatusBadge`/`SeveridadeBadge`
  (cores da seção 6.1), `CategoriaChip`, `CardIndicador`, `CardChamado`, `OpcaoCard`, `Stepper`.
- **Rotas (React Router 7):** `app/router.tsx` com `createBrowserRouter`; Login fora do shell;
  `RequirePerfil` (stub da sessão em memória) protege o restante; `admin/usuarios` exige ADMIN.
  Páginas vazias (`PaginaVazia`): Dashboard, Meus Chamados, Novo, Detalhe, Base, Notificações,
  Perfil, Admin e 404. `App.tsx` (QueryClient + tema + Toaster) e `main.tsx`.
- **Serviço `web`:** `frontend/Dockerfile` multi-stage (Node 22 build → `nginxinc/nginx-unprivileged`
  na 8080, não-root); `nginx.conf` serve a SPA e faz proxy de `/api` → `api:8000`. No Compose base;
  porta publicada em `127.0.0.1:${PORTA_WEB:-8180}` no override de dev. Depende da `api` saudável.
- **Testes:** Vitest + Testing Library; `src/test/setup.ts` (jest-dom) e `basico.test.tsx` (4
  testes: StatusBadge nos estados 6.1, `iniciais`, `saudacao`). `vitest.config.ts` separado do
  `vite.config.ts`.
- **Makefile:** `front-install`, `front-lint` (eslint + tsc), `front-test`, `front-build`,
  `front-dev` e `front-gen-api` (aponta para `localhost:8100`).
- **Correções de build relevantes:** `@testing-library/react` → 16.3.3 (compatível com React 19);
  `vite-env.d.ts` (`vite/client`) para tipar o import de `.css`; e **alinhar `tailwindcss` e
  `@tailwindcss/vite` em 4.3.3** — o mismatch 4.0.0 (declarado) vs 4.3.3 (engine puxado) quebrava o
  build do Tailwind ("Cannot convert undefined or null to object").
- **Validação (host):** `npm run typecheck`, `npm run lint`, `npm run test` (4 passaram) e
  `npm run build` verdes; `docker compose config` ok com o serviço `web` presente (8 serviços).

## Pendências e riscos

- A base de front não tem autenticação real nem dados: as telas estão vazias de propósito (ganham
  conteúdo nas fases seguintes; Login/Perfil/Admin na F1.3). A imagem do `web` ainda não foi
  construída via Compose (`make build`); lint/test/build rodam no host com npm e passam.

---

## F1.2 — Cadastro de usuários, config pública e criar-admin (17/10/2026)

- **Cadastro (UC01, RF01, RN07):** camadas `UsuarioRepository` (ganhou `existe_email`, `criar` e
  `listar` paginado) → `services/usuario_service.py` (`UsuarioService.cadastrar`/`listar`/`obter`,
  com `ErroUsuario` de código estável) → `controllers/usuarios.py`. `POST /api/usuarios` valida
  RN07 (e-mail único, normalizado em minúsculas → `409 EMAIL_DUPLICADO`, inclusive quando só a
  caixa difere) e TU06 (senha 8..72 bytes → `422 VALIDACAO`; hash BCrypt `$2b$`, nunca em claro).
- **Autorização:** todo o router `/api/usuarios` tem `exigir_perfil(ADMIN)` (decisão B1, sem
  auto-cadastro). Sem token → `401`; CLIENTE → `403` (TU07). `GET /api/usuarios` é paginado
  (`q`, `perfil`, `ativo`, `page`, `page_size` 1..50) no envelope `{ items, total, page,
  page_size }`; `GET /api/usuarios/{id}` devolve o detalhe ou `404 NAO_ENCONTRADO`.
- **Config pública:** `GET /api/config/publica` (público) devolve
  `{ whatsapp_suporte, email_suporte, google_sso, versao }` para a tela de login. `google_sso`
  deriva de `GOOGLE_CLIENT_ID`; `versao` vem de `app.__version__` (fonte única, também no
  OpenAPI; subiu para `0.1.0`). Nenhum segredo é exposto.
- **`make criar-admin`:** `app/cli.py` (Typer) lê `ADMIN_NOME/EMAIL/SENHA` do `.env` e é
  idempotente (não recria nem troca a senha se o e-mail já existe). A lógica fica em
  `criar_admin_na_sessao(sessao, config)`, separada do `commit` para ser testável. O alvo roda
  `docker compose run --rm api python -m app.cli criar-admin`.
- **Compose:** o serviço `api` passou a receber `JWT_*`, `BCRYPT_CUSTO`, `CORS_ORIGINS`,
  `WHATSAPP_NUMERO_SUPORTE`, `EMAIL_SUPORTE`, `GOOGLE_CLIENT_ID` e `ADMIN_*`, para a API em
  container e o `make criar-admin` funcionarem.
- **Config (`core/config.py`):** novos campos `admin_nome/email/senha`,
  `whatsapp_numero_suporte`, `email_suporte`, `google_client_id`, e as propriedades `google_sso`
  e `versao`.
- **Testes (12 novos):** `tests/test_usuarios.py` com PostgreSQL real — cadastro `201` e
  normalização do e-mail, TU05 (duplicado e diferença só de caixa → 409), TU06 (senha curta → 422
  sem gravar; hash `$2b$`), lista com filtros e `page_size`, detalhe/404, TU07 (sem token → 401,
  CLIENTE → 403), config pública (contrato público) e o CLI `criar-admin` idempotente. O
  `conftest` ganhou o override de `obter_usuario_service` no `app_integrado`.
- **Documentação:** `docs/DECISOES.md` (ADR 2026-10-17 — F1.2), `docs/ROADMAP.md` (F1.2
  concluído, F1.3 próximo), `docs/RASTREABILIDADE.md` (RF01/RN06/RN07/UC01 e itens da F1.2) e
  este arquivo. `README.md` menciona `make criar-admin` e `/api/config/publica`.
- **Validação (host, com o PG de dev no ar):**
  - `make lint` ok (ruff check, ruff format --check, mypy `strict`, 38 arquivos em `app`);
  - `make test` 40 passaram, cobertura total 90,57% (módulos novos: `usuarios`, `config`,
    `usuario_service` e `usuario_repository` em 100%); piso de 50% atingido;
  - `make config` (`docker compose config`) ok.

## Pendências e riscos

- A imagem `api` em execução é anterior à F1.1/F1.2; `make criar-admin` exige `make build` antes
  (usa `docker compose run --rm api`). Os testes rodam no host com `uv` e passam.
- O ciclo de vida de usuário (PATCH, `ativo`/exclusão lógica, `/tecnicos`) é da F4; a tela
  `/admin/usuarios` é da F1.3.

---

## F1.1 — Backend de autenticação (17/10/2026)

- **Migration `0002_autenticacao`** cria `tokens_refresh` (seção 5.4): `id` BIGINT identity,
  `id_usuario` FK `ON DELETE RESTRICT`, `token_hash` `CHAR(64)` único (SHA-256), `familia` UUID,
  `expira_em`, `revogado_em` (nulo), `criado_em`, com índices por família e por usuário.
  `downgrade()` remove a tabela. Entidade `TokenRefresh` registrada no `Base.metadata`.
- **`app/core/seguranca.py`:** validação de senha (8..72 bytes), hash/conferência BCrypt
  (`BCRYPT_CUSTO`), access token JWT HS256 (claims `sub`/`perfil`/`iat`/`exp`/`jti`), refresh
  opaco de 256 bits e seu SHA-256, e `familia`. **`app/core/rate_limit.py`:** 5 tentativas por IP
  e por e-mail em 15 min no Redis (`rl:login:*`).
- **Camadas:** `repositories/` (`UsuarioRepository`, `TokenRefreshRepository`) →
  `services/auth_service.py` (`AuthService`: login, refresh com rotação e revogação de família,
  logout, `me`, troca de senha) → `controllers/auth.py` (rotas) e `controllers/dependencias.py`
  (`usuario_atual`, `exigir_perfil`). O service não importa FastAPI.
- **Endpoints:** `POST /api/auth/login` (público), `POST /api/auth/refresh` (cookie),
  `POST /api/auth/logout` (autenticado), `GET /api/auth/me`, `PUT /api/auth/senha`. Cookie
  `refresh_token` `HttpOnly`, `SameSite=Strict`, `Path=/api/auth`, `Secure` em produção. CORS só
  em dev. Login com mensagem genérica (FE01) e `429` ao estourar o limite (RNF01).
- **Config:** `JWT_SECRET`, `JWT_ACCESS_MINUTOS` (30), `JWT_REFRESH_DIAS` (7), `BCRYPT_CUSTO`
  (12) e `CORS_ORIGINS` (já presentes no `.env.example` desde a F0.1). Dependências novas:
  `pyjwt`, `bcrypt`, `email-validator` (`uv.lock` atualizado).
- **Testes (20 novos):** `tests/test_autenticacao.py` (18) com PostgreSQL real e `fakeredis`
  (fixtures de integração em `conftest.py`: `engine_banco`, `sessao_banco` transacional,
  `app_integrado` com overrides, helper `criar_usuario`), cobrindo contrato do login + cookie,
  FE01 (mensagem genérica, inativo), TU06 (hash `$2b$`, senha curta/>72 → 422), TU07 (sem token →
  401, `exigir_perfil` ADMIN nega CLIENTE → 403), `me`, refresh com rotação, reuso de token
  revogado derrubando a família, logout, e RNF01 (limite → 429). A ida e volta das migrations
  passou a cobrir `0001 ↔ 0002`.
- **Decisões:** registradas em `docs/DECISOES.md` (ADR 2026-10-17 — Autenticação). Destaque:
  `bcrypt` fixado na linha 4.x; `email-validator` rejeita o TLD `.test`, então os dados fictícios
  usam `.com`/`.com.br`.
- **Validação (host, com o PG de dev no ar):**
  - `make lint` ok (ruff check, ruff format --check, mypy `strict`, 33 arquivos em `app`);
  - `make test` 28 passaram, cobertura total 89,71% (`auth_service` 88%, repositórios 100%,
    `seguranca` 96%); piso de 50% atingido;
  - `test_migrations_ida_e_volta` (`0001 → 0002 → base → head`) ok; banco de dev em `0002` com a
    tabela `tokens_refresh` (7 colunas) conferida.

## Pendências e riscos

- A imagem `api` em execução é anterior à F1.1 (sem as rotas novas); precisa de rebuild para a API
  do Compose refletir a autenticação. Os testes rodam no host com `uv` e passam.
- Cadastro de usuário, `make criar-admin` e `/api/config/publica` são da F1.2 (incluem TU05).

---

## F0.4 — Qualidade e CI (17/10/2026)

- **Cobertura (pytest-cov):** `backend/pyproject.toml` com `addopts = "-q --cov=app
  --cov-report=term-missing --cov-fail-under=50"`, `[tool.coverage.run]` (branch, `source = app`,
  `omit` das migrations) e `[tool.coverage.report]` (`show_missing`, `exclude_also` para
  `__main__`, `TYPE_CHECKING` e `NotImplementedError`). O piso é baixo de propósito nesta fase
  (quase não há camada de serviço) e sobe quando os services da F1/F2 existirem; a meta final da
  seção 12.1 é 90% em `services/` e 80% no total. O marcador `performance` foi mantido.
- **GitHub Actions (`.github/workflows/ci.yml`):** dispara em `pull_request` para `develop`/`main`
  e em `push` para essas branches. Job `backend` em `ubuntu-latest` com serviço PostgreSQL
  `postgres:17.11-alpine` (health-check por `pg_isready`, porta `5432` publicada no runner).
  Passos: `actions/checkout@v4`, `astral-sh/setup-uv@v6` (uv `0.13.1` fixado),
  `actions/setup-python@v5` (3.13), `uv sync --frozen`, escrita de um `.env` mínimo apontando o
  `PORTA_DB` para a porta do serviço (os testes leem esse `.env` para montar a URL do host),
  `ruff check`, `ruff format --check`, `mypy app`, `alembic upgrade head` e `pytest`. Driver
  `postgresql+psycopg`, `BCRYPT_CUSTO=4` para velocidade. Versões de ação fixadas (sem `@latest`).
- **Template de PR (`.github/pull_request_template.md`):** PT-BR com resumo, requisitos/códigos
  (RF/RNF/RN/UC/UJ/FA/FE/TU), o que foi testado e checklist (lint, testes com cobertura, ida e
  volta de migration, `docker compose config`, sem dado pessoal real, docs atualizadas, prints
  quando há tela).
- **Makefile:** alvo `format` (`ruff format .`) somado ao `lint`/`test` já existentes.
- **Documentação:** `README.md` (seção "Integração contínua e fluxo de branches", notas de
  proteção de branch e menção à cobertura), `docs/ROADMAP.md` (F0.4 → concluído, F0.5 → próximo),
  `docs/RASTREABILIDADE.md` (entrada de CI/qualidade) e este arquivo.
- **Validação (host, com o PG de dev no ar):**
  - `make lint` ok (ruff check, ruff format --check, mypy `strict`);
  - `make test` 10 passaram, cobertura total 83,82% (piso de 50% atingido);
  - `docker compose config` ok; `git diff --check` limpo;
  - YAML do workflow validado localmente com `yaml.safe_load` (bem-formado). O workflow só executa
    de fato no GitHub, quando houver remoto e um push/PR; aqui foi validada apenas a sintaxe.

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
