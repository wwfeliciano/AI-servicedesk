# Decisões pendentes (do usuário)

Este arquivo reúne o que **depende de decisão sua** para as próximas fases, além de resíduos de
tentativas anteriores que precisam de um destino. É o complemento de:

- [DECISOES.md](DECISOES.md): decisões já tomadas e implementadas (ADR);
- [DEVELOPMENT_STATUS.md](DEVELOPMENT_STATUS.md), seção "Decisões aprovadas, ainda não
  implementadas": decisões já aprovadas, aguardando código.

Por que existe: pela regra do projeto (`AGENTS.md`, seções 1 e 2), o trabalho é feito **um recorte
por vez**, e **decisão que muda entidade, permissão, regra de negócio ou fonte da verdade é do
usuário**. O agente para na fronteira de cada fase e traz estas perguntas em vez de inventar
requisito.

> Para a maioria dos itens já existe um **padrão adotado** na seção 14 do prompt
> (`PROMPT_IMPLEMENTACAO.md`): se você não decidir diferente, seguimos esse padrão. Marque abaixo o
> que quer mudar.

Legenda de estado: ⏳ aguardando você · ✅ decidido (migrar para `DECISOES.md` quando virar código).

---

## A. Processo e infraestrutura (transversal)

| # | Decisão | Padrão / situação atual | Estado |
|---|---|---|---|
| A1 | **Avançar de fase.** A cada fronteira de recorte, o agente para. Avançar F1→F2→… é um "ok" seu a cada vez. | Um recorte por vez (AGENTS.md §1). Você autoriza o próximo. | ⏳ |
| A2 | **Remoto do GitHub.** Qual repositório, quando autenticar e quando dar push. | Repositório **público**, **GitHub Pro**, sem credenciais no código. Versionamento **local** por enquanto; push só com sua autorização a cada vez. | ⏳ |
| A3 | **F0.5 (front-end base).** Quando retomar; e o que fazer com o `frontend/` já começado (ver seção C). | **Adiada** a pedido seu (17/10/2026). A F0 só fecha quando ela voltar. | ⏳ |
| A4 | **Rebuild da imagem `api`.** A imagem em execução é anterior à F1.1. | Testes rodam no host com `uv` e passam; a API do Compose não reflete as rotas novas até o rebuild. | ⏳ |

## B. Decisões por fase (seção 14 do prompt — padrões já adotados)

Estes padrões valem automaticamente, mas mexem em regra de negócio/permissão, então ficam
registrados para você confirmar ou mudar **antes** da fase correspondente.

### F1 — Autenticação e cadastro (restante: F1.2, F1.3)

| # | Decisão | Padrão adotado | Estado |
|---|---|---|---|
| B1 | **Quem cadastra usuários.** | Só **ADMIN** cria usuários (`POST /api/usuarios`); não há auto-cadastro (UC01). | ⏳ |
| B2 | **Primeiro administrador.** | `make criar-admin` lê `ADMIN_NOME/EMAIL/SENHA` do `.env`. Confirmar nome/e-mail reais do admin inicial (sem senha real no Git). | ⏳ |
| B3 | **Login com Google Workspace.** | **Opcional**, só para usuários já cadastrados, e só na **F7**. Confirmar se entra no escopo. | ⏳ |
| B4 | **Perfis e rótulos de tela.** | `ADMIN`, `ANALISTA`, `CLIENTE` (dicionário de dados). Confirmar os rótulos exibidos ao usuário. | ⏳ |

### F2 — Abertura e consulta de chamados

| # | Decisão | Padrão adotado | Estado |
|---|---|---|---|
| B5 | **Significado de `PENDENTE`.** | "Triado, aguardando atribuição" (no protótipo aparece como "Aberto"). | ⏳ |
| B6 | **Quem abre chamado.** | Qualquer perfil, **sempre para si**. Abrir em nome de outra pessoa fica fora do escopo. | ⏳ |
| B7 | **Indicador "Resolvidos".** | Conta só `CONCLUIDO`; `FECHADO` vai em "Encerrados". | ⏳ |
| B8 | **Ícones das categorias.** | Emojis no banco (como no protótipo). Alternativa: nomes de ícones `lucide`. | ⏳ |

### F3 — Anexos e notificações

| # | Decisão | Padrão adotado | Estado |
|---|---|---|---|
| B9 | **Limite de anexos.** | Até **5 por chamado**, **10 MB** cada (configurável em `.env`). | ✅ (F3.1) |
| B10 | **Tipos de arquivo aceitos.** | `image/png`, `image/jpeg`, `application/pdf` (validado por magic bytes). | ✅ (F3.1) |
| B11 | **Notificações "em tempo real".** | Consulta a cada **30 s** (polling). SSE fica como melhoria futura. | ⏳ |

### F4 — Ciclo de vida do chamado

| # | Decisão | Padrão adotado | Estado |
|---|---|---|---|
| B12 | **Visão do ANALISTA.** | Vê **todos** os chamados (fila), com filtros "Atribuídos a mim" e "Sem responsável". Alternativa: só os seus e os sem responsável. | ⏳ |
| B13 | **Encerramento automático.** | **Não existe**: FECHADO exige aprovação expressa do solicitante (RN02). | ✅ (F4.2) |
| B14 | **Transições de status válidas.** | Conforme a tabela 6.3 do prompt. Confirmar se o fluxo desejado é exatamente esse. | ✅ (F4.1, tabela 6.3) |
| B15 | **Exclusão de usuário/chamado.** | **Lógica** (coluna `ativo`); nunca apagar (FKs `ON DELETE RESTRICT`). | ✅ (F4.1) |

