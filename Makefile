.DEFAULT_GOAL := help

.PHONY: help dev dev-backend dev-frontend dev-bot up down lint format typecheck test test-backend test-mcp test-bot test-frontend ci index reindex upload-langfuse-dataset reload-langfuse-dataset eval-validate eval-sync eval-experiment eval-multimodal-baseline eval-multimodal eval-multimodal-a-ocr eval-multimodal-b-caption eval-multimodal-c-unified eval-multimodal-d-multivector ocr-build ocr-run-tesseract ocr-run-easyocr eval-graph-hybrid eval-graph-global eval-graph-routing eval-graph-regression eval-analyze eval-compare eval-backfill-runs bench bench-one graph-up graph-down graph-status graph-shell graph-init-ro graph-seed graph-inspect graph-qa graph-extract graph-compare graph-index

COMPOSE_FILE := devops/docker-compose.yml
OCR_COMPOSE_FILE := devops/docker-compose.ocr.yml
REPO_ROOT := $(CURDIR)
ifeq ($(OS),Windows_NT)
  UV := $(REPO_ROOT)/scripts/uv.cmd
else
  UV ?= uv
endif
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
	@echo                       PULL=1 to force langfuse image pull before start
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
	@echo   eval-multimodal-baseline  Sprint-10 naive text baseline (PDF layer to e5 to Qdrant)
	@echo   eval-multimodal           Sprint-10 multimodal eval (CONFIG=evals/configs/multimodal-baseline.yaml)
	@echo   eval-multimodal-a-ocr     Sprint-10 method A: Tesseract (docker) + RapidOCR (local) + CER
	@echo   eval-multimodal-b-caption Sprint-10 method B: Nemotron + Gemini VLM caption + hallucination check
	@echo   eval-multimodal-c-unified Sprint-10 method C: VL image embed + C vs B report
	@echo   eval-multimodal-d-multivector Sprint-10 method D: Jina multivector + TEDS + D vs C/B
	@echo   ocr-build                 Build OCR docker images (Tesseract; EasyOCR/RapidOCR optional)
	@echo   ocr-run-tesseract         OCR batch via docker to evals/artifacts/ocr/tesseract
	@echo   ocr-run-easyocr           OCR batch via docker to evals/artifacts/ocr/easyocr
	@echo   ocr-run-rapidocr          OCR batch via docker to evals/artifacts/ocr/rapidocr
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
	cd backend && $(UV) run uvicorn app.main:app --host 127.0.0.1 --port $(BACKEND_PORT)

dev-frontend:
	cd frontend && pnpm dev --port $(FRONTEND_PORT)

dev-bot:
	cd bot && $(UV) run python -m bot.main

PULL ?= 0

up:
ifeq ($(PULL),1)
	docker compose --env-file .env -f $(COMPOSE_FILE) pull langfuse-web langfuse-worker
endif
	docker compose --env-file .env -f $(COMPOSE_FILE) up -d --pull missing --wait

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
	cd mcp_server && $(UV) run python -m scripts.neo4j_smoke

graph-shell:
	cd mcp_server && $(UV) run python -m scripts.neo4j_shell

graph-init-ro:
	cd mcp_server && $(UV) run python -m scripts.neo4j_init_ro

graph-seed:
	cd mcp_server && $(UV) run python -m scripts.neo4j_seed

graph-inspect:
	cd mcp_server && $(UV) run python -m scripts.neo4j_qa --inspect

graph-qa:
	cd mcp_server && $(UV) run python -m scripts.neo4j_qa

graph-extract:
	cd mcp_server && $(UV) run python ../scripts/graph_indexer.py

graph-compare:
	cd mcp_server && $(UV) run python ../scripts/graph_compare.py --output ../data/graph/extraction-report.md

graph-index: graph-seed graph-extract

lint: lint-backend lint-mcp lint-bot lint-frontend

lint-backend:
	cd backend && $(UV) run ruff check .

lint-mcp:
	cd mcp_server && $(UV) run ruff check .

lint-bot:
	cd bot && $(UV) run ruff check .

lint-frontend:
	cd frontend && pnpm lint

