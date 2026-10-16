> Convertido do .docx original do grupo. Onde a stack técnica diverge, vale o `docs/PROMPT_IMPLEMENTACAO.md`; regras de negócio, telas e critérios de aceite deste documento continuam valendo.
>
> As ferramentas de teste sugeridas (Jest, Supertest) correspondem a pytest + TestClient no backend e Vitest no front-end.

*CENTRO UNIVERSITÁRIO NOSSA SENHORA DO PATROCÍNIO — CEUNSP (CAMPUS SALTO) — Curso: Ciências da computação — 3º / 4º Semestre — Disciplina: Análise e Projeto de Sistemas — Docente: Prof.ª Waldinelly Costa*

*CADASTRO, CONSULTA E PRIMEIRAS REGRAS DE NEGÓCIO — Entregável Prático: Create \| Read \| Regras de Negócio \| Testes*

# DOCUMENTO 03: Cadastro, Consulta e Primeiras Regras de Negócio

## Escopo do Incremento (Sprint)

- **CRUD (Create, Read, Update, Delete):** operações básicas de banco de dados. Neste incremento entram **Create** (cadastro) e **Read** (consulta); Update (ciclo de vida, follow-ups e solução) e a exclusão lógica ficam para as próximas sprints.

- **Casos de uso cobertos:** UC01 (cadastrar usuários) e UC02 (registrar e classificar chamado), além da listagem e do detalhe do chamado (parte de UC03).

- **Requisitos atendidos:** RF01, RF02, RF05, RNF01, RNF02 e RN04.

## Módulo de Cadastro (Create)

- **Create (Criar / Inserir):** formulário web conectado ao backend para salvar novos registros no banco, com validação dos campos.

**A) Cadastro de usuários (UC01 / RF01) — ator: Administrador**

- **Campos:** nome, e-mail válido, senha com no mínimo 8 caracteres e perfil de acesso (CLIENTE, ANALISTA ou ADMIN). Endpoint: POST /api/usuarios.

**Passo 1 (Ator):** Preenche os dados e aciona “Cadastrar”.

**Passo 2 (Sistema):** Valida os campos obrigatórios e o formato do e-mail.

**Passo 3 (Sistema):** Verifica se o e-mail já existe na base.

**Passo 4 (Sistema):** Grava o usuário com a senha criptografada (BCrypt) e exibe a mensagem de sucesso.

- **FA01 — E-mail duplicado:** o sistema alerta e impede a duplicação. **FE01 — Campos incompletos:** os campos obrigatórios são destacados.

**B) Cadastro de chamados (UC02 / RF02 / RF05) — ator: Usuário (CLIENTE)**

- **Formulário em 3 etapas** (Categoria → Severidade → Detalhes). Endpoint: POST /api/chamados.

- **Validações:** categoria obrigatória; severidade BAIXA, MEDIA, ALTA ou CRITICO (padrão BAIXA); título obrigatório (até 150 caracteres); descrição obrigatória (até 500 caracteres, com contador na tela); anexos opcionais em PNG, JPG ou PDF de até 10 MB (a gravação dos anexos fica numa migration complementar).

**Passo 1 (Ator):** Escolhe a categoria e a severidade e preenche título e descrição.

**Passo 2 (Ator):** Submete o formulário de abertura.

**Passo 3 (Sistema):** Valida os dados obrigatórios e atribui o estado inicial “Novo”.

**Passo 4 (Sistema):** Associa o usuário autenticado e a categoria, e grava o chamado no banco.

**Passo 5 (Sistema):** Exibe a confirmação com o número de protocolo (ex.: TK-0051).

- **FE01 — Dados obrigatórios ausentes:** o sistema solicita o preenchimento antes de prosseguir.

## Módulo de Consulta (Read)

- **Read (Ler / Consultar):** telas que exibem os dados salvos, com paginação, filtros e barra de pesquisa em tempo real.

- **Meus Chamados** (GET /api/chamados): listagem em cartões e paginada, com protocolo, categoria, severidade, status, responsável, datas e número de mensagens.

- **Busca:** por título ou protocolo, em tempo real. **Filtros:** por status (Todos, Abertos, Em andamento, Resolvidos e Encerrados, com contadores) e por categoria.

