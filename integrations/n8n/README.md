# n8n — automação dos canais externos (F6)

O n8n é **transporte**, não regra: ele recebe webhooks, filtra eventos, chama a API
e entrega mensagens pelo WAHA (WhatsApp) e por SMTP (e-mail). As regras, os textos e
o estado da conversa ficam no backend (seção 9.1 do prompt).

## Serviço

Sobe junto com a stack (`docker-compose.yml`), usando o Postgres do projeto (banco e
usuário criados por `infra/postgres/init/01-n8n.sh` na primeira subida do volume
`pg_data`). Em dev, a interface fica em `http://127.0.0.1:5678` (porta do
`docker-compose.override.yml`). Em produção **não** há porta publicada: a exposição
pelo Traefik exige autorização (ver `/home/ubuntu/AGENTS.md`).

Licença: edição **Community** (Sustainable Use License). Não usar recursos
Enterprise (Variables, SSO, Source Control/Environments, External Secrets, Log
Streaming) — ver seção 3 do prompt.

## Variáveis (.env)

| Var | Uso |
|---|---|
| `N8N_DB_NAME` / `N8N_DB_USER` / `N8N_DB_PASSWORD` | banco do n8n no Postgres do projeto |
| `N8N_ENCRYPTION_KEY` | chave de criptografia das credenciais do n8n (`openssl rand -hex 32`) |
| `N8N_HOST` / `N8N_PROTOCOL` / `WEBHOOK_URL` | host/URL pública dos webhooks |
| `N8N_WEBHOOK_TOKEN` | header `X-Mentory-Token` que o worker envia ao webhook de notificações |
| `INTEGRACAO_API_KEY` | header `X-Integracao-Chave` que o n8n envia à API |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USUARIO` / `SMTP_SENHA` / `SMTP_REMETENTE` | e-mail (em dev, Mailpit) |

## Workflows (`workflows/`)

Exportados **sem credenciais** (as credenciais do SMTP são cadastradas na UI do n8n,
por nome; os tokens vêm das variáveis de ambiente do serviço). Importe em
*Workflows → Import from File*.

- **`notificacoes.json`** — saída. Recebe `POST /webhook/helpdesk-notificacoes` do
  `worker` (outbox), valida o `X-Mentory-Token`, remove `id_evento` repetido
  (idempotência) e roteia por `canal`: `WHATSAPP` → `WAHA /api/sendText`; `EMAIL` →
  nó *Send Email* (credencial SMTP).
- **`waha-eventos.json`** — entrada. Recebe `POST /webhook/waha-eventos` do WAHA,
  descarta `fromMe`/grupos, chama `POST /api/integracoes/whatsapp/mensagens` (com
  `X-Integracao-Chave`) e devolve cada resposta do bot pelo WAHA. Em produção,
  inserir `startTyping` → espera 1–3 s → `sendText` → `stopTyping` (anti-bloqueio).

## Primeira configuração

1. Suba a stack e abra `http://127.0.0.1:5678`; crie o usuário local (owner).
2. Cadastre a credencial **SMTP** (host/porta pelo `.env`; em dev, Mailpit em
   `mailpit:1025`). Não cadastre segredos nos arquivos de workflow.
3. Importe os dois workflows e ligue-os (*Active*).
4. Ligue o despacho do outbox: `OUTBOX_HABILITADO=true` no `.env` e recrie `worker`.

> Segurança (servidor): sem portas publicadas na internet sem autorização; limites
> de CPU/memória definidos no compose; nada de `docker.sock` no container.