format: format-backend format-mcp format-bot

format-backend:
	cd backend && $(UV) run ruff format .

format-mcp:
	cd mcp_server && $(UV) run ruff format .

format-bot:
	cd bot && $(UV) run ruff format .

typecheck: typecheck-backend typecheck-mcp typecheck-bot typecheck-frontend

typecheck-backend:
	cd backend && $(UV) run mypy .

typecheck-mcp:
	cd mcp_server && $(UV) run mypy .

typecheck-bot:
	cd bot && $(UV) run mypy .

typecheck-frontend:
	cd frontend && pnpm typecheck

test: test-backend test-mcp test-bot test-frontend

test-backend:
	cd backend && $(UV) run pytest

test-mcp:
	cd mcp_server && $(UV) run pytest

test-bot:
	cd bot && $(UV) run pytest

reindex:
	cd mcp_server && $(UV) run python -c "from mcp_server.rag.indexer import reindex; print(f'indexed {reindex()} chunks')"

index:
ifdef BACKEND
ifeq ($(BACKEND),qdrant)
	cd mcp_server && $(UV) run python -m mcp_server.rag.qdrant_indexer
else ifeq ($(BACKEND),pgvector)
	cd mcp_server && $(UV) run python -m mcp_server.rag.pgvector_indexer
else ifeq ($(BACKEND),chroma)
	cd mcp_server && $(UV) run python -c "from mcp_server.rag.indexer import reindex; print(f'indexed {reindex()} chunks')"
else
	$(error Unknown BACKEND: $(BACKEND). Use qdrant, chroma, or pgvector)
endif
else
	cd mcp_server && $(UV) run python -m mcp_server.rag.qdrant_indexer
endif

upload-langfuse-dataset:
	cd backend && $(UV) run python ../datasets/scripts/upload_langfuse_dataset.py \
		--dataset-name $(DATASET_NAME) \
		--source ../$(DATASET_SOURCE)

reload-langfuse-dataset:
	cd backend && $(UV) run python ../datasets/scripts/upload_langfuse_dataset.py \
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

eval-multimodal-baseline:
	cd evals && $(UV) sync && $(UV) run python -m scripts.run_multimodal_eval --config configs/multimodal-baseline.yaml

eval-multimodal:
	cd evals && $(UV) sync && $(UV) run python -m scripts.run_multimodal_eval --config $(if $(CONFIG),$(CONFIG),configs/multimodal-baseline.yaml)

ocr-build:
	docker compose -f $(OCR_COMPOSE_FILE) build

ocr-run-tesseract:
	docker compose -f $(OCR_COMPOSE_FILE) run --rm ocr-tesseract

ocr-run-easyocr:
	docker compose -f $(OCR_COMPOSE_FILE) run --rm ocr-easyocr

ocr-run-rapidocr:
	docker compose -f $(OCR_COMPOSE_FILE) run --rm ocr-rapidocr

eval-multimodal-a-ocr:
	cd evals && $(UV) sync --group ocr-modern && $(UV) run python -m scripts.run_multimodal_a_ocr

eval-multimodal-b-caption:
	cd evals && $(UV) sync && $(UV) run python -m scripts.run_multimodal_b_caption

eval-multimodal-c-unified:
	cd evals && $(UV) sync && $(UV) run python -m scripts.run_multimodal_c_unified

eval-multimodal-d-multivector:
	cd evals && $(UV) sync && $(UV) run python -m scripts.run_multimodal_d_multivector

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
	cd mcp_server && $(UV) run python -m scripts.bench \
		--config ../evals/configs/vector-db-$(RETRIEVER_BACKEND).yaml \
		--backend $(RETRIEVER_BACKEND) \
		--out ../evals/reports/ \
		$(if $(BENCH_SKIP_INDEX),--skip-index,)
else
	cd mcp_server && $(UV) run python -m scripts.bench_all \
		--backends $(BENCH_BACKENDS) \
		--configs-dir ../evals/configs/ \
		--reports-dir ../evals/reports/ \
		$(if $(BENCH_SKIP_INDEX),--skip-index,)
endif
