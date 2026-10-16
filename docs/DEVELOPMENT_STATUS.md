# Status de desenvolvimento

Andamento do projeto, recorte a recorte. Mais recente primeiro. O plano está em
[ROADMAP.md](ROADMAP.md).

## Situação atual (16/10/2026)

- **Etapa vigente:** E0 concluída. Próximo recorte: **F0.1 — Infraestrutura**, aguardando o pedido
  do usuário.
- **Código validado:** nenhum ainda.
- **Repositório:** Git local na branch `develop`, sem remoto.

## Pendências

- Definir o remoto do GitHub (público ou privado com GitHub Education — seção 3.3 do prompt).
- Configurar `user.name` e `user.email` do Git neste repositório antes do primeiro commit.
- Confirmar com o usuário se o arquivo vazio `ddd` na raiz pode ser removida.

## Decisões aprovadas, ainda não implementadas

Vão para [DECISOES.md](DECISOES.md) quando o código existir.

- **MinIO no lugar do SeaweedFS** (pedido do usuário, 16/10/2026). Contraria a seção 2 do prompt,
  que proíbe o MinIO. Motivo: projeto acadêmico; o grupo já conhece o MinIO (usado no GRH). Como o
  código usa a API S3 genérica (boto3), a troca é só configuração. Imagem: Chainguard fixada por
  digest (as imagens oficiais não são mais publicadas). Entra na F0.1 (serviço) e na F3 (uso).
- **Backend antes do front-end** em cada etapa (pedido do usuário, 16/10/2026). Na F0, o front-end
  base é o último recorte (F0.5).
- **Etapas quebradas em recortes** (F0.1, F0.2...), no formato do GRH, com commit e relatório por
  recorte.

---

## E0.1 — Organização do repositório (16/10/2026)

- Documentação no formato do projeto GRH: `AGENTS.md`, `docs/INSTRUCOES_AGENTES.md`,
  `docs/ROADMAP.md`, este arquivo, `docs/DECISOES.md`, `docs/AJUSTES_IDENTIFICADOS.md`,
  `docs/RASTREABILIDADE.md`, `docs/telas/` e `README.md`.
- Pacote do grupo copiado para `docs/`: `PROMPT_IMPLEMENTACAO.md`, `requisitos/` (Documentos 01 a
  03) e `prototipo/` (6 capturas).
- Ambiente preparado no servidor:
  - `make` instalado pelo apt; `uv` 0.13.1 em `~/.local/bin`; Python 3.13.16 gerenciado pelo uv;
  - imagens fixadas baixadas e conferidas para ARM64 (lista em `INSTRUCOES_AGENTES.md`, seção 6).
- Um rascunho de API feito antes da organização foi apagado a pedido do usuário; a F0 recomeça do
  zero pela F0.1.
- Sem testes, sem containers do projeto em execução.
