# Decisões

Decisões de arquitetura e de produto **já implementadas**, no formato ADR curto. Mais recente
primeiro. Decisões aprovadas e ainda sem código ficam em
[DEVELOPMENT_STATUS.md](DEVELOPMENT_STATUS.md), na seção "Decisões aprovadas, ainda não
implementadas".

Formato de cada entrada:

```markdown
## AAAA-MM-DD — Título

**Contexto:** o problema ou a lacuna.
**Decisão:** o que foi escolhido.
**Consequências:** o que muda, migrations, riscos e alternativas descartadas.
**Requisitos:** códigos afetados (RF, RN, UC...).
```

As diferenças em relação ao Documento 02 (seção 5.3 do prompt) entram aqui na F0.3, junto com a
migration `0001_esquema_inicial`.

---

## 2026-10-18 — SLA do mês (F7.2 / decisão B20)

**Contexto:** o Dashboard mostra o "SLA do mês" e o painel do Login promete "SLA por categoria e
prioridade". Faltava a política de prazo e o cálculo (seção 7.2/8.4).

**Decisão:**
- **Metas por severidade** em `sla_politicas` (B20): CRITICO 4 h · ALTA 8 h · MEDIA 24 h · BAIXA
  72 h, **horas corridas** (horário comercial fica fora do escopo). Ajustável pela tabela.
- **Prazo gravado na abertura** (`chamados.prazo_sla = data_criacao + prazo_horas`), imutável depois
  — reflete a meta no momento em que o chamado nasceu, mesmo que a política mude.
- **"SLA do mês"** = entre os chamados **concluídos no mês** (por `data_conclusao`), o percentual com
  `data_conclusao <= prazo_sla`. Chamados sem `prazo_sla` (anteriores à F7.2) contam no total, não
  como no prazo — conservador e honesto.

**Consequências:** migration 0008 (tabela + seed + coluna), entidade `SlaPolitica`, `SlaRepository`/
`SlaService`, `GET /api/sla/mes` e o cartão no Dashboard. O `ChamadoService` ganhou o `SlaRepository`
(opcional). Numeração: a 0007 ficou só com os tokens de senha e a 0008 com o SLA (recortes isolados;
difere do `0007_sla_senha` único citado na seção 5.3).

**Requisitos:** seção 7.2/8.4; decisão B20; testes `test_sla`, `dashboardSla.test`.

---

## 2026-10-18 — Redefinição de senha por e-mail (F7.1 / FA02)

**Contexto:** permitir que o usuário recupere o acesso sem o TI, por e-mail, sem abrir brecha de
enumeração de contas (seção 7.2, FA02).

**Decisão:**
- **Token opaco guardado como hash** (SHA-256) em `tokens_redefinicao_senha`, expiração de **30 min**
  e **uso único** (`usado_em`) — mesmo padrão do refresh token. O valor em claro só vai no link do
  e-mail.
- **Esqueci-senha silencioso:** sempre a mesma resposta, exista o e-mail ou não (anti-enumeração);
  só gera token para usuário **ativo**.
- **E-mail pelo outbox, ignorando `notificar_email`:** é transacional de segurança, não uma
  notificação opcional (exceção explícita da matriz 9.6).
- **Redefinir revoga todas as sessões** do usuário e invalida o token.
- **Migration isolada (0007):** só a tabela de tokens; o SLA entra na 0008 (F7.2).

**Consequências:** nova entidade `TokenRedefinicaoSenha`, `TokenRedefinicaoRepository`,
`EventoService.senha_redefinicao`, dois endpoints públicos em `auth.py` e as telas `/esqueci-senha`
e `/redefinir-senha`; o Login ganhou o link funcional. O `AuthService` passou a receber (opcionais)
o repo de redefinição, o `EventoService` e o `portal_url`.

**Requisitos:** FA02; `TOKEN_INVALIDO` (400); testes `test_redefinicao_senha`, `redefinicaoSenha.test`.

---

## 2026-10-18 — Infra n8n + WAHA (F6.5)

**Contexto:** ligar os canais externos de ponta a ponta exige o n8n (transporte/entrega) e o WAHA
(sessão do WhatsApp), em containers, respeitando as regras do servidor ARM64 (seção 3).

**Decisão:**
- **Imagens fixas e ARM64:** `n8nio/n8n:2.34.4` (Community) e `devlikeapro/waha:arm-2026.4.3`
  (pública/Apache-2.0; a tag `arm-*` é a do servidor Ampere). Nunca `latest`.
- **n8n no Postgres do projeto:** reutiliza o banco criado por `infra/postgres/init/01-n8n.sh`
  (um único Postgres), em vez de subir outro banco só para o n8n.
- **SMTP via Mailpit em dev:** o n8n manda e-mail pelo Mailpit em desenvolvimento; a credencial de
  produção entra depois (não há segredo no repositório).
- **Sem publicação:** os serviços ficam na rede interna, com limites de CPU/memória e **sem portas
  na internet** — a exposição pelo Traefik exige autorização (regra do servidor). Em dev, portas só
  em `127.0.0.1`.
