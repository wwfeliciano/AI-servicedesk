# 02 — Chamados (Dashboard, Novo Chamado, Meus Chamados, Detalhe)

Telas da F2.4, na identidade teal (IBM Plex Sans, tema claro/escuro). Descreve o comportamento
atual; o planejado fica na seção 8.4 do prompt.

## Dashboard (`/dashboard`)

- Saudação por faixa de horário ("Bom dia/tarde/noite") + primeiro nome; botão "Novo Chamado".
- **Alerta de urgentes:** só aparece quando `/api/chamados/resumo` traz `urgentes > 0`; o botão
  "Ver agora" leva à lista filtrada por abertos.
- **Quatro indicadores** (do `/resumo`): Abertos, Em andamento, Resolvidos e Urgentes.
- **Chamados recentes:** os 5 últimos (`GET /api/chamados?page_size=5`), cada card leva ao detalhe.
- **Ações rápidas:** abrir chamado, base de conhecimento e histórico.
- Escopo por perfil: o CLIENTE vê só os seus; ANALISTA/ADMIN veem a fila inteira (vem da API).

## Novo Chamado (`/chamados/novo`)

- **Wizard de 3 etapas** com indicador de progresso:
  1. **Categoria** — grade das categorias ativas (`GET /api/categorias`); seleção obrigatória para
     avançar.
  2. **Prioridade** — Baixa / Média / Alta / Urgente (o Urgente mostra a sirene). O rótulo é
     "Prioridade", mas o campo enviado é `severidade`.
  3. **Detalhes** — título (até 150) e descrição (até 500, com contador `0/500` que fica vermelho
     quando vazio ou no limite).
- **FE02:** título ou descrição vazios destacam o campo em vermelho e **bloqueiam** o envio.
- **Voltar** (etapas 2 e 3) e **Cancelar** (descarta o rascunho e volta ao Dashboard — FE03). O
  rascunho fica só em memória: sair da tela o descarta.
- Sucesso: tela de confirmação com o **protocolo em destaque** (ex.: `TK-0051`) e os botões "Ver
  chamado" e "Meus chamados".

## Meus Chamados (`/chamados`)

- Título, total de chamados e botão "Novo".
- **Busca** por título ou protocolo com **debounce de 300 ms**.
- **Abas com contadores:** Todos, Abertos, Em andamento, Resolvidos, Encerrados (os contadores vêm
  da API e respeitam a busca/categoria, mas não o filtro de aba).
- **Chips de categoria:** "Todas as categorias" + as categorias.
- **Cartões:** protocolo (mono), chip de categoria, chip "Urgente" quando crítico, título,
  descrição (2 linhas), status e severidade; rodapé com datas, responsável e nº de mensagens.
  Clicar abre o detalhe.
- **Paginação** de 10 e **filtros refletidos na URL** (`?q&grupo&categoria&page`), para o botão
  Voltar do navegador funcionar. Estados de carregando, vazio e erro (com "Tentar novamente").

## Detalhe do chamado (`/chamados/:id`)

- Cabeçalho: protocolo, categoria, título e os badges de status e severidade.
- Dados: solicitante, responsável (ou "Sem responsável"), datas de abertura e atualização.
- Descrição completa. Uma nota indica que histórico, mensagens e ações chegam na F4.
- Chamado inexistente ou fora do escopo do perfil → tela de **404** (não revela chamados de outros).

### Anexos (F3.3)

- **No Novo Chamado (etapa 3):** zona "Clique para adicionar arquivo ou arraste aqui — PNG, JPG,
  PDF até 10 MB". Os arquivos escolhidos aparecem numa lista removível (até 5). Ao enviar o
  chamado, os anexos sobem **depois** de criar o chamado; se algum falhar, o chamado continua
  criado e a confirmação avisa para reenviar no detalhe.
- **No Detalhe:** lista os anexos com botão de download e uma zona de upload que envia na hora;
  desabilita ao atingir 5 anexos. A validação de tipo/tamanho acontece no cliente e também no
  servidor (por magic bytes).

### Ciclo de vida no Detalhe (F4.3)

- **Linha do tempo:** cada transição de status (NOVO → … → FECHADO) aparece em ordem, com o tempo
  relativo. **Follow-ups** (mensagens) ficam abaixo, com uma caixa para enviar nova mensagem.
- **Ações por perfil (ANALISTA/ADMIN):** "Triar" (quando NOVO → Aberto), "Atribuir"/"Reatribuir"
  (modal com a lista de técnicos ativos) e "Registrar solução" (modal; conclui o chamado). Aparecem
  conforme o status.
- **Cartão da solução (solicitante):** quando o chamado está CONCLUIDO, o solicitante vê a solução
  proposta e pode **Aprovar e encerrar** (→ Encerrado) ou **Reprovar** (motivo obrigatório; volta a
  Em andamento e o motivo vira um follow-up).
- **Fila (Meus Chamados):** para ANALISTA/ADMIN o título vira "Chamados" e cada card mostra o
  solicitante. Chamado **Encerrado** não aceita novas ações nem mensagens.



## Base de Conhecimento (`/base-conhecimento`, F5.2)

- **Busca e filtro:** campo de busca por palavra-chave (sem acento; reflete em `?q=`) e chips de
  categoria (`?categoria=`). O estado fica na URL, então o Voltar do navegador funciona.
- **Acordeão:** os artigos aparecem como uma lista; clicar no título abre/fecha o conteúdo. O artigo
  aberto mostra a categoria, a data de publicação e as ações.
- **"Não resolveu? Abrir chamado":** leva ao wizard de Novo Chamado já com a categoria selecionada e
  o título pré-preenchido ("Dúvida: &lt;título do artigo&gt;"); o prefill só se aplica se o rascunho
  ainda estiver vazio.
- **ANALISTA/ADMIN — Editar:** abre um modal para ajustar título e conteúdo do artigo (`PATCH`).
- **Publicar a partir do chamado:** no Detalhe de um chamado com **solução aprovada**, ANALISTA/ADMIN
  veem um cartão "Publicar na base"; o modal pré-preenche o título (do chamado) e o conteúdo
  (descrição da solução). Artigos só nascem de uma solução aprovada (RN05).
