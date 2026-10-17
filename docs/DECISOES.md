# Decisões

Decisões de arquitetura e de produto **já implementadas**, no formato ADR curto. Mais recente
primeiro. Decisões aprovadas e ainda sem código ficam em
[DEVELOPMENT_STATUS.md](DEVELOPMENT_STATUS.md), na seção "Decisões aprovadas, ainda não
implementadas".

Formato de cada entrada:

```markdown
## AAAA-MM-DD — Título

**Contexto:** o problema ou a lacuna.
**Decisão:** o que foi escolhido.
**Consequências:** o que muda, migrations, riscos e alternativas descartadas.
**Requisitos:** códigos afetados (RF, RN, UC...).
```

As diferenças em relação ao Documento 02 (seção 5.3 do prompt) entram aqui na F0.3, junto com a
migration `0001_esquema_inicial`.

---

## 2026-10-17 — Esquema inicial (migration 0001) e diferenças em relação ao Documento 02

**Contexto:** a F0.3 cria o banco. O dicionário de dados do Documento 02 precisava de
ajustes para atender aos requisitos (RN03, RN04, RNF02), ao protótipo e à exclusão lógica,
e faltava escolher a ferramenta de migration.

**Decisão:** o esquema é criado **só por migration Alembic** (`0001_esquema_inicial`), que
reproduz exatamente o SQL da seção 5.2. O Alembic é a ferramenta de migration do projeto
(sync + psycopg 3); a `DATABASE_URL` vem de `app.core.config`, não do `alembic.ini`. A API
nunca aplica migration na partida — quem aplica é o serviço `migrate` (`make migrate`), do
qual `api` e `worker` dependem (`service_completed_successfully`). As diferenças adotadas em
relação ao Documento 02 (seção 5.3 do prompt):

| Mudança | Motivo |
|---|---|
| `usuarios.ativo` | RN04 e TU02 exigem "solicitante ativo"; também é a exclusão lógica prevista |
| `usuarios.cargo` (opcional) | O protótipo mostra o cargo abaixo do nome ("Analista de Marketing") |
| `chamados.protocolo` (coluna gerada) | Busca por protocolo com índice; formato estável acima de 9999 (`TK-12345`) |
| `chamados.data_atualizacao` | Os cards exibem "Atualizado: dd/mm/aa" |
| `categorias.icone`, `ordem` e `ativa` | Grade de categorias montada pelo banco; desativar sem apagar (FK) |
| CHECKs e índice único parcial em `solucoes` | Invariantes da RN03, do TU04 e de "uma solução pendente por chamado" |
| `TIMESTAMPTZ` em vez de `TIMESTAMP` | Evita erro de fuso horário |
| Extensões `pg_trgm` e `unaccent` + `f_unaccent()` | Busca por título em tempo real, sem diferenciar acento, dentro do RNF02 |

**Consequências:** os 4 tipos ENUM (`perfil_usuario`, `severidade_chamado`, `status_chamado`,
`status_aprovacao`) são criados e removidos explicitamente na migration (`create_type=False`
nas colunas), para o `downgrade()` ser completo (inclui `DROP TYPE`, `DROP FUNCTION` e
`DROP EXTENSION`). FKs com `ON DELETE RESTRICT`: usuários e chamados nunca são apagados. O
`protocolo` é coluna gerada e somente leitura (`Computed(persisted=True)`); a busca por título
usa `f_unaccent(lower(titulo))`, idêntica à do índice trigram. A ida e volta
(`upgrade head → downgrade base → upgrade head`) foi validada em PostgreSQL real.

**Requisitos:** RN03 (CHECK), RN04, RN07 (UNIQUE), RNF02 (índices e busca sem acento).

---

## 2026-10-16 — Portas de desenvolvimento só em 127.0.0.1, fora das já usadas no servidor

**Contexto:** o prompt sugere 5432, 8000, 8080 e 8333 no host. No servidor Oracle, 5432 (PostgreSQL
do GRH), 8080, 8090 (GRH) e 9000/9001 (MinIO do GRH) já estão ocupadas, e o `AGENTS.md` do servidor
proíbe expor portas na internet.

**Decisão:** portas configuráveis no `.env`, publicadas só no `docker-compose.override.yml` e sempre
em `127.0.0.1`: PostgreSQL 5442, MinIO 9100 (S3) e 9101 (console), Mailpit 8125 (UI) e 1125
(SMTP). API (8100) e web (8180) seguem o mesmo padrão quando entrarem. Acesso de fora do servidor
por túnel SSH ou pelo encaminhamento de portas do VS Code.

**Consequências:** o `docker-compose.yml` base não publica porta nenhuma; produção (F7) usa o
Traefik. Os serviços conversam pelos nomes na rede interna (`db:5432`, `s3:9000`).

**Requisitos:** RNF01.

## 2026-10-16 — MinIO no lugar do SeaweedFS

**Contexto:** a seção 2 do prompt proíbe o MinIO porque o Community Edition parou de publicar
imagens e teve o repositório arquivado. O grupo prefere o MinIO, que já conhece (é usado no GRH),
e o projeto é acadêmico.

**Decisão:** serviço `s3` com MinIO RELEASE.2026-09-22, imagem do Chainguard
(`cgr.dev/chainguard/minio`) fixada **por digest**: as imagens oficiais não existem mais no Docker
Hub nem no Quay, e o Chainguard só publica a tag `latest`. Healthcheck com `mc ready local`. O
nome do serviço (`s3`) e as variáveis `S3_*` continuam genéricos; `S3_ACCESS_KEY` e
`S3_SECRET_KEY` viram o usuário e a senha raiz do MinIO. O `infra/seaweedfs/entrypoint.sh` do
prompt deixa de existir.

**Consequências:** o código (F3) usa só a API S3 via boto3, então voltar ao SeaweedFS, ou usar
Garage ou AWS S3, continua sendo só configuração. Atualizar o MinIO é trocar o digest de propósito
e registrar aqui. Licença do MinIO: AGPLv3, sem obrigação enquanto não for modificado.

**Requisitos:** RF02 (anexos, F3).