- **Workflows versionados sem credenciais:** `integrations/n8n/workflows/*.json` usam `$env` para os
  tokens e credencial nomeada para o SMTP; nada de segredo nos arquivos.
- **Healthcheck do WAHA por `/ping`:** a raiz do WAHA exige a API key (401); `/ping` responde 200
  sem auth.

**Consequências:** `docker-compose.yml` ganhou `n8n`/`waha` e os volumes `n8n_data`/`waha_data`;
o override publica as portas de dev; `.env.example` ganhou `PORTA_N8N`/`PORTA_WAHA`. Novos
`integrations/n8n/` e `integrations/waha/` (workflows + READMEs). Fecha a F6.

**Requisitos:** seção 9.7; `/home/ubuntu/AGENTS.md` (ARM64, limites, portas, Traefik sob
autorização).

---

## 2026-10-18 — Bot: fluxo guiado, aprovação e `/admin/integracoes` (F6.4b)

**Contexto:** fechar o atendimento pelo WhatsApp: abrir chamado passo a passo, aprovar/reprovar a
solução pela conversa e dar visibilidade da integração ao ADMIN (seção 9.5).

**Decisão:**
- **Máquina de estados na conversa** (`wa:conversa`, Redis, TTL 30 min): categoria → prioridade →
  título → descrição → confirmação. A abertura reusa `ChamadoService.abrir` (RN04) com
  `canal_origem=WHATSAPP` (coluna da 0006), sem duplicar regra.
- **Aprovação pela conversa (RN02):** comandos `APROVAR/REPROVAR TK-xxxx` (motivo obrigatório na
  reprovação) e atalho `1`/`2` quando a conversa está em `AGUARDANDO_APROVACAO` — estado armado
  quando o solicitante consulta um chamado CONCLUIDO seu. Isso evita acoplar o `EventoService` ao
  Redis: o aviso de solução orienta "responda 1 ou 2" e, ao checar o protocolo, o atalho é ativado.
- **Sessão do WAHA** guardada no Redis (`wa:sessao`) pelo `POST …/sessao` e lida pelo
  `GET /api/admin/integracoes`; a tela junta isso com a fila do outbox (F6.2).

**Consequências:** `BotService` ganhou `ChamadoService`/`CicloVidaService` (injetados na dependência);
`ChamadoRepository.criar`/`ChamadoService.abrir` aceitam `canal_origem`. Novos
`controllers/admin_integracoes.py`, endpoint de sessão em `integracoes.py`, `api/integracoes.ts` e
`AdminIntegracoesPage`. O endpoint de sessão responde 200 `{ok}` (um 204 tipado quebra o FastAPI).

**Requisitos:** seção 9.5; RN02, RN04; testes `test_bot_whatsapp`, `adminIntegracoes.test`.

---

## 2026-10-18 — Bot de atendimento do WhatsApp: núcleo (F6.4)

**Contexto:** com o vínculo pronto (F6.3), falta o atendimento de entrada: o WAHA entrega ao n8n,
que chama a API, e a API devolve as respostas do bot (seção 9.3/9.5).

**Decisão:**
- **Regras e textos no backend** (o n8n é só transporte): `BotService` roteia os comandos sem
  diferenciar maiúsculas nem acentos; os textos ficam em `app/integrations/whatsapp/mensagens.py` e
  têm testes.
- **Autenticação por chave** no header `X-Integracao-Chave` (não é usuário logado); sem chave
  configurada o endpoint fica indisponível (não deixa o bot aberto).
- **Idempotência**: dedup por `SET NX` em `wa:msg:{message_id}`; a mesma mensagem não gera resposta
  duas vezes (o n8n entrega "pelo menos uma vez").
- **Identificação** por `whatsapp_chat_id` → `whatsapp_lid` → `whatsapp_numero`, só ativos; número
  não vinculado só aceita `VINCULAR <código>` (que consome o código do Redis e grava o vínculo).
- **Minimização (LGPD)** e **RN06**: status/consulta só dos chamados do próprio solicitante.
- **Recorte**: o fluxo guiado de abertura (`1`, com `canal_origem=WHATSAPP`), a aprovação da solução
  pelo WhatsApp, o `POST /api/integracoes/whatsapp/sessao` e a tela `/admin/integracoes` ficaram para
  a **F6.4b**, para manter o recorte revisável. O estado da conversa (`wa:conversa`, TTL 30 min) já
  foi criado como base.

**Consequências:** pacote `app/integrations/whatsapp` (`mensagens.py`, `estado.py`), `BotService`,
`controllers/integracoes.py`, e `buscar_por_whatsapp`/`vincular_whatsapp` no `UsuarioRepository`. Os
serviços `api`/`worker` do compose passaram a receber `INTEGRACAO_API_KEY` e as vars do n8n.

**Requisitos:** seção 9.3/9.5; RN06; testes `test_bot_whatsapp`.

---

## 2026-10-17 — Vínculo do WhatsApp por prova de posse + consentimento (F6.3)

**Contexto:** para notificar e atender pelo WhatsApp é preciso ligar o número do usuário ao chat,
sem cair nos problemas do 9º dígito/`@lid` e com base legal (consentimento, LGPD) — seção 9.4.

