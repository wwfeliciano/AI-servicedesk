> Convertido do .docx original do grupo. Onde a stack técnica diverge, vale o `docs/PROMPT_IMPLEMENTACAO.md`; regras de negócio, telas e critérios de aceite deste documento continuam valendo.
>
> A stack NestJS/TypeORM/Jest citada aqui foi substituída por Python (FastAPI, SQLAlchemy, Alembic, pytest) — ver a seção 3.4 do prompt. As camadas e o esquema das 6 tabelas foram mantidos.

*CENTRO UNIVERSITÁRIO NOSSA SENHORA DO PATROCÍNIO — CEUNSP (CAMPUS SALTO) — Curso: Ciências da computação — 3º / 4º Semestre — Disciplina: Análise e Projeto de Sistemas — Docente: Prof.ª Waldinelly Costa*

*REPOSITÓRIO CRIADO, BANCO CONFIGURADO E ESTRUTURA INICIAL — Entregável Prático: Repositório \| Banco \| Migrations \| Estrutura*

# DOCUMENTO 02: Repositório Criado, Banco Configurado e Estrutura Inicial

## Repositório de Código (GitHub / GitLab)

- **Repositório:** local centralizado para armazenamento e versionamento do código. Nome: mentory-helpdesk (URL: **\[preencher pelo grupo\]**), com acesso concedido à docente e a todos os integrantes.

- **Branch Protection (Proteção de Ramos):** regra que impede alterações diretas na branch principal (main). As mudanças entram por Pull Request, com ao menos 1 aprovação e build verde, a partir de ramos feature/\* integrados em develop.

- **.gitignore:** arquivo que indica o que o Git deve ignorar — node_modules/, dist/, build/, .env, volumes do Docker e arquivos de IDE. O .env.example fica versionado como modelo.

- **README.md:** descreve o projeto, os pré-requisitos e os passos para subir o ambiente.

## Banco de Dados (PostgreSQL / MySQL)

- **SGBD (Sistema de Gerenciamento de Banco de Dados):** PostgreSQL (alternativa prevista: MySQL 8.0). **Justificativa:** confiabilidade ACID, suporte a ENUMs para severidades e ciclo de vida e integridade referencial.

- **Docker:** tecnologia de containers para padronizar o ambiente de desenvolvimento. O docker-compose.yml sobe o banco com um único comando, com a mesma versão para todo o grupo.

- **Migrations (Migrações):** scripts de versionamento da estrutura do banco. O esquema evolui de forma incremental, sem engessar o banco antes de as regras de negócio estarem fechadas.

- **Variáveis de ambiente:** credenciais de conexão e segredos de criptografia ficam no arquivo .env, fora do repositório.

- **Ferramenta de apoio:** DBeaver, para conferir tabelas e dados; o DER é mantido no Draw.io / Lucidchart.

## Esquema Criado pela Migration Inicial (DER e Dicionário de Dados)

**Entidades e relações-chave**

- \[USUARIOS\] 1 — N \[CHAMADOS\] \| \[CHAMADOS\] 1 — N \[FOLLOW_UPS\] \| \[CHAMADOS\] N — 1 \[CATEGORIAS\]

- \[CHAMADOS\] 1 — 1 ou N \[SOLUCOES\] \| \[SOLUCOES\] 1 — 1 \[BASE_CONHECIMENTO\] \| \[USUARIOS\] (analistas) 1 — N \[CHAMADOS\] (técnico responsável)

- **Integridade:** chaves estrangeiras (FKs) ativas, com restrições de exclusão e atualização configuradas.

**Tabela 01: USUARIOS**

- **id_usuario** (INT/BIGINT, PK, auto incremento); **nome** (VARCHAR(150), NOT NULL); **email** (VARCHAR(100), NOT NULL, UNIQUE); **senha_hash** (VARCHAR(255), NOT NULL, BCrypt); **tipo_perfil** (ENUM ADMIN, ANALISTA, CLIENTE); **data_cadastro** (TIMESTAMP, padrão CURRENT_TIMESTAMP).

**Tabela 02: CATEGORIAS**

- **id_categoria** (INT, PK); **nome_categoria** (VARCHAR(100), NOT NULL, UNIQUE). Carga inicial: TI, RH, Financeiro, Acesso, Hardware, Software e Outro.

**Tabela 03: CHAMADOS**

- **id_chamado** (INT, PK); **id_usuario_abertura** (FK → USUARIOS, NOT NULL); **id_tecnico_responsavel** (FK → USUARIOS, NULL); **id_categoria** (FK → CATEGORIAS, NOT NULL).

- **titulo** (VARCHAR(150), NOT NULL) — título exibido nas listagens, previsto no protótipo e acrescentado ao modelo base; **descricao** (TEXT, NOT NULL).

