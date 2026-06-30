.DEFAULT_GOAL := help

.PHONY: help dev dev-backend dev-frontend dev-bot up down lint format typecheck test test-backend test-mcp test-bot test-frontend ci index reindex upload-langfuse-dataset reload-langfuse-dataset eval-validate eval-sync eval-experiment eval-graph-hybrid eval-graph-global eval-graph-routing eval-graph-regression eval-analyze eval-compare eval-backfill-runs bench bench-one graph-up graph-down graph-status graph-shell graph-init-ro graph-seed graph-inspect graph-qa graph-extract graph-compare graph-index

COMPOSE_FILE := devops/docker-compose.yml
BACKEND_PORT ?= 8003
FRONTEND_PORT ?= 3002
DATASET_NAME ?= llmstart-agent-v1
DATASET_SOURCE ?= datasets/b2c/v2/dataset.jsonl
RETRIEVER_BACKEND ?=
BENCH_BACKENDS ?= qdrant chroma pgvector
BENCH_SKIP_INDEX ?=

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
	@echo   graph-up            Start Neo4j only
	@echo   graph-down          Stop Neo4j (data preserved in volume)
	@echo   graph-status        Neo4j container status + connectivity smoke check
	@echo   graph-shell         Interactive cypher-shell (admin user)
	@echo   graph-init-ro       Create read-only text2cypher_ro user (once after graph-up)
	@echo   graph-seed          Load seed.cypher into Neo4j (idempotent)
	@echo   graph-inspect       Node/edge stats, orphans, COVERS coverage
	@echo   graph-qa            Run QA Cypher checks (graph-qa.cypher)
	@echo   graph-extract       Auto-extract themes via SimpleKGPipeline
	@echo   graph-compare       Diff seed vs auto + keyword-recall report
	@echo   graph-index         Full pipeline: graph-seed + graph-extract
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
	@echo   index               Index knowledge base into Qdrant (md, txt, pdf)
	@echo   reindex             Rebuild RAG vector index (Chroma)
	@echo   upload-langfuse-dataset   Upload JSONL dataset to Langfuse (upsert)
	@echo   reload-langfuse-dataset     Delete all items and re-upload dataset
	@echo.
	@echo Eval
	@echo   eval-validate         Pydantic + integrity tests for eval contour
	@echo   eval-sync             Sync datasets to Langfuse (stub until task 04)
	@echo   eval-experiment       Run experiment (CONFIG=..., DATASET=...)
	@echo   eval-graph-hybrid     GraphRAG Task 06 eval hybrid branch (CONFIG=graphrag-graph.yaml)
	@echo   eval-graph-global     GraphRAG Task 06 smoke global branch (CONFIG=graphrag-global-branch.yaml)
	@echo   eval-graph-routing    GraphRAG Task 08 agent routing eval (CONFIG=graphrag-routing.yaml)
	@echo   eval-graph-regression GraphRAG Task 08 fix-loop regression set (CONFIG=graphrag-routing-v5.yaml)
	@echo   eval-analyze          Analyze run report (JSON to markdown)
	@echo   eval-compare          Compare two runs (stub until v0.2)
	@echo   eval-backfill-runs    Backfill Langfuse dataset_run_items from JSON (RUN=optional)
	@echo.
	@echo Bench
	@echo   bench                 Run retriever benchmark for all backends ($(BENCH_BACKENDS))
	@echo   bench RETRIEVER_BACKEND=qdrant  Run benchmark for a single backend
	@echo   bench BENCH_SKIP_INDEX=1        Skip re-index (use after make index)
	@echo.
	@echo Variables
	@echo   BACKEND_PORT=$(BACKEND_PORT)   Backend listen port
	@echo   FRONTEND_PORT=$(FRONTEND_PORT)  Frontend dev port
	@echo   DATASET_NAME=$(DATASET_NAME)  Langfuse dataset name
	@echo   DATASET_SOURCE=$(DATASET_SOURCE)  Path to JSONL source file
	@echo   RETRIEVER_BACKEND=$(RETRIEVER_BACKEND)  Override backend for bench (empty = all)
	@echo   BENCH_SKIP_INDEX=$(BENCH_SKIP_INDEX)  Set to 1 to skip re-index during bench

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
	docker compose --env-file .env -f $(COMPOSE_FILE) pull langfuse-web langfuse-worker
	docker compose --env-file .env -f $(COMPOSE_FILE) up -d