**Decisão:**
- **Prova de posse iniciada pelo usuário:** a API gera um **código de 6 dígitos**, guarda no Redis
  só o `sha256(codigo) → id_usuario` com **TTL de 10 min** e devolve o link
  `wa.me/<número>?text=VINCULAR <código>`. O primeiro contato parte do usuário (menos risco de
  bloqueio) e o bot (F6.4) completa o vínculo ao receber a mensagem. Guardar o hash evita expor o
  código em claro se o Redis for inspecionado.
- **Consentimento obrigatório** antes de gerar o vínculo (`422 CONSENTIMENTO_OBRIGATORIO`);
  opt-out a qualquer momento (`DELETE`), que apaga o vínculo e desliga o opt-in.
- **Preferências** (`notificar_email`, `whatsapp_opt_in`) no `PATCH /api/perfil/preferencias`,
  expostas também no `GET /api/auth/me` para o front refletir o estado.
- **QR no navegador** (`qrcode.react`, pinado) e **polling de 3 s** enquanto aguarda a confirmação.

**Consequências:** `core/vinculo_whatsapp.py` (código/hash/TTL), `PerfilService`,
`controllers/perfil.py` e os métodos `atualizar_preferencias`/`desvincular_whatsapp` no
`UsuarioRepository`. `UsuarioPublico` (do `/auth/me`) ganhou os três campos. Nova dependência de
front `qrcode.react@4.2.0`. O consumo de `VINCULAR <código>` pelo bot é a F6.4.

**Requisitos:** seção 9.4; testes `test_perfil`, `perfilWhatsapp.test`.

---

## 2026-10-17 — Worker despacha o outbox ao n8n (F6.2)

**Contexto:** com o outbox gravado (F6.1), falta entregar os eventos ao n8n com garantia de "pelo
menos uma vez" e sem perder nada se o n8n/WAHA estiver fora do ar (seção 9.2).

**Decisão:**
- **Reserva em lote com `FOR UPDATE SKIP LOCKED`** (exatamente o SQL da seção 9.2): marca
  `PROCESSANDO` + `bloqueado_ate = now()+60s`, permitindo escalar o worker sem processar o mesmo
  evento duas vezes.
- **Backoff exponencial** (30 s, 1, 2, 4, 8, 16, 32 min, 1 h) por `tentativas`; na 8ª vai para
  `FALHOU`, visível e reenfileirável em `/admin/outbox`.
- **Idempotência no n8n:** cada `POST` leva `X-Evento-Id`; o n8n descarta repetidos (o contrato é a
  seção 9.2). O token vai no header `X-Mentory-Token`.
- **Gating por `OUTBOX_HABILITADO`:** com a integração desligada (padrão) o worker só mantém o
  heartbeat; os eventos ficam `PENDENTE`.
- **Commit por evento:** o worker confirma a reserva do lote e depois confirma cada envio/falha
  isoladamente, para que uma falha não desfaça os sucessos do lote.
- **`httpx` vira dependência de runtime** (o worker usa no `POST`); antes era só de dev.

**Consequências:** `OutboxRepository` ganhou `reservar_lote`/`marcar_enviado`/`registrar_falha`/
`listar`/`contar_por_status`/`reenfileirar`; novos `app/integrations/despacho.py`,
`services/outbox_service.py` e `controllers/admin_outbox.py` (`GET`/`POST /api/admin/outbox`, só
ADMIN). `pyproject`/`uv.lock` atualizados (httpx runtime) e imagens reconstruídas. Os testes de
despacho rodam a lógica reserva→enviar/falhar na mesma sessão porque a sessão de teste roda numa
transação isolada que um `FabricaSessao` separado (do worker) não enxergaria.

**Requisitos:** seção 9.2; testes `test_outbox_despacho`, `test_outbox_contrato`.

---

## 2026-10-17 — Canais externos: outbox transacional (F6.1)

**Contexto:** a F6 liga os canais e-mail e WhatsApp (seção 9). O primeiro recorte é a base durável,
sem SMTP/WAHA ainda (as credenciais de SMTP não foram fornecidas).

**Decisão:**
- **Outbox transacional (seção 9.2):** a mudança de estado e o evento de notificação externa são
  gravados na **mesma transação**. O `EventoService` continua criando a notificação de portal e
  passa a enfileirar linhas em `eventos_outbox` (e-mail/WhatsApp) conforme a **matriz 9.6**; o
  `worker` despacha ao n8n na F6.2. Com `OUTBOX_HABILITADO=false` (padrão), os eventos ficam
  `PENDENTE`.
- **Preferências por destinatário:** e-mail só com `notificar_email`; WhatsApp só com vínculo
  (`whatsapp_chat_id`) e opt-in (`whatsapp_opt_in`).
- **Textos no backend (seção 9.1/9.5):** `app/integrations/mensagens.py` monta o `payload` de cada
  mensagem (o n8n é só transporte). Minimização de dados (LGPD): protocolo, título, status e link; a
  solução é resumida a ≤ 300 caracteres.