- **severidade** (ENUM BAIXA, MEDIA, ALTA, CRITICO; padrão BAIXA); **status_chamado** (ENUM NOVO, PENDENTE, ATRIBUIDO, CONCLUIDO, FECHADO; padrão NOVO); **data_criacao** (TIMESTAMP).

- O protocolo exibido na tela (ex.: TK-0051) é gerado a partir do id_chamado.

**Tabela 04: FOLLOW_UPS**

- **id_followup** (PK); **id_chamado** (FK → CHAMADOS, NOT NULL); **id_autor** (FK → USUARIOS, NOT NULL); **mensagem** (TEXT, NOT NULL); **data_envio** (TIMESTAMP).

**Tabela 05: SOLUCOES**

- **id_solucao** (PK); **id_chamado** (FK, NOT NULL); **id_analista** (FK → USUARIOS, NOT NULL); **descricao_solucao** (TEXT, NOT NULL); **status_aprovacao** (ENUM PENDENTE_APROVACAO, APROVADO, REJEITADO; padrão PENDENTE_APROVACAO); **data_solucao** (TIMESTAMP).

**Tabela 06: BASE_CONHECIMENTO**

- **id_base** (PK); **id_solucao** (FK → SOLUCOES, NOT NULL); **titulo** (VARCHAR(200), NOT NULL); **conteudo_indexado** (TEXT, NOT NULL); **data_inclusao** (TIMESTAMP).

**Evolução prevista por novas migrations:** tabelas ANEXOS (arquivos PNG, JPG e PDF de até 10 MB do formulário) e NOTIFICACOES (avisos exibidos no portal).

## Estrutura Inicial (Arquitetura)

- **Arquitetura em Camadas / MVC (Model-View-Controller):** padrão que separa a lógica de dados, a interface e o controle, com **API RESTful** desacoplada do front-end.

- **Stack:** Frontend em React.js / TypeScript; Backend em Node.js (NestJS) — alternativa C# (.NET Core); banco PostgreSQL.

- **ORM (Object-Relational Mapping):** ferramenta que mapeia as tabelas do banco em classes de código e gera as migrations (TypeORM no NestJS; Entity Framework Core, se o grupo optar por .NET).

- **Camadas do backend:** Controllers (endpoints), Services (regras de negócio) e Repositories / DAO (acesso a dados). **Frontend:** Views / Pages, Components, Services de comunicação e State Management.

**Estrutura de pastas**

> mentory-helpdesk/
>
> ├── docker-compose.yml (banco em container)
>
> ├── .env.example (modelo das variáveis)
>
> ├── .gitignore
>
> ├── README.md
>
> ├── backend/ (API REST — NestJS)
>
> │ ├── src/
>
> │ │ ├── controllers/ (endpoints)
>
> │ │ ├── services/ (regras de negócio)
>
> │ │ ├── repositories/ (acesso a dados / ORM)
>
> │ │ ├── entities/ (modelos das 6 tabelas)
>
> │ │ ├── dtos/ (validação de entrada)
>
> │ │ └── migrations/ (versionamento do banco)
>
> │ └── test/ (testes unitários e de conexão)
>
> └── frontend/ (SPA — React / TypeScript)
>
> └── src/
>
> ├── pages/ (5 telas do protótipo)
>
> ├── components/ (AppShell, StatusBadge)
>
> ├── services/ (chamadas à API)
>
> └── state/ (estado da aplicação)

## Comunicação e Segurança entre Camadas

- **Protocolo:** HTTP/HTTPS com payloads em JSON (RNF01).

- **Autenticação:** tokens JWT; senhas armazenadas com hash BCrypt.

- **Banco de dados:** ORM com Prepared Statements, contra SQL Injection; segredos isolados em arquivos .env.

## Passos de Execução (Evidência)

Sequência de referência para reproduzir o ambiente a partir do repositório:

> git clone \<URL do repositório\> && cd mentory-helpdesk
>
> cp .env.example .env
>
> docker compose up -d \# sobe o PostgreSQL
>
> npm run migration:run \# cria as 6 tabelas
>
> npm run test \# teste de conexão com o banco
>
> npm run build \# compilação inicial sem erros

## Critérios de Aceitação (DoD)

- **DoD (Definition of Done):** repositório acessível ao grupo e à docente, com a main protegida e o .gitignore configurado.

- Banco no ar via docker compose up, com **conexão validada por teste automatizado**.

- Migration inicial executada sem erros, criando as 6 tabelas, as chaves estrangeiras e os ENUMs.

- **Build (compilação inicial)** do backend e do frontend sem erros, com a estrutura de pastas em camadas criada.