down:
	docker compose --env-file .env -f $(COMPOSE_FILE) down

graph-up:
	docker compose --env-file .env -f $(COMPOSE_FILE) up -d neo4j

graph-down:
	docker compose --env-file .env -f $(COMPOSE_FILE) stop neo4j

graph-status:
	@echo === docker compose ps neo4j ===
	docker compose --env-file .env -f $(COMPOSE_FILE) ps neo4j
	@echo === connectivity ===
	cd mcp_server && uv run python -m scripts.neo4j_smoke

graph-shell:
	cd mcp_server && uv run python -m scripts.neo4j_shell

graph-init-ro:
	cd mcp_server && uv run python -m scripts.neo4j_init_ro

graph-seed:
	cd mcp_server && uv run python -m scripts.neo4j_seed

graph-inspect:
	cd mcp_server && uv run python -m scripts.neo4j_qa --inspect

graph-qa:
	cd mcp_server && uv run python -m scripts.neo4j_qa

graph-extract:
	cd mcp_server && uv run python ../scripts/graph_indexer.py

graph-compare:
	cd mcp_server && uv run python ../scripts/graph_compare.py --output ../data/graph/extraction-report.md

graph-index: graph-seed graph-extract

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

index:
ifdef BACKEND
ifeq ($(BACKEND),qdrant)
	cd mcp_server && uv run python -m mcp_server.rag.qdrant_indexer
else ifeq ($(BACKEND),pgvector)
	cd mcp_server && uv run python -m mcp_server.rag.pgvector_indexer
else ifeq ($(BACKEND),chroma)
	cd mcp_server && uv run python -c "from mcp_server.rag.indexer import reindex; print(f'indexed {reindex()} chunks')"
else
	$(error Unknown BACKEND: $(BACKEND). Use qdrant, chroma, or pgvector)
endif
else
	cd mcp_server && uv run python -m mcp_server.rag.qdrant_indexer
endif

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

eval-validate:
	$(MAKE) -C evals validate

eval-sync:
	$(MAKE) -C evals sync

eval-experiment:
	$(MAKE) -C evals experiment

eval-graph-hybrid:
	@echo Before run: set RETRIEVER_BRANCH=hybrid and RAG_TOP_K=5 in .env, restart backend.
	$(MAKE) -C evals experiment CONFIG=configs/graphrag-graph.yaml DATASET=$(if $(DATASET),$(DATASET),all)

eval-graph-global:
	@echo Before run: set RETRIEVER_BRANCH=global and RAG_TOP_K=5 in .env, restart backend.
	$(MAKE) -C evals experiment CONFIG=configs/graphrag-global-branch.yaml DATASET=$(if $(DATASET),$(DATASET),global)

eval-graph-routing:
	@echo Before run: restart backend with Task 08 tools + prompt v4 (RETRIEVER_BRANCH=vector default).
	$(MAKE) -C evals experiment CONFIG=configs/graphrag-routing.yaml DATASET=$(if $(DATASET),$(DATASET),all)

eval-graph-regression:
	@echo Fix-loop regression set. Default CONFIG=graphrag-routing-v5 (prompt v5); pass CONFIG=configs/graphrag-routing.yaml for v4 baseline.
	@echo Restart backend so config_id is loaded before running.
	$(MAKE) -C evals experiment CONFIG=$(if $(CONFIG),$(CONFIG),configs/graphrag-routing-v5.yaml) DATASET=$(if $(DATASET),$(DATASET),e2e/e2e-regression)

eval-analyze:
	$(MAKE) -C evals analyze

eval-compare:
	$(MAKE) -C evals compare

eval-backfill-runs:
	$(MAKE) -C evals backfill-runs RUN="$(RUN)"

bench:
ifdef RETRIEVER_BACKEND
	cd mcp_server && uv run python -m scripts.bench \
		--config ../evals/configs/vector-db-$(RETRIEVER_BACKEND).yaml \
		--backend $(RETRIEVER_BACKEND) \
		--out ../evals/reports/ \
		$(if $(BENCH_SKIP_INDEX),--skip-index,)
else
	cd mcp_server && uv run python -m scripts.bench_all \
		--backends $(BENCH_BACKENDS) \
		--configs-dir ../evals/configs/ \
		--reports-dir ../evals/reports/ \
		$(if $(BENCH_SKIP_INDEX),--skip-index,)
endif