- **`canal_origem` em `chamados`** (PORTAL/WHATSAPP, padrão PORTAL) para o bot abrir chamados na F6.4.

**Consequências:** migration `0006_canais_externos` (3 ENUMs, colunas em `usuarios`, `canal_origem`
em `chamados`, tabela `eventos_outbox` + índice parcial; downgrade com `DROP TYPE`). Nova entidade
`EventoOutbox`, `OutboxRepository` e o pacote `app/integrations`. `EventoService` ganhou `outbox` e
`portal_url` opcionais (injetados nas dependências). Config nova: `OUTBOX_HABILITADO`,
`N8N_WEBHOOK_NOTIFICACOES_URL`, `N8N_WEBHOOK_TOKEN`, `INTEGRACAO_API_KEY`.

**Requisitos:** seção 9 (9.2, 9.6); TU17 (`test_canais_externos`).

---

## 2026-10-17 — Front da Base de Conhecimento e `ArtigoCategoria` (F5.2)

**Contexto:** a F5.2 entrega a tela da Base de Conhecimento e os pontos de integração com os
chamados (RF06, UC04, FA01).

**Decisão:**
- **Tela em acordeão** com busca (debounce na URL, `?q=`) e filtro por categoria (`?categoria=`),
  seguindo o mesmo padrão da lista de chamados (estado na URL para o Voltar do navegador funcionar).
- **"Abrir chamado" pelo artigo** passa a categoria e o título por query string ao wizard
  (`/chamados/novo?categoria=&titulo=`); o `NovoChamadoPage` só aplica o prefill num rascunho vazio.
- **Publicar a partir do chamado** fica no detalhe, visível a ANALISTA/ADMIN quando há **solução
  aprovada** (a RN05 é reforçada no backend); o modal pré-preenche título (do chamado) e conteúdo
  (descrição da solução). Editar artigo também é de ANALISTA/ADMIN.
- **`ArtigoCategoria`:** o schema de saída da categoria do artigo chamava-se `CategoriaResumo` e
  colidia no OpenAPI com o de chamados (o `openapi-typescript` gerava nomes qualificados pelo módulo
  e o `tsc -b` quebrava). Renomeado para `ArtigoCategoria` no controller da base.

**Consequências:** `src/api/baseConhecimento.ts` novo; `BaseConhecimentoPage` reescrita;
`NovoChamadoPage` e `ChamadoDetalhePage` ganharam o prefill e o "Publicar na base". Schema do front
regenerado. O `npm run build` (`tsc -b`) entra no gate porque pega colisões que o `--noEmit` não
pega. Fecha a F5.

**Requisitos:** RF06, UC04, FA01, RN05 (front); testes `baseConhecimento.test`.

---

## 2026-10-17 — Base de Conhecimento: busca full-text e RN05 (F5.1)

**Contexto:** a F5 entrega a Base de Conhecimento (RF06, UC04). A F5.1 é o backend: busca full-text
e a publicação a partir de solução aprovada (RN05).

**Decisão:**
- **Busca full-text em PT-BR sem acento:** configuração `pt_br_unaccent` (cópia de `portuguese`,
  mapeamento por `unaccent` + `portuguese_stem`) e coluna gerada `busca` (`tsvector`, título peso A
  e conteúdo peso B) com índice GIN (migration 0005, exatamente o SQL da seção 5.4). Consulta por
  `busca @@ websearch_to_tsquery('pt_br_unaccent', :q)` ordenada por `ts_rank`.
- **Categoria do artigo por join:** a tabela `base_conhecimento` não guarda `id_categoria`; o filtro
  e a categoria exibida vêm do join `base → solucoes → chamados → categorias`.
- **RN05 (confirma B16):** publicar só a partir de uma **solução APROVADA** e no máximo **uma por
  solução** (UNIQUE `uq_base_conhecimento_solucao`). A escrita (publicar/editar) é de **ANALISTA/
  ADMIN** (router à parte com guard de perfil); a leitura é de qualquer autenticado.

**Consequências:** migration `0005_busca_base_conhecimento` com downgrade (remove índice, coluna e
a configuração de busca). A entidade `BaseConhecimento` passou a mapear a coluna gerada `busca`
(read-only). Novos arquivos: `repositories/base_conhecimento_repository.py`,
`services/base_conhecimento_service.py`, `controllers/base_conhecimento.py`. A tela (acordeão,
"abrir chamado", publicar pelo chamado) é a F5.2.

**Requisitos:** RF06, RN05, UC04 (parcial); TU15; decisão B16.

---

## 2026-10-17 — Ciclo de vida: solução, aprovação, follow-ups e PATCH usuário (F4.2)

**Contexto:** a F4.2 completa o ciclo de vida no backend (RF03): conclusão com solução (RN01),
aprovação/reprovação pelo solicitante (RN02), follow-ups e a edição/exclusão lógica de usuário.

**Decisão:**
- **RN01 (conclusão):** ATRIBUIDO → CONCLUIDO exige a **descrição da solução** (422 se vazia); só o
  **técnico responsável ou ADMIN**; a solução nasce `PENDENTE_APROVACAO` (índice único parcial
  garante no máximo uma pendente por chamado); preenche `data_conclusao`.
