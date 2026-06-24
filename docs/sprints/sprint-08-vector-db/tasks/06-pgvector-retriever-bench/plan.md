# Task 06: pgvector-retriever-bench

> **Sprint:** [../../README.md](../../README.md)
> **Тип:** feat
> **Ветка:** `feat/eval-6-pgvector-retriever-bench`
> **Spec:** без spec

---

## Цель

Реализовать `PgvectorRetriever`, добавить ChromaDB как optional-extra для bench, прогнать все три
бэкенда (Qdrant, ChromaDB, pgvector) на одном корпусе, сформировать сводный отчёт; заодно убрать
шум `RuntimeError: Event loop is closed` в eval-логах через sync judge wrapper.

---

## Состав работ

### A. Sync judge wrapper (eval-контур, fix)

- [ ] Добавить класс `SyncOpenRouterJudge(OpenRouterModel)` в `evals/scripts/judge_client.py`:
  переопределить `_generate()` через sync `OpenAI` client (`load_model(async_mode=False)`),
  полностью убрав путь через `asyncio.run()` / `AsyncOpenAI`
- [ ] Обновить `create_judge_model()`: возвращать `SyncOpenRouterJudge` вместо `OpenRouterModel`
- [ ] Добавить тесты в `evals/tests/test_evaluators.py`:
  - `test_create_judge_model_returns_sync_judge` — проверить тип возврата
  - `test_sync_judge_uses_sync_client` — замокать `OpenAI` (sync), убедиться что `AsyncOpenAI`
    не вызывается
- [ ] `uv run ruff check --fix` + `uv run ruff format` на изменённые файлы
- [ ] `make -C evals validate` зелёный

### B. Инфраструктура pgvector

- [ ] Добавить сервис `pgvector` в `devops/docker-compose.yml`:
  `pgvector/pgvector:pg17` (или актуальный образ из ADR), health check `pg_isready`
- [ ] Добавить named volume для персистентности
- [ ] Обновить `.env.example`: `PGVECTOR_HOST`, `PGVECTOR_PORT`, `PGVECTOR_DB`, `PGVECTOR_USER`,
  `PGVECTOR_PASSWORD`, `PGVECTOR_TABLE`

### C. PgvectorRetriever

- [ ] Реализовать `mcp_server/mcp_server/retriever/pgvector.py` (`PgvectorRetriever`):
  подключение к PostgreSQL+pgvector, метод `search(query, segment, top_k) -> list[KnowledgeChunk]`
- [ ] Оптимизировать readiness-check в `QdrantRetriever` и `PgvectorRetriever`:
  `collection_exists` / `get_collection` / `COUNT(*)` — один раз за жизнь объекта, не на каждый search
  (убирает ~11 мин лишней latency в `make bench` для qdrant)
- [ ] Добавить `pgvector` SDK в `mcp_server/pyproject.toml`
- [ ] Зарегистрировать `"pgvector"` в `mcp_server/mcp_server/retriever/factory.py`
- [ ] Добавить тест в `mcp_server/tests/test_retriever.py`: `test_get_retriever_pgvector`

### D. Eval-конфиги и indexer для pgvector

- [ ] Создать `evals/configs/vector-db-chroma.yaml` (зеркало vector-db-baseline с `backend: chroma`)
- [ ] Создать `evals/configs/vector-db-pgvector.yaml`
- [ ] Реализовать `mcp_server/mcp_server/rag/pgvector_indexer.py` (или расширить существующий):
  индексация в pgvector таблицу; запускается через `make index BACKEND=pgvector`

### E. vector_bench.py + make bench

- [ ] Реализовать `evals/scripts/vector_bench.py`:
  - последовательно: Qdrant → ChromaDB → pgvector
  - замеряет на каждом: `index_time_s`, `index_rss_mb`, `p50_latency_ms`, `p95_latency_ms`,
    `precision@k`, `recall@k`
  - сохраняет `evals/reports/vector-db-<backend>-<timestamp>.json` per-backend
  - формирует `evals/reports/vector-bench-<timestamp>.md`
