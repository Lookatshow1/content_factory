ENV_FILE ?= .env
COMPOSE = docker compose --env-file $(ENV_FILE)
.PHONY: up down logs migrate seed smoke test test_e2e

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f --tail=200

migrate:
	$(COMPOSE) run --rm api alembic upgrade head

seed:
	$(COMPOSE) run --rm api python -m app.seed.seed

smoke:
	$(COMPOSE) run --rm api python -m app.scripts.smoke

test:
	$(COMPOSE) run --rm api pytest -q

test_e2e:
	$(COMPOSE) run --rm api python -m app.scripts.smoke
