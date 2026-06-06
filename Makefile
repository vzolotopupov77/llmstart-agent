.PHONY: dev dev-backend dev-frontend dev-bot up down lint format typecheck test test-backend test-mcp test-bot test-frontend ci reindex

COMPOSE_FILE := devops/docker-compose.yml
BACKEND_PORT ?= 8003
FRONTEND_PORT ?= 3002

dev: up
	@echo "Starting backend (:$(BACKEND_PORT)), frontend (:$(FRONTEND_PORT)), bot. Press Ctrl+C to stop."
	@$(MAKE) -j3 dev-backend dev-frontend dev-bot

dev-backend:
	cd backend && uv run uvicorn app.main:app --host 127.0.0.1 --port $(BACKEND_PORT)

dev-frontend:
	cd frontend && pnpm dev --port $(FRONTEND_PORT)

dev-bot:
	cd bot && uv run python -m bot.main

up:
	docker compose --env-file .env -f $(COMPOSE_FILE) up -d

down:
	docker compose --env-file .env -f $(COMPOSE_FILE) down

lint: lint-backend lint-mcp lint-bot lint-frontend

lint-backend:
	cd backend && uv run ruff check .

lint-mcp:
	cd mcp_server && uv run ruff check .

lint-bot:
	cd bot && uv run ruff check .

lint-frontend:
	cd frontend && pnpm lint

format: format-backend format-mcp format-bot

format-backend:
	cd backend && uv run ruff format .

format-mcp:
	cd mcp_server && uv run ruff format .

format-bot:
	cd bot && uv run ruff format .

typecheck: typecheck-backend typecheck-mcp typecheck-bot typecheck-frontend

typecheck-backend:
	cd backend && uv run mypy .

typecheck-mcp:
	cd mcp_server && uv run mypy .

typecheck-bot:
	cd bot && uv run mypy .

typecheck-frontend:
	cd frontend && pnpm typecheck

test: test-backend test-mcp test-bot test-frontend

test-backend:
	cd backend && uv run pytest

test-mcp:
	cd mcp_server && uv run pytest

test-bot:
	cd bot && uv run pytest

reindex:
	cd mcp_server && uv run python -c "from mcp_server.rag.indexer import reindex; print(f'indexed {reindex()} chunks')"

test-frontend:
	cd frontend && pnpm test && pnpm build

ci: lint typecheck test
