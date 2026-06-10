.DEFAULT_GOAL := help

.PHONY: help dev dev-backend dev-frontend dev-bot up down lint format typecheck test test-backend test-mcp test-bot test-frontend ci reindex upload-langfuse-dataset reload-langfuse-dataset

COMPOSE_FILE := devops/docker-compose.yml
BACKEND_PORT ?= 8003
FRONTEND_PORT ?= 3002
DATASET_NAME ?= llmstart-agent-v1
DATASET_SOURCE ?= datasets/b2c/v2/dataset.jsonl

help:
	@echo Usage: make [target] [VAR=value ...]
	@echo.
	@echo Development
	@echo   dev                 Start infra + backend + frontend + bot (Ctrl+C stops all)
	@echo   dev-backend         Backend API only (port $(BACKEND_PORT))
	@echo   dev-frontend        Frontend only (port $(FRONTEND_PORT))
	@echo   dev-bot             Telegram bot only
	@echo.
	@echo Infrastructure
	@echo   up                  Start Docker stack (Langfuse v3, Postgres, etc.)
	@echo   down                Stop Docker stack
	@echo.
	@echo Quality
	@echo   lint                Run all linters (backend, mcp, bot, frontend)
	@echo   lint-backend        Ruff check — backend
	@echo   lint-mcp            Ruff check — mcp_server
	@echo   lint-bot            Ruff check — bot
	@echo   lint-frontend       ESLint — frontend
	@echo   format              Format all Python services
	@echo   format-backend      Ruff format — backend
	@echo   format-mcp          Ruff format — mcp_server
	@echo   format-bot          Ruff format — bot
	@echo   typecheck           Run all type checkers
	@echo   typecheck-backend   mypy — backend
	@echo   typecheck-mcp       mypy — mcp_server
	@echo   typecheck-bot       mypy — bot
	@echo   typecheck-frontend  tsc — frontend
	@echo   ci                  lint + typecheck + test
	@echo.
	@echo Tests
	@echo   test                Run all test suites
	@echo   test-backend        pytest — backend
	@echo   test-mcp            pytest — mcp_server
	@echo   test-bot            pytest — bot
	@echo   test-frontend       vitest + build — frontend
	@echo.
	@echo Data
	@echo   reindex             Rebuild RAG vector index (Chroma)
	@echo   upload-langfuse-dataset   Upload JSONL dataset to Langfuse (upsert)
	@echo   reload-langfuse-dataset     Delete all items and re-upload dataset
	@echo.
	@echo Variables
	@echo   BACKEND_PORT=$(BACKEND_PORT)   Backend listen port
	@echo   FRONTEND_PORT=$(FRONTEND_PORT)  Frontend dev port
	@echo   DATASET_NAME=$(DATASET_NAME)  Langfuse dataset name
	@echo   DATASET_SOURCE=$(DATASET_SOURCE)  Path to JSONL source file

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

upload-langfuse-dataset:
	cd backend && uv run python ../datasets/scripts/upload_langfuse_dataset.py \
		--dataset-name $(DATASET_NAME) \
		--source ../$(DATASET_SOURCE)

reload-langfuse-dataset:
	cd backend && uv run python ../datasets/scripts/upload_langfuse_dataset.py \
		--dataset-name $(DATASET_NAME) \
		--source ../$(DATASET_SOURCE) \
		--reload

test-frontend:
	cd frontend && pnpm test && pnpm build

ci: lint typecheck test
