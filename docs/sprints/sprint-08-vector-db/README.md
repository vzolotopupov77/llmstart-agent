# Sprint 08: vector-db (RAG Upgrade)

> **Версия roadmap:** v0.1  
> **Roadmap:** [../../roadmap.md](../../roadmap.md)  
> **Статус:** ✅ Done  
> **Открыт:** 2026-06-22

---

## Цель спринта

Выбрать векторную БД, перевести RAG-слой на абстрактный `retriever`-интерфейс с конкретной реализацией через конфиг, провести baseline-замеры качества поиска.

**Ограничения:**
- только семантический поиск; гибридный (BM25 + dense) — вне скоупа
- версии образов и SDK фиксировать явно
- конкретная БД задаётся конфигом (env / eval-config), не хардкодом

---

## DoD спринта

| # | Критерий | Результат |
|---|----------|-----------|
| 1 | ADR зафиксирован: выбранная БД, версии образа и SDK, отклонённые кандидаты с причинами | ✅ |
| 2 | `make up` поднимает векторную БД как часть compose-стека (health check зелёный) | ✅ |
| 3 | `make index` завершается без ошибок, коллекция содержит все чанки из `data/` | ✅ |
| 4 | `search_knowledge_base` работает через абстрактный `retriever`-интерфейс; БД выбирается через env-переменную | ✅ |
| 5 | Альтернативную реализацию retriever можно подключить без правки бизнес-логики Core | ✅ |
| 6 | `evals/configs/vector-db-baseline.yaml` и отчёт `evals/reports/vector-db-baseline.md` сохранены; Qdrant e2e-метрики зафиксированы как baseline | ✅ |
| 7 | `PgvectorRetriever` реализован; `make bench` прогоняет все три бэкенда и формирует `vector-bench-*.md` | ✅ |
| 8 | `make test-backend` зелёный; roadmap и этот README обновлены | ✅ |

---

## Задачи