- **RN02 (aprovação):** só o **solicitante** responde. Aprovar → FECHADO + `data_fechamento` +
  solução `APROVADO`. Reprovar exige **motivo** (422 se vazio) → volta a ATRIBUIDO, solução
  `REJEITADO`, e o **motivo vira um follow-up**. **Sem encerramento automático** (confirma a decisão
  B13): FECHADO só com aprovação expressa.
- **Follow-ups:** participantes = solicitante, técnico responsável e ADMIN; não participante recebe
  `404` (não revela o chamado). Chamado **FECHADO** não aceita novo follow-up (`409`).
- **`PATCH /api/usuarios/{id}` (ADMIN):** edita nome/cargo/perfil/`ativo` (exclusão lógica por
  `ativo`, decisão B15). Salvaguarda de produto: o ADMIN **não desativa nem rebaixa a si mesmo**
  (evita lockout). Confirmar se deve também garantir "ao menos 1 admin ativo" — por ora, só a
  proteção do próprio usuário.
- **Resposta por id de solução:** `POST /api/solucoes/{id}/resposta` (router próprio `/api/solucoes`);
  o service localiza o chamado a partir da solução.

**Consequências:** sem migration nova (tabelas `solucoes`/`follow_ups` já existem desde a 0001).
Novos arquivos: `repositories/solucao_repository.py`, `repositories/follow_up_repository.py`;
`CicloVidaService` e `EventoService` estendidos; `UsuarioService.atualizar`. Eventos de portal:
`SOLUCAO_REGISTRADA`, `SOLUCAO_APROVADA`, `SOLUCAO_REJEITADA`.

**Requisitos:** RF03, RN01, RN02, UC03; TU11–TU14; decisões B13, B15.

---

## 2026-10-17 — Ciclo de vida: triagem e atribuição (F4.1)

**Contexto:** a F4 implementa o ciclo de vida do chamado (RF03). A F4.1 cobre as duas primeiras
transições (triagem e atribuição), a linha do tempo e a RN03.

**Decisão:**
- **Transições conforme a tabela 6.3** do prompt (confirma a decisão B14): triagem NOVO → PENDENTE
  (ANALISTA/ADMIN, pode ajustar categoria ativa e severidade); atribuição NOVO/PENDENTE/ATRIBUIDO →
  ATRIBUIDO. Qualquer outra → `409 TRANSICAO_INVALIDA`.
- **RN03:** o responsável precisa ser ANALISTA/ADMIN **ativo** (`RN03_TECNICO_INVALIDO`), além do
  CHECK `ck_chamados_rn03_tecnico` no banco. **ANALISTA só atribui a si mesmo**; ADMIN a qualquer
  técnico (seção 6.3).
- **Histórico (`historico_chamado`, migration 0004):** cada transição grava um evento
  (`status_anterior`/`status_novo`, autor, observação) e atualiza `data_atualizacao` na mesma
  transação. A **abertura** também passa a gravar o evento `NOVO`; a migration faz **backfill** de
  um `NOVO` por chamado existente, para a linha do tempo começar na criação. Adicionadas
  `chamados.data_conclusao`/`data_fechamento` (usadas na F4.2).
- **Notificações (canal Portal):** `STATUS_ALTERADO` (ao solicitante) e `CHAMADO_ATRIBUIDO` (ao
  técnico).
- **`GET /api/usuarios/tecnicos`** (ANALISTA/ADMIN ativos) fica num router próprio, sem o guard de
  ADMIN do `/api/usuarios`, e é declarado antes de `/{id}` para ter precedência de rota.

**Consequências:** migration `0004_ciclo_de_vida` com downgrade. Exclusão lógica por `ativo`
confirmada como padrão (B15): a inatividade de um técnico o remove dos elegíveis à atribuição.
A visão de fila do ANALISTA/ADMIN (B12) e o "sem encerramento automático" (B13, RN02) entram nas
F4.2/F4.3. Novos arquivos: `services/ciclo_vida_service.py`, `repositories/chamado_historico_repository.py`,
`entities/historico_chamado.py`, endpoints de triagem/atribuição/histórico/tecnicos.

**Requisitos:** RF03 (parcial), RN03, UC03 (parcial), TU09, TU10; decisões B14, B15.

---

## 2026-10-17 — Anexos: MinIO + StorageService, validação B9/B10 (F3.1)

**Contexto:** a F3.1 entrega o backend de anexos (RF02): guardar, listar e baixar arquivos de um
chamado. O prompt citava SeaweedFS, mas a decisão de infraestrutura já adotou **MinIO** (ADR da
F0.1). Faltava fixar o cliente S3, as validações e o desenho do armazenamento.

