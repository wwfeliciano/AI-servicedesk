# WAHA — WhatsApp HTTP API (F6)

O WAHA mantém a sessão do WhatsApp (QR code), envia e recebe mensagens. Entrega os
eventos ao n8n por webhook; o n8n chama a API, que roda o bot (seção 9.3).

Licença: imagem **pública gratuita** (Apache-2.0). A tag fixada é a ARM
(`devlikeapro/waha:arm-2026.4.3`) porque o servidor é ARM64; em outra arquitetura,
use a tag correspondente da mesma versão.

## Serviço

Sobe com a stack. Em dev, a API/dashboard ficam em `http://127.0.0.1:3000`
(`PORTA_WAHA`). Em produção **não** há porta publicada (exposição pelo Traefik exige
autorização). Sessões persistem no volume `waha_data`.

## Variáveis (.env)

| Var | Uso |
|---|---|
| `WAHA_API_KEY` → `WHATSAPP_API_KEY` | chave da API do WAHA (header `X-Api-Key`) |
| `WAHA_DASHBOARD_USERNAME` / `WAHA_DASHBOARD_PASSWORD` | login do dashboard |
| `WHATSAPP_SWAGGER_USERNAME` / `WHATSAPP_SWAGGER_PASSWORD` | login do Swagger |
| `WHATSAPP_DEFAULT_ENGINE` | engine (padrão `WEBJS`) |
| `WHATSAPP_HOOK_URL` | webhook dos eventos → `http://n8n:5678/webhook/waha-eventos` |
| `WHATSAPP_HOOK_EVENTS` | eventos assinados: `message,session.status` |

## Iniciar a sessão (QR)

1. Abra o dashboard em `http://127.0.0.1:3000` (ou o Swagger `/swagger`) e autentique.
2. Inicie a sessão `default` (`POST /api/sessions/start` com `{"name":"default"}`).
3. Leia o **QR code** (`GET /api/default/auth/qr`) com o WhatsApp do **número
   dedicado** de suporte (o mesmo `WHATSAPP_NUMERO_SUPORTE` do `.env`, usado no link
   `wa.me` do vínculo).
4. Quando a sessão ficar `WORKING`, o WAHA passa a receber e enviar mensagens.

O status da sessão (`session.status`) é repassado pelo n8n a
`POST /api/integracoes/whatsapp/sessao`, e aparece em `/admin/integracoes`.

## Número dedicado

Use um número **exclusivo** para o atendimento (não o WhatsApp pessoal). O primeiro
contato parte sempre do usuário (fluxo de vínculo `VINCULAR <código>`), o que reduz o
risco de bloqueio. Não registre o número, `chat_id` ou tokens em logs, testes ou
commits.

> Segurança (servidor): sem portas publicadas na internet sem autorização; limites
> de CPU/memória no compose; nada de `docker.sock` no container.