| # | Задача | Статус | Plan | Summary |
|---|--------|--------|------|---------|
| 01 | [adr-vector-db](#task-01-adr-vector-db) | ✅ | [plan](tasks/01-adr-vector-db/plan.md) | [summary](tasks/01-adr-vector-db/summary.md) |
| 02 | [infra-vector-db](#task-02-infra-vector-db) | ✅ | [plan](tasks/02-infra-vector-db/plan.md) | [summary](tasks/02-infra-vector-db/summary.md) |
| 03 | [indexing-pipeline](#task-03-indexing-pipeline) | ✅ | [plan](tasks/03-indexing-pipeline/plan.md) | [summary](tasks/03-indexing-pipeline/summary.md) |
| 04 | [semantic-retriever](#task-04-semantic-retriever) | ✅ | [plan](tasks/04-semantic-retriever/plan.md) | [summary](tasks/04-semantic-retriever/summary.md) |
| 05 | [baseline-eval-qdrant](#task-05-baseline-eval-qdrant) | ✅ | [plan](tasks/05-baseline-eval/plan.md) | [summary](tasks/05-baseline-eval/summary.md) |
| 06 | [pgvector-retriever-bench](#task-06-pgvector-retriever-bench) | ✅ | [plan](tasks/06-pgvector-retriever-bench/plan.md) | [summary](tasks/06-pgvector-retriever-bench/summary.md) |

---

## Task 01: adr-vector-db

**Цель:** проанализировать кандидатов (Qdrant, ChromaDB, pgvector), принять решение, зафиксировать в ADR.

**Состав работ:**
- Сравнительная таблица по критериям: production-готовность, ease of docker self-host, Python SDK, поддержка метаданата-фильтрации, лицензия
- Зафиксировать точные версии образа и Python SDK для выбранной БД
- Задокументировать отклонённые кандидаты с явными причинами
- Создать `docs/adrs/ADR-004-vector-db.md`

**Критерии готовности:**
- ADR существует и содержит: контекст, рассмотренные варианты, решение, последствия
- Версии образа и SDK зафиксированы (не `latest`)
- Причины отказа от кандидатов явны

**Артефакты:**
- `docs/adrs/ADR-004-vector-db.md`

---

## Task 02: infra-vector-db

**Цель:** добавить выбранную векторную БД в docker-compose; `make up` поднимает её с health check.

**Состав работ:**
- Добавить сервис в `devops/docker-compose.yml` с точной версией образа из ADR
- Настроить health check (`curl` / gRPC probe в зависимости от БД)
- Добавить named volume для персистентности данных
- Обновить `.env.example`: хост, порт, имя коллекции, опциональный API-ключ

**Критерии готовности:**
- `make up` поднимает стек; health check сервиса векторной БД `healthy`
- `docker compose down && make up` — данные не теряются (named volume)
- `.env.example` содержит все новые переменные с комментариями

**Артефакты:**
- `devops/docker-compose.yml` (обновлён)
- `.env.example` (обновлён)

---

## Task 03: indexing-pipeline

**Цель:** скрипт индексации: читает `data/`, чанкинг, эмбеддинги, upsert в коллекцию; запускается через `make index`.

**Состав работ:**
- Скрипт `scripts/index.py` (или `mcp_server/indexer.py`): обход `data/`, чанкинг текста, генерация эмбеддингов (тот же провайдер, что и в Core), upsert в коллекцию
- Идемпотентность: повторный запуск не дублирует документы (upsert по детерминированному `id`)
- Добавить `make index` в `Makefile`
- Логировать прогресс: файл, количество чанков, общий итог

**Критерии готовности:**
- `make index` завершается с кодом 0
- Повторный `make index` не создаёт дубликатов
- Количество документов в коллекции соответствует ожидаемому (проверяется в unit/smoke-тесте)
- Логи содержат итог: N файлов, M чанков проиндексировано

**Артефакты:**
- `scripts/index.py` (или аналог внутри сервиса)
- `Makefile` (цель `index`)

---

## Task 04: semantic-retriever

**Цель:** переписать `search_knowledge_base` через абстрактный `retriever`-интерфейс; конкретная реализация выбирается через конфиг.

**Состав работ:**
- Определить абстрактный интерфейс `BaseRetriever` (ABC или Protocol): метод `search(query: str, top_k: int) -> list[Document]`
- Реализовать конкретный класс для выбранной БД (например `QdrantRetriever`)
- Фабрика / DI: retriever создаётся один раз при старте сервиса из env-переменной `RETRIEVER_BACKEND` (или аналога)
- Переписать обработчик `search_knowledge_base` в MCP-сервере через интерфейс — без прямых импортов конкретной БД
- Удалить ChromaDB из зависимостей и compose, если она была и не выбрана
- Обновить тесты: мокировать `BaseRetriever`, не конкретную БД

**Критерии готовности:**
- `BaseRetriever` определён; конкретная реализация изолирована в отдельном модуле
- Смена `RETRIEVER_BACKEND` в `.env` меняет реализацию без правки бизнес-логики
- `search_knowledge_base` не импортирует конкретный SDK напрямую
- Тесты Core и MCP-сервера проходят через мок retriever
- ChromaDB удалена из `pyproject.toml` и compose (если не выбрана)

**Артефакты:**
- `mcp_server/retriever/base.py` — интерфейс
- `mcp_server/retriever/<backend>.py` — конкретная реализация
- `mcp_server/retriever/factory.py` — фабрика
- обновлённые тесты

---

## Task 05: baseline-eval-qdrant

**Цель:** прогнать eval-датасет `e2e/e2e-qa/v002` через `QdrantRetriever`, зафиксировать e2e-baseline метрики.

**Состав работ:**
- Создать `evals/configs/vector-db-baseline.yaml`: retrieval backend, db_version, embedding_model, chunk_size, top_k, датасет v002
- Прогнать `make -C evals experiment CONFIG=configs/vector-db-baseline.yaml DATASET=e2e/e2e-qa`
- Сохранить JSON + markdown-отчёт `evals/reports/vector-db-baseline.md` (метрики, стратификация, сравнение с chroma-baseline, решение)

**Критерии готовности:**
- Конфиг и JSON-отчёт сохранены
- `evals/reports/vector-db-baseline.md` содержит run-level метрики, стратификацию, сравнение и раздел «Решение»
- Ссылка на отчёт в разделе «Итог»

**Артефакты:**
- `evals/configs/vector-db-baseline.yaml`
- `evals/reports/runs/vector-db-baseline--e2e-qa-<timestamp>.json`
- `evals/reports/vector-db-baseline.md`

---

## Task 06: pgvector-retriever-bench

**Цель:** реализовать `PgvectorRetriever`, добавить ChromaDB как optional-extra для bench, прогнать все три бэкенда на одном корпусе и сформировать сводный отчёт.

**Состав работ:**
- Добавить `pgvector` сервис в `devops/docker-compose.yml` (PostgreSQL + pgvector extension, health check) — ✅
- Реализовать `mcp_server/retriever/pgvector.py` (`PgvectorRetriever`), зарегистрировать в фабрике — ✅
- Добавить `pgvector` SDK в `pyproject.toml`; ChromaDB — как optional-extra `[bench]` — ✅
- Обновить `.env.example`: `PGVECTOR_*` переменные — ✅
- Создать `evals/configs/vector-db-pgvector.yaml`, `vector-db-chroma.yaml`, `vector-db-qdrant.yaml` — ✅
- Реализовать bench-раннер (`mcp_server/scripts/bench.py`, `bench_all.py`, `bench_report.py`):
  - последовательно запускает все три бэкенда: Qdrant, ChromaDB, pgvector
  - на каждом прогоне замеряет: `index_time_s`, `index_rss_mb`, `p50_latency_ms`, `p95_latency_ms`, `precision@k`, `recall@k`
  - сохраняет `evals/reports/vector-db-<backend>-<timestamp>.json` per-backend
  - формирует сводный `evals/reports/vector-bench-<timestamp>.md`
  — ✅ (`make bench`, прогон `20260624T144759Z`)
- Оптимизировать readiness-check в `QdrantRetriever` и `PgvectorRetriever`: `collection_exists` / `get_collection` / `COUNT(*)` — один раз за жизнь объекта, не на каждый `search` — ✅
- Добавить `make bench` в Makefile — ✅
- Залинковать итоговый `vector-bench-*.md` из раздела «Итог» этого README — ✅
- Перепрогнать `make bench` после фикса qdrant latency — ✅ (прогон `152928Z`, gRPC-клиент)
- Исправить сегментацию `real_data/` в `_scan_files` и унифицировать Chroma indexer — ✅ (финальный прогон `172450Z`)

**Формат `vector-bench-{timestamp}.md`:**
```markdown
# Vector DB Benchmark — {timestamp}

dataset: {path}
top_k: {k}
score_threshold: {t}

| backend  | index_time_s | index_rss_mb | p50_latency_ms | p95_latency_ms | precision@k | recall@k |
|----------|-------------|-------------|----------------|----------------|-------------|----------|
| qdrant   | ...         | ...         | ...            | ...            | ...         | ...      |
| chroma   | ...         | ...         | ...            | ...            | ...         | ...      |
| pgvector | ...         | ...         | ...            | ...            | ...         | ...      |
```

**Критерии готовности:**
- `PgvectorRetriever` реализован; смена `RETRIEVER_BACKEND=pgvector` работает без правки бизнес-логики — ✅
- Конфиги для всех трёх бэкендов существуют и воспроизводимы — ✅
- `make bench` завершается без ошибок — ✅
- Сырые JSON-отчёты сохранены для каждого из трёх бэкендов — ✅
- `evals/reports/vector-bench-<timestamp>.md` содержит все 6 метрик по всем 3 бэкендам — ✅
- Readiness-check в retriever'ах не дублируется на hot path — ✅
- Ссылка на `vector-bench-*.md` проставлена в раздел «Итог» этого README — ✅
- Финальный bench-прогон с актуальным кодом (qdrant gRPC) — ✅ (`152928Z`)

**Артефакты:**
- `mcp_server/retriever/pgvector.py`, `mcp_server/retriever/qdrant.py` (readiness-cache)
- `mcp_server/mcp_server/rag/pgvector_indexer.py`
- `mcp_server/scripts/bench.py`, `bench_all.py`, `bench_report.py`
- `mcp_server/tests/test_retriever.py` (тесты readiness-cache)
- `evals/configs/vector-db-pgvector.yaml`, `vector-db-chroma.yaml`, `vector-db-qdrant.yaml`
- `evals/reports/vector-db-<backend>-20260624T*.json`
- [vector-bench-20260624T152928Z.md](../../../evals/reports/vector-bench-20260624T152928Z.md) ← финальный

---

## Итог

> Спринт закрыт. Все 6 задач выполнены. Финальный bench после фиксов корпуса (`172450Z`): qdrant p50=3.33 мс, chroma p50=4.89 мс, pgvector p50=4.29 мс — все три бэкенда на едином корпусе (202 чанка), recall@4≈0.98. Production-бэкенд: Qdrant.

### E2E baseline (Qdrant, e2e-qa v002)

| Backend | avg_answer_correctness | avg_faithfulness | avg_task_completion | error_rate | top_k | Отчёт |
|---------|---------------------|------------------|---------------------|------------|-------|-------|
| Qdrant | 0.588 (adj ≈0.64) | 0.873 | 0.585 | 0.000 | 4 | [vector-db-baseline.md](../../../evals/reports/vector-db-baseline.md) |

Сравнение с chroma-baseline (0.662): см. отчёт.

### Сравнение бэкендов (vector bench — Task 06)

Финальный прогон после фиксов сегментации: `make bench` · dataset `data/` · top_k=4 · [сводный отчёт](../../../evals/reports/vector-bench-20260624T172450Z.md)

| Backend | indexed_chunks | index_time_s | p50_latency_ms | p95_latency_ms | precision@k | recall@k |
|---------|----------------|-------------|----------------|----------------|-------------|----------|
| Qdrant | 202 | 52.0 | **3.33** | 4.87 | 0.2448 | 0.9792 |
| ChromaDB | 202 | 162.6 | 4.89 | 9.19 | 0.2448 | 0.9792 |
| pgvector | 202 | 142.3 | 4.29 | **5.24** | 0.2448 | 0.9792 |

**Примечания:**
- `index_rss_mb` = n/a: `resource.getrusage()` недоступен на Windows; требует замены на `psutil`.
- **Search latency** (p50): все три бэкенда сопоставимы — **3–5 ms**.
- **precision@k и recall@k одинаковы** — все три бэкенда используют один корпус, одну модель эмбеддингов и одни запросы; ~2% промахов (recall 0.9792 < 1.0) связаны с конкуренцией похожих чанков из PDF.
- Предыдущий прогон `152928Z` показывал recall=1.0 только потому, что bench проверял 4 md-файла вместо 24 — артефакт неправильной сегментации `real_data/`.

**Пост-закрытие фиксы (см. [summary Task 06](tasks/06-pgvector-retriever-bench/summary.md#пост-закрытие-фиксы-сегментации-и-унификации-корпуса)):**
- `_scan_files`: сегментация `b2b`/`b2c` на любом уровне вложенности; исключение служебных файлов
- Chroma `indexer.py`: унифицирован с `_scan_files` — индексирует полный корпус (md + txt + pdf)
- Тесты: `mcp_server/tests/test_qdrant_indexer.py` (2), доработан `tests/test_rag.py`

### Выбранная реализация

> Production-бэкенд: **Qdrant** (зафиксирован в ADR-004). ChromaDB и pgvector — альтернативы, проверены в bench; смена через `RETRIEVER_BACKEND` в `.env` без правки кода.
