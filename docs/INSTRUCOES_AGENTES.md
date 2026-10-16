# Instruções de trabalho para agentes — Mentory Help Desk

Complementa o `AGENTS.md` da raiz, que continua sendo a fonte das regras de arquitetura e qualidade.
O andamento vivo está em `docs/DEVELOPMENT_STATUS.md`.

---

## 1. Antes de alterar qualquer coisa

1. Leia `AGENTS.md` (raiz) e `/home/ubuntu/AGENTS.md` (servidor).
2. Leia o topo de `docs/DEVELOPMENT_STATUS.md` e o recorte pedido em `docs/ROADMAP.md`.
3. Leia a seção correspondente de `docs/PROMPT_IMPLEMENTACAO.md` e os requisitos citados.
4. Rode `git status`, `git log --oneline -10` e `git diff`. Não descarte mudança que não é sua.
5. Declare o recorte, os arquivos prováveis, os impactos e a validação planejada.

## 2. Como trabalhar

- **Um recorte por vez** (exemplo: `F0.2`). Execute só o que foi pedido e pare.
- **Backend antes do front-end** em cada etapa: primeiro API, banco e testes; a tela vem depois,
  sobre um contrato já validado.
- **Pergunte só o que é decisão de negócio ou visual.** Nome, estrutura e padrão se resolvem pelo
  prompt e pelo código existente.
- **Interface:** nenhuma tela entra sem seguir o protótipo (`docs/prototipo/`) e os tokens da seção
  8.2 do prompt; mostre ao usuário antes de considerar a tela pronta.

## 3. Ao concluir um recorte (sempre, nesta ordem)

1. **Validação**, separando falha preexistente de falha introduzida:
   - backend: `make lint` (ruff check, ruff format --check, mypy) e `make test`;
   - front-end (quando houver): `npm run lint`, `tsc --noEmit`, `vitest run`;
   - com migration: ida e volta (`upgrade head → downgrade base → upgrade head`);
   - `docker compose config` antes de subir e `git diff --check`.
2. **Documentação** do mesmo recorte (seção 5).
3. **Commit** pequeno e coerente, no padrão Conventional Commits citando o código
   (`feat(api): F0.2 health e formato de erro`). Só depois de tudo passar.
4. **Push só com autorização explícita**, a cada vez.
5. **Deixar a aplicação no ar** para o usuário testar e confirmar que respondeu.
6. **Relatório** no formato da seção 15 do prompt. Depois, pare.

## 4. Proibições

- Não colocar dado pessoal real em código, testes, documentação, logs ou commits.
- Não usar `metadata.create_all()`, não aplicar migration na partida da API, não apagar volume,
  banco ou dado.
- Não publicar no Traefik nem abrir porta fora de `127.0.0.1` sem aprovação.
- Não tocar nos containers do GRH, do Traefik ou de qualquer outra aplicação.

## 5. Documentação: o que atualizar em cada recorte

| Documento | Quando |
|---|---|
| `docs/DEVELOPMENT_STATUS.md` | sempre: seção do recorte no topo, pendências e próximo passo |
| `docs/ROADMAP.md` | estado do recorte (`futuro` → `em_andamento` → `concluído`) |
| `docs/DECISOES.md` | decisão aprovada **e implementada** (nunca só planejada) |
| `docs/RASTREABILIDADE.md` | requisito, endpoint, tela ou teste novo |
| `docs/AJUSTES_IDENTIFICADOS.md` | defeito ou ajuste encontrado e ainda não corrigido |
| `docs/telas/*.md` e `docs/telas/HISTORICO.md` | tela nova ou mudança de comportamento |
| `docs/der.md` | migration que muda tabelas ou relações |
| `README.md` | comando, serviço, porta ou passo de execução novo |

`docs/telas/` e `docs/der.md` descrevem só o que existe; desejo e plano ficam no roadmap.

## 6. Ambiente local (servidor Oracle ARM64)

**Ferramentas no host** (só no usuário, nada global, exceto o `make` do apt):

- `uv` 0.13.1 em `~/.local/bin` (exporte `PATH="$HOME/.local/bin:$PATH"` em shell não interativo);
- Python 3.13.16 gerenciado pelo uv (`~/.local/share/uv/python`);
- Node **não** é instalado no host: npm roda no container `node:24.22.0-alpine` pelo Makefile.

**Imagens fixadas (ARM64 conferido em 16/10/2026):**

| Serviço | Imagem |
|---|---|
| db | `postgres:17.11-alpine` |
| redis | `redis:8.8.3-alpine` |
| s3 (MinIO RELEASE.2026-09-22) | `cgr.dev/chainguard/minio@sha256:2136d593beacf4461187035eca949fe49abd589d5079735025c711ca58fee0c8` |
| backend (api, worker, migrate) | `python:3.13.16-slim` + `ghcr.io/astral-sh/uv:0.13.1` |
| build do front-end | `node:24.22.0-alpine` |
| web | `nginx:1.30.6-alpine` |
| e-mail em dev | `axllent/mailpit:v1.31.6` |

**Portas no host (todas em `127.0.0.1`)** — 5432, 8080, 8090, 9000 e 9001 já são usadas por outras
aplicações:

| Serviço | Porta |
|---|---|
| PostgreSQL (DBeaver) | 5442 |
| API | 8100 |
| Web | 8180 |
| MinIO S3 / console | 9100 / 9101 |
| Mailpit UI / SMTP | 8125 / 1125 |

O usuário acessa por túnel SSH (`ssh -L 8180:127.0.0.1:8180 ...`) ou pelo encaminhamento de portas
do VS Code.

## 7. Armadilhas conhecidas

- **Recursos compartilhados:** 4 OCPUs e 24 GB com GRH, Traefik e outros. Não rode builds pesados em
  paralelo (imagem do backend junto com o build do front-end).
- **MinIO:** as imagens oficiais saíram do Docker Hub e do Quay; a única fonte mantida é a do
  Chainguard, que só publica `latest`. Fixe sempre pelo digest e atualize o digest de propósito.
- **Sequências não voltam no rollback** dos testes: não fixe ids.
- **`EmailStr` recusa `.local` e `.test`:** seeds e testes usam `@empresa.com.br`.
