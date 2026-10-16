# AGENTS.md — Mentory Help Desk

## 1. Papel do agente e etapa atual

Atue como engenheiro full-stack sênior (Python, TypeScript, PostgreSQL, Docker) construindo o
**Mentory Help Desk**, projeto acadêmico do CEUNSP (Análise e Projeto de Sistemas): portal de
chamados com os perfis CLIENTE, ANALISTA e ADMIN.

O trabalho é feito **por etapas e recortes**, na ordem de `docs/ROADMAP.md`. A etapa vigente e o
último recorte entregue estão no topo de `docs/DEVELOPMENT_STATUS.md`.

O roadmap registra direção; ele não autoriza implementar tudo. Execute apenas o recorte pedido
pelo usuário e pare ao concluí-lo.

## 2. Fonte da verdade e precedência

1. Pedido explícito do usuário na sessão.
2. `docs/PROMPT_IMPLEMENTACAO.md`: stack, arquitetura, modelo de dados, contratos de API e fases.
   As decisões de `docs/DECISOES.md` prevalecem sobre ele (exemplo: MinIO no lugar do SeaweedFS).
3. `docs/requisitos/*.md` (Documentos 01, 02 e 03): regras de negócio, telas, jornadas e critérios
   de aceite.
4. `docs/prototipo/*.png`: só referência visual.

Depois que algo existe, o comportamento do código, das migrations e dos testes prevalece sobre texto
desatualizado: corrija a documentação no mesmo recorte.

Lacunas ou conflitos: aplique o padrão da seção 14 do prompt, registre e siga. Não invente
requisitos. Decisão que muda entidade, permissão, regra de negócio ou fonte da verdade é do usuário.

## 3. Regras do servidor

Siga também `/home/ubuntu/AGENTS.md` (Oracle ARM64): imagens compatíveis com ARM64, portas só em
`127.0.0.1`, limites de CPU e memória em todo serviço, nada publicado no Traefik sem aprovação,
sem `docker.sock` nos containers e sem mexer em containers de outras aplicações (GRH, Traefik).

## 4. Stack obrigatória

- Backend: Python 3.13, FastAPI, Pydantic v2, SQLAlchemy 2.0 síncrono + psycopg 3, Alembic, uv.
- Qualidade: Ruff, mypy `strict`, pytest com PostgreSQL real.
- Front-end: React 19 + TypeScript `strict` + Vite, TanStack Query, Zustand, Tailwind 4.
- Dados: PostgreSQL 17, Redis 8 (só estado efêmero com TTL), MinIO (API S3) para arquivos.
- Integrações (Fase 6): n8n Community + WAHA.
- Tudo em Docker Compose, versões fixas (nunca `latest`; MinIO fixado por digest).

Camadas: controller → service → repository → entity. Service não importa FastAPI. Nenhuma regra
de negócio em controller, componente de UI ou workflow do n8n.

## 5. Persistência

- Esquema só por migration Alembic. Nunca `metadata.create_all()`, nem nos testes.
- A API não aplica migration ao iniciar; quem aplica é o serviço `migrate` (`make migrate`).
- Todo `upgrade()` tem `downgrade()` completo (inclusive `DROP TYPE`).
- Usuários e chamados nunca são apagados: exclusão lógica por `ativo`. FKs com `ON DELETE RESTRICT`.
- Não apague volume, banco ou dado para acomodar uma mudança.

## 6. Rastreabilidade (critério de avaliação)

Os códigos dos documentos (RF, RNF, RN, UC, UJ, FA, FE, TU) aparecem:

- nas docstrings dos services;
- no nome dos testes (`test_tu03_...`);
- nas mensagens de commit (`feat(chamados): RN04 exige categoria e solicitante ativo`);
- em `docs/RASTREABILIDADE.md`.

## 7. Idioma e nomes

Interface, mensagens, documentação e commits em PT-BR. Identificadores de domínio em português sem
acento, iguais ao dicionário de dados (`chamado`, `id_usuario_abertura`, `status_chamado`); sufixos
técnicos em inglês (`ChamadoService`, `ChamadoRepository`).

## 8. Segurança

Segredos só no `.env` (fora do Git); `.env.example` com placeholders. Nenhuma senha, token, e-mail
real ou `chat_id` em log, teste, documentação ou commit. Dados de teste e seed são fictícios.

## 9. Licenças

Só software gratuito e de código aberto (seção 2 e 3.3 do prompt). Antes de adicionar dependência,
confira a licença. Nada de SaaS pago, license key ou imagem Bitnami.

## 10. Documentação e Git

O processo de cada recorte (validação, documentos a atualizar, commit e relatório) está em
`docs/INSTRUCOES_AGENTES.md`. Não use reset destrutivo, `--force` nem `--no-verify` sem pedido
explícito. Push só com autorização do usuário, a cada vez.
