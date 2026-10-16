# Status de desenvolvimento

Andamento do projeto, recorte a recorte. Mais recente primeiro. O plano está em
[ROADMAP.md](ROADMAP.md).

## Situação atual (16/10/2026)

- **Etapa vigente:** F0 — Fundação. Último recorte: **F0.1 — Infraestrutura** (concluído).
  Próximo: **F0.2 — API base**, aguardando o pedido do usuário.
- **No ar:** `db`, `redis`, `s3` (MinIO) e `mailpit`, todos `healthy` (`make ps`).
- **Repositório:** Git local na branch `develop`, sem remoto.

## Pendências

- Definir o remoto do GitHub (público ou privado com GitHub Education — seção 3.3 do prompt).

## Decisões aprovadas, ainda não implementadas

Vão para [DECISOES.md](DECISOES.md) quando o código existir.

- **Backend antes do front-end** em cada etapa (pedido do usuário, 16/10/2026). Na F0, o front-end
  base é o último recorte (F0.5).
- **Etapas quebradas em recortes** (F0.1, F0.2...), no formato do GRH, com commit e relatório por
  recorte.

---

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