- [ ] Добавить `make bench` / `make bench RETRIEVER_BACKEND=qdrant` в `Makefile` (уже частично есть,
  убедиться что работает с новыми конфигами)

### F. Финализация

- [ ] Ссылка на `vector-bench-*.md` в разделе «Итог» sprint README
- [ ] Обновить `docs/roadmap.md` если спринт закрывается
- [ ] Самопроверка по всем DoD
- [ ] (после «ок» пользователя) Создать `summary.md`, обновить sprint README

---

## Критерии готовности (DoD)

| # | Критерий | Способ проверки |
|---|----------|-----------------|
| 1 | `SyncOpenRouterJudge` возвращается из `create_judge_model()`; в логах нет `Event loop is closed` при judge-вызовах | `make -C evals validate` |
| 2 | `PgvectorRetriever` реализован; `RETRIEVER_BACKEND=pgvector` работает без правки бизнес-логики | `cd mcp_server && uv run pytest tests/test_retriever.py` |
| 3 | `make up` поднимает pgvector; health check зелёный | `docker compose ps` |
| 4 | Конфиги `vector-db-chroma.yaml` и `vector-db-pgvector.yaml` существуют и загружаются | `make -C evals validate` |
| 5 | `make bench` завершается без ошибок; сырые JSON-отчёты сохранены для 3 бэкендов | `make bench` |
| 6 | `evals/reports/vector-bench-<timestamp>.md` содержит все 6 метрик по 3 бэкендам | просмотр отчёта |
| 7 | Lint проходит | `make lint` |
| 8 | Тесты проходят | `make test-backend && make -C evals validate` |

---

## Артефакты

- `evals/scripts/judge_client.py` — `SyncOpenRouterJudge` + обновлённый `create_judge_model`
- `evals/tests/test_evaluators.py` — 2 новых теста для sync judge
- `devops/docker-compose.yml` — сервис pgvector
- `.env.example` — `PGVECTOR_*` переменные
- `mcp_server/mcp_server/retriever/pgvector.py` — `PgvectorRetriever`
- `mcp_server/pyproject.toml` — зависимость `pgvector`
- `mcp_server/mcp_server/retriever/factory.py` — регистрация `pgvector`
- `mcp_server/tests/test_retriever.py` — тест `pgvector`
- `evals/configs/vector-db-chroma.yaml`
- `evals/configs/vector-db-pgvector.yaml`
- `evals/scripts/vector_bench.py`
- `evals/reports/vector-db-<backend>-<timestamp>.json` × 3
- `evals/reports/vector-bench-<timestamp>.md`

---

## Scope

**Трогаем:** файлы из списка «Артефакты».

**НЕ трогаем:**
- `evals/scripts/evaluators.py` — публичный API не меняется (judge model передаётся как объект)
- `mcp_server/mcp_server/rag/indexer.py` — Chroma indexer не трогаем, только pgvector
- `backend/` — никаких изменений
- `frontend/` — никаких изменений

---

## Риски и допущения

- `deepeval 4.0.6`: `OpenRouterModel.load_model(async_mode=False)` возвращает sync `OpenAI` —
  проверено по исходникам `gateway_model.py`; если API изменится в новой версии — нужен адаптер
- Chroma как optional-extra: если `chromadb` не установлен в eval-venv, тест `chroma`-бэкенда
  пропускается через `pytest.importorskip`
- pgvector image: использовать `pgvector/pgvector:pg17` (актуальный на дату задачи)

---

## Открытые вопросы

- [ ] Нужен ли `pgvector_indexer.py` отдельным файлом или достаточно расширить `qdrant_indexer` паттерном?
- [ ] `make bench` запускать все 3 бэкенда последовательно или только тот, что в `RETRIEVER_BACKEND`?
  (Makefile уже имеет логику с `BENCH_BACKENDS` — уточнить)