**Decisão:**
- **Armazenamento:** interface `StorageService` (`salvar`, `abrir_stream`, `remover`) e
  implementação `S3StorageService` com **boto3** apontando para o MinIO —
  `addressing_style="path"`, `signature_version="s3v4"` e checksums `when_required` (o MinIO recusa
  os checksums automáticos do boto3 ≥ 1.36). O binário vai para o bucket `mentory-anexos`; o banco
  guarda só os metadados. A API cria os buckets no **startup** (lifespan), de forma idempotente e
  resiliente (não derruba a API se o MinIO estiver fora; pulado em `AMBIENTE=test`). Trocar de
  provedor é só configuração. Dependências novas: `boto3`, `python-multipart` (uploads multipart).
- **Chave do objeto:** `chamados/{id_chamado}/{uuid4}.{ext}`; o nome original fica só no banco.
- **Validação (decisões B9/B10):** no máximo **5 anexos por chamado** e **10 MB** por arquivo
  (configuráveis em `.env`); tipos aceitos **PNG, JPEG e PDF**, conferidos por **magic bytes** — a
  API **não confia** no `Content-Type` nem na extensão enviados. `sha256` do conteúdo é gravado.
- **Escopo (RN06):** anexar/listar/baixar exige que o chamado esteja no escopo do perfil (CLIENTE
  só os seus); fora do escopo → `404` (não revela o chamado de outro). `escopo_solicitante` do
  `ChamadoService` passou a ser público e reutilizado pelo `AnexoService`.
- **Erros (seção 7.1):** tipo não permitido → `415 TIPO_ARQUIVO_INVALIDO`; grande/vazio →
  `413 ARQUIVO_GRANDE`; limite de anexos → `409 LIMITE_ANEXOS`; fora do escopo → `404`.

**Consequências:** migration `0003_anexos_notificacoes` (tabelas `anexos` e `notificacoes`, com os
CHECKs de mime/tamanho e o índice parcial de notificações não lidas) com downgrade. O serviço `api`
do Compose recebeu as variáveis S3. `mypy` ganhou override para `boto3`/`botocore` (sem stubs). As
notificações (tabela criada aqui) são preenchidas na F3.2; a tabela `anexos` já é usada.

**Requisitos:** RF02 (anexos), RN06, TU16; decisões B9 e B10.

---

## 2026-10-17 — Identidade visual herdada do esboço (ex-HelpFlow → Mentory)

**Contexto:** a identidade visual anterior (seção 8.2, "extraída das capturas do protótipo":
sidebar azul-marinho escuro, primária `#1B3F7E`, tipografia Outfit/Inter) foi considerada pelo
usuário com "cara de template de IA". O usuário forneceu um **esboço próprio** (coleção
"01 — Foundations", feito quando o app se chamava HelpFlow) com screenshot da paleta e um protótipo
HTML/CSS/JS, pedindo para seguir essa identidade e apenas trocar o nome para **Mentory**.

**Decisão:** adotar o design system do esboço como identidade do Mentory. Fonte da verdade da
identidade passa a ser a tela **"01 — Foundations"** do esboço (a screenshot prevalece sobre o CSS
do protótipo quando divergirem — ex.: `Secondary #475569` da Foundations, não o `#71808d` do CSS).
- **Marca teal/petróleo:** Brand 600 `#066873`, Brand 500 `#087F8C`.
- **Neutros/semânticas:** Canvas `#F8FAFC`, Surface `#FFFFFF`, Text `#0B1220`, Secondary `#475569`,
  Success `#16885B`, Warning `#C77700`, Danger `#D13B4A`, Info `#2563EB`.
- **Tipografia:** IBM Plex Sans (no lugar de Outfit/Inter). Mono: IBM Plex Mono para protocolo.
- **Forma:** sidebar **branca** (item ativo em pílula teal), superfícies com borda de 1px, raios
  `6·10·14·20·full`, espaço `4..64`, ícones `16·20·24` (lucide), breakpoints `390/768/1440`.
- **Tema claro e escuro:** o escuro é derivado da mesma paleta teal (o esboço cita a coleção
  "Color Dark"). Alternância por `data-theme`/`prefers-color-scheme`, com persistência.
- **Nome:** "HelpFlow" → "Mentory" (mantido o ponto do logotipo: "Mentory.").

**Assistente de IA/RAG:** é a **visão final do produto** (confirmado pelo usuário em 17/10/2026) e
fica **preservado na identidade** — item de menu "Assistente IA", hero conversacional e card de
apoio. A **implementação é de fase futura**: o **núcleo de chamados vem primeiro**. Até lá, a
entrada de IA aparece marcada como "em breve"/desabilitada. Não é mais "fora de escopo".

**Consequências:** a **seção 8.2** do prompt foi reescrita com os tokens das Foundations e a
**seção 6.1** teve as cores de badge alinhadas à paleta (Info/Warning/Success/Danger/Secondary).
A seção 8.4 passou a descrever o painel do Login na cor da marca e a entrada de IA como fase futura.
O resíduo em `frontend/` (tokens Outfit/Inter antigos, item C1 de `DECISOES_PENDENTES.md`) **será
refeito** na F0.5 com a nova identidade. Protótipo de referência (claro+escuro) em
`docs/design/mentory/index.html`; material do esboço em `docs/design/exploracao/`. Fontes a trocar
no front: `@fontsource/outfit`+`inter` → `@fontsource/ibm-plex-sans` (+ `ibm-plex-mono`).