- **Ordenação:** mais recentes primeiro, destacando os chamados de severidade CRITICO (Urgente), que são atendidos primeiro.

- **Detalhe do chamado** (GET /api/chamados/{id}) e **indicadores do Dashboard** (GET /api/chamados/resumo): abertos, em andamento, resolvidos e urgentes, lidos da mesma base.

- **Escopo por perfil:** o CLIENTE consulta somente os próprios chamados (RN06); a visão de ANALISTA e ADMIN será detalhada na sprint do ciclo de vida.

- **Desempenho:** a listagem deve responder em até 2 segundos (RNF02).

## Regras de Negócio (Business Rules)

- **Regras de Negócio:** lógicas e restrições operacionais do sistema, conforme o levantamento de requisitos (RN01 a RN05) e duas regras complementares deste incremento (RN06 e RN07).

- **RN04 — Rastreabilidade de Solicitante e Categoria (RF02):** não é permitido criar chamado sem a amarração simultânea com uma categoria de serviço e um usuário solicitante ativo. **Situação: implementada nesta sprint.**

- **RN06 — Acesso autenticado e escopo por perfil (RNF01):** só usuários autenticados cadastram e consultam chamados, e o CLIENTE vê apenas os seus. **Situação: implementada nesta sprint.** *(complementar)*

- **RN07 — Bloqueio de duplicidade por chave única:** o e-mail é único por usuário (UNIQUE), e o sistema impede o cadastro duplicado. **Situação: implementada nesta sprint.** *(complementar)*

- **RN01 — Cadastro de soluções no chamado (RF03):** para concluir um chamado, o técnico deve registrar a solução aplicada. **Situação: próxima sprint.**

- **RN02 — Aprovação de solução pelo usuário (RF03):** o status “Fechado” exige a aprovação expressa do usuário que abriu o chamado. **Situação: próxima sprint.**

- **RN03 — Atribuição de técnico ao chamado (RF03):** o status “Atribuído” exige vincular um analista/técnico responsável. **Situação: próxima sprint.**

- **RN05 — Publicação na Base de Conhecimento (RF06):** soluções de chamados bem-sucedidos podem ser registradas na base de conhecimento. **Situação: próxima sprint.**

## Critérios de Aceitação (DoD)

- **DoD (Definition of Done):** o formulário grava o usuário e o chamado no banco, e o chamado recém-criado aparece em “Meus Chamados” e nos indicadores do Dashboard.

- Busca, filtros por status e categoria e paginação funcionam, e o usuário não vê chamados de outro usuário.

- As regras RN04, RN06 e RN07 estão cobertas por testes unitários, e o build passa sem erros.

- A listagem responde em até 2 segundos (RNF02), em desktop e celular (RNF03).

## Critérios de Aceitação & Testes

- **Testes Unitários:** validação automatizada de partes isoladas do código (ferramentas sugeridas: Jest para as regras e Supertest/Postman para os endpoints).

- **TU01 (RN04):** criar chamado sem categoria → rejeitado. **TU02 (RN04):** solicitante inexistente ou inativo → rejeitado.

- **TU03:** chamado válido nasce com status NOVO, vinculado ao usuário autenticado, com a severidade informada e o protocolo gerado.

- **TU04:** título ou descrição vazios, e descrição acima de 500 caracteres → rejeitados.

- **TU05 (RN07):** e-mail duplicado → rejeitado. **TU06:** senha com menos de 8 caracteres → rejeitada; a senha é gravada como hash, nunca em texto puro.

- **TU07 (RN06):** requisição sem autenticação → acesso negado (401); o CLIENTE não lê chamado de outro usuário.

- **TU08:** filtros por status e categoria, busca por título/protocolo e paginação retornam o conjunto esperado.

- **Sprint Review:** reunião de demonstração do incremento ao Product Owner (PO). Roteiro: login → cadastro de usuário → abertura de chamado nas 3 etapas → consulta em “Meus Chamados” com filtros → tentativas inválidas (e-mail duplicado, chamado sem categoria). O feedback é registrado no backlog.