### F5 — Base de Conhecimento

| # | Decisão | Padrão adotado | Estado |
|---|---|---|---|
| B16 | **Origem dos artigos.** | Só a partir de **solução aprovada** (RN05); publicação por ANALISTA/ADMIN. | ✅ (F5.1) |

### F6 — Canais externos (e-mail e WhatsApp, n8n + WAHA)

| # | Decisão | Padrão adotado | Estado |
|---|---|---|---|
| B17 | **Habilitar o outbox/integrações.** | `OUTBOX_HABILITADO=false` por padrão. Depende de número dedicado do WhatsApp Business e segredos. | ⏳ |
| B18 | **Consentimento/opt-in do WhatsApp (LGPD).** | Opt-in explícito e registrado; opt-out a qualquer momento. Confirmar texto e política. | ⏳ |
| B19 | **Dados de suporte expostos na tela de login.** | `WHATSAPP_NUMERO_SUPORTE`, `EMAIL_SUPORTE`. Confirmar os valores reais (fora do Git). | ⏳ |

### F7 — Complementos e produção

| # | Decisão | Padrão adotado | Estado |
|---|---|---|---|
| B20 | **Metas de SLA.** | CRITICO 4 h · ALTA 8 h · MEDIA 24 h · BAIXA 72 h (horas corridas), ajustáveis em `sla_politicas`. Horário comercial fica para depois. | ✅ (F7.2) |
| B21 | **Redefinição de senha por e-mail (FA02).** | Entra na F7 (`esqueci-senha`/`redefinir-senha`). Confirmar remetente e expiração do token. | ⏳ |
| B22 | **Produção/HTTPS.** | Traefik v3 + Let's Encrypt, cookie `Secure`, `/api/docs` desligado. Depende de domínio e rede do Traefik (regras do servidor). | ⏳ |

### F8 — Assistente de IA (Mentory AI, RAG)

| # | Decisão | Padrão adotado | Estado |
|---|---|---|---|
| B23 | **Provedor e modelo padrão.** | OpenAI-compatible apontando para a **API Gemini** (`generativelanguage.googleapis.com`), modelo da camada gratuita; cadeia de fallback configurável em `/admin/ia`. Confirmar provedor/modelo e se outros entram (Groq, OpenRouter, Ollama local). | ⏳ |
| B24 | **Chave(s) do provedor de IA.** | `GOOGLE_AI_API_KEY` (ou equivalente), cifrada no banco, nunca no Git/log. **Bloqueador:** sem a chave não dá para validar a geração ponta a ponta. | ⏳ |
| B25 | **Escopo e permissões da IA.** | A IA é um canal: abrir/consultar/responder chamado passa pelos services e pelas permissões do usuário (RN04/RN06). Confirmar quais ferramentas a IA pode usar por perfil. | ⏳ |
| B26 | **RAG e embeddings.** | RAG sobre a Base de Conhecimento; em dev, _fallback_ para o full-text da F5 (sem servidor de embeddings). Confirmar se haverá serviço de embeddings (ex.: TEI) e o modelo. | ⏳ |
| B27 | **Retenção e privacidade (LGPD).** | Guardar o mínimo da conversa (`ia_conversas`/`ia_mensagens`) e as métricas de token (`ia_uso`); respostas citam a fonte. Confirmar prazo de retenção e se o conteúdo da conversa pode ser logado (padrão: não). | ⏳ |
| B28 | **Custo/limites.** | Preferir camada gratuita + fallback; teto de `max_output_tokens` e de rodadas de ferramenta. Confirmar limites de custo e se haverá cota por usuário. | ⏳ |

## C. Resíduos de tentativas anteriores (precisam de destino)

Encontrados **não rastreados** no Git (branch `develop`), de uma execução anterior que foi
interrompida ao fechar o SSH (o processo não estava em tmux/nohup e recebeu `SIGHUP`). **Nada foi
commitado nem apagado** — aguardam sua decisão.

| # | Item | O que é | Opções | Estado |
|---|---|---|---|---|
| C1 | `frontend/` | Começo de SPA (Vite + React + Tailwind): componentes, stores, `api/`, `types/`, configs. Material da **F0.5**, incompleto e não validado. | **(b) refazer na F0.5** com a nova identidade (ADR 2026-10-17 — identidade do esboço): tokens Outfit/Inter antigos serão trocados por IBM Plex Sans e a paleta teal. | ✅ |
| C2 | `.kiro/` | Configurações do Kiro (`settings/lsp.json`, `agents/`). Não é código do produto. | (a) manter local e ignorar no Git (`.gitignore`); (b) versionar settings compartilháveis; (c) remover. | ⏳ |

> Sugestão (não decisão): tratar `.kiro/` no `.gitignore` e revisar `frontend/` só quando a F0.5
> for retomada, comparando com os tokens da seção 8.2 e o protótipo antes de reaproveitar.

---

## Como usar

1. Percorra a seção **B** antes de iniciar cada fase e me diga o que muda em relação ao padrão.
2. Resolva a seção **A** (processo/infra) quando quiser — A2 (GitHub) e A3 (F0.5) estão abertas.
3. Decida a seção **C** (resíduos) a qualquer momento.

Quando um item virar código, ele sai daqui e entra em `DECISOES.md` como ADR.
