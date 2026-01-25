ENV_FILE ?= .env
OUT_DIR ?= $(shell pwd)/out
COMPOSE = docker compose --env-file $(ENV_FILE)
.PHONY: up down logs migrate seed smoke llm_smoke gen_one gen_10 test test_e2e

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
	$(COMPOSE) run --rm worker python -m app.scripts.smoke

llm_smoke:
	$(COMPOSE) run --rm worker python -m app.scripts.llm_smoke

gen_one:
	mkdir -p $(OUT_DIR)
	$(COMPOSE) run --rm -v $(OUT_DIR):/out worker python -m app.scripts.gen_one --download /out/clip_final.mp4

gen_10:
	$(COMPOSE) run --rm -e FORCE_RUBRIC_ID=$(RUBRIC_ID) worker python -m app.scripts.gen_10 --count 10

test:
	$(COMPOSE) run --rm api pytest -q

test_e2e:
	$(COMPOSE) run --rm worker python -m app.scripts.smoke
