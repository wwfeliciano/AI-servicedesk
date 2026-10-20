# Histórico de mudanças de comportamento

Registro do que **mudou para quem usa o sistema**, com o commit de cada mudança. Só entra o que
altera o que a tela faz. Mais recente primeiro.

---

## 2026-10-18 — F7.2 — SLA do mês no Dashboard

- **Tela:** Dashboard (`/dashboard`).
- **O que mudou para quem usa:** o Dashboard ganhou o cartão **"SLA do mês"**, com o percentual de
  chamados concluídos no mês **dentro do prazo** (barra de progresso e "N de M no prazo"). O prazo
  vem das metas por severidade (CRITICO 4 h · ALTA 8 h · MEDIA 24 h · BAIXA 72 h), gravadas na
  abertura de cada chamado.
- **Commit:** (a registrar no commit da F7.2).

---

## 2026-10-18 — F7.1 — Esqueci minha senha

- **Telas:** Login (`/login`), **Esqueci minha senha** (`/esqueci-senha`) e **Redefinir senha**
  (`/redefinir-senha`).
- **O que mudou para quem usa:** o Login ganhou o link **"Esqueci minha senha"**. Nele, o usuário
  informa o e-mail e recebe um link (válido por 30 min) para criar uma nova senha. A mensagem é
  sempre a mesma — exista o e-mail ou não — para não revelar quem tem conta. Pelo link, define a
  nova senha; links inválidos ou já usados são recusados.
- **Commit:** (a registrar no commit da F7.1).

---

## 2026-10-18 — F6.4b — Bot guiado e Integrações (ADMIN)

- **Telas/canais:** atendimento pelo WhatsApp (bot) e nova tela **Integrações** (`/admin/integracoes`).
- **O que mudou para quem usa:** pelo WhatsApp, o usuário abre um chamado **passo a passo**
  (categoria → prioridade → título → descrição → confirmar) e pode **aprovar/reprovar a solução** na
  conversa (`APROVAR/REPROVAR TK-0051` ou `1`/`2` após consultar o chamado). O ADMIN ganhou a tela
  **Integrações**, com o status da sessão do WhatsApp e a fila de envios externos (pendentes,
  enviados e falhas, com opção de **reenviar**).
- **Commit:** (a registrar no commit da F6.4b).

---

## 2026-10-17 — F6.3 — Vínculo do WhatsApp no Perfil

- **Tela:** Perfil (`/perfil`).
- **O que mudou para quem usa:** a tela de Perfil ganhou a seção **WhatsApp**. Marcando o
  consentimento e clicando em "Vincular WhatsApp", o usuário vê um **código**, um **link para abrir
  o WhatsApp** e um **QR code**; a tela fica aguardando a confirmação (consulta a cada 3 s). Depois
  de vinculado, aparece o número e o botão **Desvincular**. Há também as preferências de receber
  notificações por e-mail e por WhatsApp (a de WhatsApp só habilita quando há vínculo).
- **Commit:** (a registrar no commit da F6.3).

---

## 2026-10-17 — F5.2 — Base de Conhecimento no front (fecha a F5)

- **Telas:** Base de Conhecimento (`/base-conhecimento`), Novo Chamado e Detalhe do chamado
  ([02-chamados.md](02-chamados.md)).
- **O que mudou para quem usa:** a Base de Conhecimento deixa de ser um placeholder — qualquer
  usuário pesquisa por palavra-chave (sem acento), filtra por categoria e abre os artigos em
  acordeão. Dentro de um artigo há o atalho "Não resolveu? Abrir chamado", que leva ao wizard já com
  a categoria e o título preenchidos. ANALISTA/ADMIN podem editar um artigo e, na tela de um chamado
  com solução aprovada, publicar essa solução como artigo da base.
- **Commit:** (a registrar no commit da F5.2).

---

## 2026-10-17 — F4.3 — Ciclo de vida no front (fecha a F4)

- **Telas:** Detalhe do chamado, Meus Chamados/Chamados e `/admin/usuarios`
  ([02-chamados.md](02-chamados.md), [01-acesso.md](01-acesso.md)).
- **O que mudou para quem usa:** o técnico passa a triar, atribuir e registrar a solução pela tela
  do chamado; o solicitante aprova ou reprova a solução (com motivo); todos acompanham a linha do
  tempo e trocam mensagens. ANALISTA/ADMIN veem a fila ("Chamados") com o solicitante no card. O
  ADMIN edita e ativa/desativa usuários em `/admin/usuarios`.
- **Commit:** (a registrar no commit da F4.3).

---

## 2026-10-17 — F3.3 — Anexos e Notificações (fecha a F3)

- **Telas:** `/notificacoes` ([03-notificacoes.md](03-notificacoes.md)) e anexos no Novo Chamado e
  no Detalhe ([02-chamados.md](02-chamados.md)).
- **O que mudou para quem usa:** passou a ser possível anexar arquivos (PNG/JPG/PDF até 10 MB, até
  5 por chamado) ao abrir o chamado e na tela dele, com download; e há uma tela de Notificações com
  as não lidas em destaque, "marcar todas como lidas" e um contador no menu que atualiza sozinho a
  cada 30 s.
- **Commit:** (a registrar no commit da F3.3).

---

## 2026-10-17 — F2.4 — Telas de chamados (Dashboard, Novo Chamado, Meus Chamados, Detalhe)

- **Telas:** `/dashboard`, `/chamados`, `/chamados/novo`, `/chamados/:id` (ver
  [02-chamados.md](02-chamados.md)).
- **O que mudou para quem usa:** o Dashboard passou a mostrar indicadores reais, alerta de
  urgentes e chamados recentes; a pessoa abre um chamado num assistente de 3 etapas e recebe o
  protocolo; "Meus Chamados" tem busca em tempo real, abas com contadores, filtro por categoria,
  paginação (com filtros na URL) e abre o detalhe de cada chamado. O CLIENTE vê só os seus.
- **Commit:** (a registrar no commit da F2.4).

---

## 2026-10-17 — F1.3 — Telas de acesso (Login, Perfil, /admin/usuarios)

- **Telas:** `/login`, `/perfil`, `/admin/usuarios` (ver [01-acesso.md](01-acesso.md)).
- **O que mudou para quem usa:** o portal passou a ter login real (sessão restaurada ao reabrir),
  logout, troca de senha no Perfil e, para ADMIN, cadastro e listagem de usuários com busca e
  filtro. Erros aparecem de forma clara: credenciais inválidas em mensagem genérica (FE01), e-mail
  duplicado e senha fraca no campo. Rotas passam a respeitar o perfil.
- **Commit:** (a registrar no commit da F1.3).

---

_As telas vazias da F0.5 (Dashboard, Chamados, Base etc.) seguem como placeholder até a F2+._
