# Mentory Help Desk — atalhos de desenvolvimento.
# Os alvos de migrations e seeds entram nos recortes seguintes da F0 e nas fases 1 e 2.

COMPOSE := docker compose
UV := PATH="$(HOME)/.local/bin:$(PATH)" uv
BACKEND := backend
FRONTEND := frontend

.DEFAULT_GOAL := help
.PHONY: help env config up down publicar despublicar ps logs lint format test test-performance test-lento test-tudo build migrate migration criar-admin seed seed-performance \
        front-install front-lint front-test front-build front-dev front-gen-api

help: ## Lista os alvos disponíveis
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  %-10s %s\n", $$1, $$2}'

env: ## Cria o .env a partir do .env.example com segredos aleatórios (não sobrescreve)
	@./infra/gerar-env.sh

config: ## Valida o Docker Compose
	@$(COMPOSE) config --quiet && echo "docker compose config: ok"

up: config ## Sobe os serviços e espera ficarem saudáveis
	$(COMPOSE) up -d --wait

down: ## Para os serviços (os volumes são preservados)
	$(COMPOSE) down

COMPOSE_PUBLICO := $(COMPOSE) -f docker-compose.yml -f docker-compose.override.yml -f docker-compose.publico.yml

publicar: ## Publica o teste externo em https://help.wwftech.com.br (Traefik)
	@$(COMPOSE_PUBLICO) config --quiet && echo "docker compose config (publico): ok"
	$(COMPOSE_PUBLICO) up -d --wait api worker web

despublicar: ## Tira o web do Traefik e volta ao dev só em 127.0.0.1
	$(COMPOSE) up -d --wait api worker web

ps: ## Mostra o estado dos serviços
	$(COMPOSE) ps

logs: ## Acompanha os logs (make logs s=db para um serviço)
	$(COMPOSE) logs -f --tail=100 $(s)

lint: ## Backend: ruff check, ruff format --check e mypy strict
	cd $(BACKEND) && $(UV) run ruff check . && $(UV) run ruff format --check . && $(UV) run mypy app

format: ## Backend: formata o código (ruff format)
	cd $(BACKEND) && $(UV) run ruff format .

test: ## Backend: pytest
	cd $(BACKEND) && $(UV) run pytest

test-performance: ## Backend: só os testes de desempenho (RNF02), sob demanda
	cd $(BACKEND) && $(UV) run pytest -m performance -p no:cacheprovider --no-cov

test-lento: ## Backend: só os testes lentos (upload grande, ida e volta de migrations)
	cd $(BACKEND) && $(UV) run pytest -m lento -p no:cacheprovider --no-cov

test-tudo: ## Backend: todos os testes, inclusive lentos e de performance
	cd $(BACKEND) && $(UV) run pytest -m "" 

build: ## Build das imagens Docker (backend: api e worker)
	$(COMPOSE) build

migrate: ## Aplica as migrations no banco (serviço migrate, one-shot)
	$(COMPOSE) run --rm migrate

migration: ## Gera uma migration por autogenerate (make migration nome=descricao) — revisar à mão
	@test -n "$(nome)" || { echo "Uso: make migration nome=descricao_curta"; exit 1; }
	cd $(BACKEND) && $(UV) run alembic revision --autogenerate -m "$(nome)"

criar-admin: ## Cria o primeiro ADMIN a partir do .env (idempotente; lê ADMIN_NOME/EMAIL/SENHA)
	$(COMPOSE) run --rm api python -m app.cli criar-admin

seed: ## Popula o dev com usuários fictícios e ~60 chamados (idempotente; só dev)
	$(COMPOSE) run --rm api python -m app.cli seed

seed-performance: ## Insere em lote 200 usuários e 10.000 chamados para medir o RNF02 (só dev)
	$(COMPOSE) run --rm api python -m app.cli seed-performance

front-install: ## Front: instala as dependências (npm ci)
	cd $(FRONTEND) && npm ci

front-lint: ## Front: ESLint + typecheck (tsc --noEmit)
	cd $(FRONTEND) && npm run lint && npm run typecheck

front-test: ## Front: testes (Vitest)
	cd $(FRONTEND) && npm run test

front-build: ## Front: build de produção (tsc -b && vite build)
	cd $(FRONTEND) && npm run build

front-dev: ## Front: servidor de desenvolvimento (Vite, 127.0.0.1:5173, proxy /api)
	cd $(FRONTEND) && npm run dev

front-gen-api: ## Front: regenera src/api/schema.ts a partir do OpenAPI da API (API no ar)
	cd $(FRONTEND) && npm run gen:api