**Requisitos:** RNF03 (responsividade/identidade), seções 8.2, 8.3, 8.4 e 6.1 do prompt.

---

## 2026-10-17 — Cadastro de usuários, config pública e criar-admin (F1.2)

**Contexto:** a F1.2 fecha a parte de backend do cadastro de usuários (UC01, RF01, RN07), expõe a
configuração pública da tela de login (`GET /api/config/publica`) e cria o primeiro administrador
(`make criar-admin`), conforme as seções 5.7, 7.1, 7.2 e 11 do prompt.

**Decisão:**
- **Só ADMIN cadastra/lista/consulta usuários** (decisão B1): as rotas `/api/usuarios` têm a
  dependência `exigir_perfil(ADMIN)` no router inteiro. Não há auto-cadastro. Sem token → `401`;
  perfil errado → `403` (TU07).
- **RN07 / TU05:** o e-mail é único e normalizado em minúsculas. O `UsuarioService.cadastrar`
  checa a duplicidade antes de inserir e devolve `409 EMAIL_DUPLICADO` (com `campos.email`); o
  `UNIQUE uq_usuarios_email` continua como última barreira. Diferença só de caixa também é
  duplicidade.
- **TU06:** a validação de força da senha (8..72 bytes) fica no service, reaproveitando
  `core/seguranca.gerar_hash_senha`; senha fraca → `422 VALIDACAO`. A senha nunca é devolvida nem
  persistida em claro (só o hash BCrypt `$2b$`).
- **Paginação (seção 7.1):** `GET /api/usuarios` aceita `q` (nome/e-mail), `perfil`, `ativo`,
  `page` (≥1) e `page_size` (1..50, padrão 10) e responde no envelope
  `{ items, total, page, page_size }`, ordenando por nome e id.
- **Config pública:** `GET /api/config/publica` é público e devolve
  `{ whatsapp_suporte, email_suporte, google_sso, versao }`. `google_sso` deriva de
  `GOOGLE_CLIENT_ID` existir (Fase 7); `versao` vem de `app.__version__` (fonte única, também no
  OpenAPI). Nenhum segredo é exposto.
- **`make criar-admin`:** `python -m app.cli criar-admin` (Typer) lê `ADMIN_NOME/EMAIL/SENHA` do
  `.env` e é **idempotente** — se já existe usuário com aquele e-mail, não recria nem troca a
  senha. A lógica foi isolada em `criar_admin_na_sessao(sessao, config)` para ser testável sem
  terminal nem `commit`.

**Consequências:** sem migration nova (o esquema de `usuarios` já existe desde a `0001`). O serviço
`api` do Compose passou a receber as variáveis de autenticação, de config pública e do admin para
que a API em container e o `make criar-admin` funcionem. `app.__version__` subiu para `0.1.0`.
Camadas novas: `services/usuario_service.py`, `controllers/usuarios.py`, `controllers/config.py`,
`controllers/schemas_usuarios.py` e `app/cli.py`; o `UsuarioRepository` ganhou `existe_email`,
`criar` e `listar`.

**Requisitos:** RF01, RN06, RN07, UC01, TU05, TU06, TU07.

---

## 2026-10-17 — Autenticação (F1.1): tokens, hashing e dependências

**Contexto:** a F1.1 entrega o backend de autenticação (login, refresh, logout, `me`, troca de
senha e limite de tentativas), conforme as seções 7.2, 7.3 e 11 do prompt. Faltava escolher as
bibliotecas e fixar o desenho do refresh token.

**Decisão:**
- **Senha:** BCrypt pela biblioteca `bcrypt` (custo `BCRYPT_CUSTO`, padrão 12; 4 nos testes),
  mínimo de 8 caracteres e máximo de 72 bytes (TU06). O prompt menciona `bcrypt` 5.x, mas foi
  fixada a linha **4.x** (`>=4.2,<5`, resolvida 4.3.0): a API usada (`hashpw`/`gensalt`/`checkpw`)
  é estável entre 4.x e 5.x e a 4.x está amplamente disponível para ARM64. Revisitar ao atualizar.
- **Access token:** JWT **HS256** (PyJWT), `JWT_SECRET` ≥ 32 bytes, claims `sub`, `perfil`,
  `iat`, `exp`, `jti`. O usuário é recarregado do banco a cada requisição e recusado se inativo.
- **Refresh token:** opaco (256 bits), entregue em cookie `HttpOnly`, `SameSite=Strict`,
  `Path=/api/auth`, `Secure` só em produção; o banco guarda apenas o **SHA-256** (`CHAR(64)`).
  Rotação a cada uso dentro de uma `familia` (UUID); o reuso de um token já revogado derruba a
  família inteira. A troca de senha revoga todas as sessões do usuário.
- **Limite de tentativas (RNF01):** 5 por IP e por e-mail em 15 min, no Redis (`rl:login:*`),
  com TTL; ao estourar, `429 MUITAS_TENTATIVAS`. Estado efêmero, coerente com a seção 5.5.
- **CORS:** habilitado só em desenvolvimento (`CORS_ORIGINS`); em produção, front e API têm a
  mesma origem.
