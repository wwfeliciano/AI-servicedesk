# Mentory Help Desk — atalhos de desenvolvimento.
# Os alvos de migrations e seeds entram nos recortes seguintes da F0 e nas fases 1 e 2.

COMPOSE := docker compose
UV := PATH="$(HOME)/.local/bin:$(PATH)" uv
BACKEND := backend

.DEFAULT_GOAL := help
.PHONY: help env config up down ps logs lint format test build migrate migration

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

build: ## Build das imagens Docker (backend: api e worker)
	$(COMPOSE) build

migrate: ## Aplica as migrations no banco (serviço migrate, one-shot)
	$(COMPOSE) run --rm migrate

migration: ## Gera uma migration por autogenerate (make migration nome=descricao) — revisar à mão
	@test -n "$(nome)" || { echo "Uso: make migration nome=descricao_curta"; exit 1; }
	cd $(BACKEND) && $(UV) run alembic revision --autogenerate -m "$(nome)"
