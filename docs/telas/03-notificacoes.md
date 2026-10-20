# 03 — Notificações

Tela da F3.3, na identidade teal. Descreve o comportamento atual; o planejado fica na seção 8.4 do
prompt.

## Notificações (`/notificacoes`)

- Lista as notificações do usuário, **não lidas em destaque** (fundo teal-claro e um ponto);
  mostra o título, a mensagem e o tempo relativo.
- Cabeçalho indica quantas estão não lidas; o botão "Marcar todas como lidas" some quando não há
  nenhuma.
- **Clicar numa notificação** marca como lida e, se houver chamado associado, abre o detalhe dele.
- Tipos atuais: `CHAMADO_CRIADO` (confirmação ao solicitante) e `CHAMADO_URGENTE` (alerta aos
  analistas/admin quando o chamado é crítico). O ícone do urgente usa a cor de perigo.
- Estados de carregando e vazio ("Você não tem notificações.").

## Contador no menu

- O item "Notificações" do menu lateral mostra um **badge** com o número de não lidas. O contador é
  atualizado por **polling a cada 30 s** (decisão B11) e também logo após marcar notificações como
  lidas (invalidação do cache).
