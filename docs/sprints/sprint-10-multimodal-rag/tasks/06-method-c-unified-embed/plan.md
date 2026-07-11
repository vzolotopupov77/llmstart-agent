# Task 06: method-c-unified-embed

> **Sprint:** [../../README.md](../../README.md)
> **Тип:** feat (eval / ingestion)
> **Spec:** [analysis.md](../../analysis.md), [metric_map.md](../../metric_map.md)
> **Предшественник:** [Task 05 summary](../05-method-b-caption/summary.md)

---

## Цель

Реализовать метод C под контракт индексатора: **PNG → VL image-embed (OpenRouter, без промежуточного текста) → Qdrant**. Прогнать eval по 5 сегментам, зафиксировать `build_time_s` / `est_cost_usd` и дать **числовой вердикт**: подтверждается ли гипотеза просадки unified image-embedder на плотном русском S1 (MIRACL-Vision) относительно метода B.

---

## Архитектура

```mermaid
flowchart LR
  PNG["data/multimodal-rag/slide-*.png"]
  VL["VLEmbedClient\nOpenRouter /embeddings"]
  IDX["CUnifiedIndexer.build_index"]
  QD["Qdrant\nmultimodal_unified_vl_v002"]
  RET["run_retrieval_eval\nVLEmbedder.embed_queries"]
  RPT["multimodal-c-unified.md\nC vs B"]

  PNG --> VL --> IDX --> QD
  QD --> RET --> RPT
```

| Слой | Меняется? | Комментарий |
|------|-----------|-------------|
| `evals/indexers/vl_embed/` | ✅ новый | OpenRouter embeddings API (text query + image document) |
| `evals/indexers/c_unified.py` | ✅ stub → full | Паттерн Qdrant upsert как `b_caption.py` |
| `multimodal_retrieval.py` | минимально | `QueryEmbedder` Protocol + `VLEmbedder` |
| `run_multimodal_eval.py` | ❌ | C — отдельный orchestrator, как B |
| `mcp_server/` | ❌ | Prod не трогаем |

### Модель

| Параметр | Значение |
|----------|----------|
| model_id | `nvidia/llama-nemotron-embed-vl-1b-v2:free` |
| API | `POST https://openrouter.ai/api/v1/embeddings` |
| Index input | image_url (data URL) |
| Query input | text |
| embedding_dim | **2048** (smoke verify) |

---

## Состав работ

- [x] `evals/indexers/vl_embed/` — OpenRouter embeddings client, batch, preflight
- [x] `evals/indexers/c_unified.py` — `CUnifiedIndexer`; обновить registry/stubs
- [x] `multimodal_retrieval.py` — `QueryEmbedder` Protocol + `VLEmbedder`
- [x] `evals/scripts/run_multimodal_c_unified.py` + отчёт `multimodal-c-unified.md`
- [x] YAML (dim 2048), `EMBED_VL_MODEL` env, Makefile, тесты
- [x] Pre-flight + полный прогон `make eval-multimodal-c-unified`
- [x] Самопроверка по DoD (пользователь: 2026-07-11)

---

## DoD

| # | Критерий | Способ проверки |
|---|----------|-----------------|
| 1 | Коллекция `multimodal_unified_vl_v002` создана, 66 points | Qdrant / run JSON |
| 2 | Eval по всем 5 сегментам (v002, 38 items) | run JSON aggregates |
| 3 | `build_time_s`, `est_cost_usd`, `api_calls` зафиксированы | отчёт + run JSON |
| 4 | Отчёт содержит C vs B по **каждому** сегменту | `multimodal-c-unified.md` |
| 5 | §Гипотеза S1: вердикт с числами | отчёт §Гипотеза |
| 6 | `git diff mcp_server/` = 0 | `git diff --stat mcp_server/` |
| 7 | Тесты evals зелёные | `cd evals && uv run pytest` |

---

## Scope

**Трогаем:** `evals/indexers/vl_embed/`, `c_unified.py`, `multimodal_retrieval.py`, `run_multimodal_c_unified.py`, configs, tests, Makefile, `.env.example`, reports.

**НЕ трогаем:** `mcp_server/**`, датасет v002, методы A/B артефакты, method D, `docs/roadmap.md`, `run_multimodal_eval.py`.

---

## Риски и митигация

| Риск | Митигация |
|------|-----------|
| embedding_dim 768 вместо 2048 | Smoke embed slide-01 |
| Rate limit `:free` | Retry/backoff; fallback на paid slug |
| Модель недоступна | Pre-flight fail-fast |