- **Mensagem genérica no login (FE01):** e-mail inexistente, senha errada e usuário inativo
  devolvem a mesma resposta `401` ("E-mail ou senha inválidos.").

**Consequências:** migration `0002_autenticacao` cria `tokens_refresh` (FK `ON DELETE RESTRICT`,
`token_hash` único, índices por família e por usuário) com `downgrade()` completo. Novas
dependências: `pyjwt`, `bcrypt`, `email-validator` (para `EmailStr`). Observação de teste: o
`email-validator` rejeita o TLD reservado `.test`; os dados fictícios usam `.com`/`.com.br`.
Cadastro de usuário, `make criar-admin` e `/api/config/publica` ficam para a F1.2.

**Requisitos:** RF01 (parcial), RN06, RN07 (parcial), RNF01, UC01 (parcial), FE01, TU06, TU07.

---

## 2026-10-17 — Esquema inicial (migration 0001) e diferenças em relação ao Documento 02

**Contexto:** a F0.3 cria o banco. O dicionário de dados do Documento 02 precisava de
ajustes para atender aos requisitos (RN03, RN04, RNF02), ao protótipo e à exclusão lógica,
e faltava escolher a ferramenta de migration.

**Decisão:** o esquema é criado **só por migration Alembic** (`0001_esquema_inicial`), que
reproduz exatamente o SQL da seção 5.2. O Alembic é a ferramenta de migration do projeto
(sync + psycopg 3); a `DATABASE_URL` vem de `app.core.config`, não do `alembic.ini`. A API
nunca aplica migration na partida — quem aplica é o serviço `migrate` (`make migrate`), do
qual `api` e `worker` dependem (`service_completed_successfully`). As diferenças adotadas em
relação ao Documento 02 (seção 5.3 do prompt):

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

**Consequências:** os 4 tipos ENUM (`perfil_usuario`, `severidade_chamado`, `status_chamado`,
`status_aprovacao`) são criados e removidos explicitamente na migration (`create_type=False`
nas colunas), para o `downgrade()` ser completo (inclui `DROP TYPE`, `DROP FUNCTION` e
`DROP EXTENSION`). FKs com `ON DELETE RESTRICT`: usuários e chamados nunca são apagados. O
`protocolo` é coluna gerada e somente leitura (`Computed(persisted=True)`); a busca por título
usa `f_unaccent(lower(titulo))`, idêntica à do índice trigram. A ida e volta
(`upgrade head → downgrade base → upgrade head`) foi validada em PostgreSQL real.

**Requisitos:** RN03 (CHECK), RN04, RN07 (UNIQUE), RNF02 (índices e busca sem acento).

---

## 2026-10-16 — Portas de desenvolvimento só em 127.0.0.1, fora das já usadas no servidor

**Contexto:** o prompt sugere 5432, 8000, 8080 e 8333 no host. No servidor Oracle, 5432 (PostgreSQL
do GRH), 8080, 8090 (GRH) e 9000/9001 (MinIO do GRH) já estão ocupadas, e o `AGENTS.md` do servidor
proíbe expor portas na internet.

**Decisão:** portas configuráveis no `.env`, publicadas só no `docker-compose.override.yml` e sempre
em `127.0.0.1`: PostgreSQL 5442, MinIO 9100 (S3) e 9101 (console), Mailpit 8125 (UI) e 1125
(SMTP). API (8100) e web (8180) seguem o mesmo padrão quando entrarem. Acesso de fora do servidor
por túnel SSH ou pelo encaminhamento de portas do VS Code.

**Consequências:** o `docker-compose.yml` base não publica porta nenhuma; produção (F7) usa o
Traefik. Os serviços conversam pelos nomes na rede interna (`db:5432`, `s3:9000`).

**Requisitos:** RNF01.

## 2026-10-16 — MinIO no lugar do SeaweedFS

**Contexto:** a seção 2 do prompt proíbe o MinIO porque o Community Edition parou de publicar
imagens e teve o repositório arquivado. O grupo prefere o MinIO, que já conhece (é usado no GRH),
e o projeto é acadêmico.

**Decisão:** serviço `s3` com MinIO RELEASE.2026-09-22, imagem do Chainguard
(`cgr.dev/chainguard/minio`) fixada **por digest**: as imagens oficiais não existem mais no Docker
Hub nem no Quay, e o Chainguard só publica a tag `latest`. Healthcheck com `mc ready local`. O
nome do serviço (`s3`) e as variáveis `S3_*` continuam genéricos; `S3_ACCESS_KEY` e
`S3_SECRET_KEY` viram o usuário e a senha raiz do MinIO. O `infra/seaweedfs/entrypoint.sh` do
prompt deixa de existir.

**Consequências:** o código (F3) usa só a API S3 via boto3, então voltar ao SeaweedFS, ou usar
Garage ou AWS S3, continua sendo só configuração. Atualizar o MinIO é trocar o digest de propósito
e registrar aqui. Licença do MinIO: AGPLv3, sem obrigação enquanto não for modificado.

**Requisitos:** RF02 (anexos, F3).
