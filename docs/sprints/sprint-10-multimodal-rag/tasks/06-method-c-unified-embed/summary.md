# Summary: Task 06 — method-c-unified-embed

> **План:** [plan.md](./plan.md)
> **Дата закрытия:** 2026-07-11

---

## Что реализовано

- `CUnifiedIndexer` (PNG → VL image embed → Qdrant) через контракт Task 03
- Модель: `nvidia/llama-nemotron-embed-vl-1b-v2:free` (OpenRouter `/embeddings`, dim 2048)
- `evals/indexers/vl_embed/` — OpenRouter VL embed client (image document + text query), batch, preflight
- `QueryEmbedder` Protocol + `VLEmbedder` в `multimodal_retrieval.py` (query-side для метода C)
- `run_multimodal_c_unified.py` — preflight/smoke → index → eval → отчёт C vs B
- Qdrant: `multimodal_unified_vl_v002` (66 points)
- Отчёт: `evals/reports/multimodal-c-unified.md`

---

## Принятые решения

| Решение | Причина |
|---------|---------|
| OpenRouter `/embeddings` с `content` array (image_url / text) | Официальный API для nemotron-embed-vl |
| Smoke embed как gate вместо каталога `/models` | Embed-модели отсутствуют в публичном catalog |
| `embedding_dim: 2048` (не 768) | Фактическая размерность по smoke + model card |
| Отдельный orchestrator (как B) | Не трогаем generic `run_multimodal_eval.py` |
| `$0` pricing fallback при отсутствии в catalog | `:free` tier; cost tracking не блокирует прогон |

---

## Отклонения от плана

- **Pre-flight:** модель `NOT_IN_CATALOG` в `/api/v1/models`, но smoke API OK → статус `SMOKE_OK_NOT_IN_CATALOG`.
- **Гипотеза MIRACL-Vision:** ожидалась просадка C на S1 — **опровергнута** (C Recall@5=1.000 vs best B=0.857).

---

## Итог DoD

| # | Критерий | Результат |
|---|----------|-----------|
| 1 | Коллекция 66 points + eval 5 сегментов | ✅ |
| 2 | `build_time_s`, `est_cost_usd`, `api_calls` | ✅ 207.37s / $0 / 66 |
| 3 | C vs B по каждому сегменту | ✅ |
| 4 | §Гипотеза S1 с числами | ✅ опровергнута |
| 5 | Вывод пользователя | ✅ (2026-07-11) |
| 6 | `mcp_server/` не менялся | ✅ |
| 7 | Тесты evals | ✅ 92 passed |

---

## Ключевые метрики (из отчёта)

| Сегмент | C Recall@5 | best B Recall@5 | Δ |
|---------|----------:|----------------:|---:|
| S1_text | **1.000** | 0.857 (nemotron) | +0.143 |
| S2_chart | 1.000 | 1.000 | 0.000 |
| S3_layout | **0.900** | 0.800 (gemini) | +0.100 |
| S4_multi | 0.833 | 1.000 (nemotron) | −0.167 |

**Вывод:** C обгоняет best B на S1/S3, проигрывает на S4 (multi-hop). Быстрее B (~207s vs 398–606s), но `index_size_mb` выше (0.516 vs 0.193) из-за dim 2048.

---

## Запуск

```bash
make eval-multimodal-c-unified
make eval-multimodal-c-unified --skip-index   # только eval (коллекция уже есть)
```

---

## Артефакты

| Путь | Описание |
|------|----------|
| `evals/indexers/vl_embed/` | VL embed client (OpenRouter, batch, preflight) |
| `evals/indexers/openrouter_common.py` | Shared helpers (API key, image data URL) |
| `evals/indexers/c_unified.py` | `CUnifiedIndexer` |
| `evals/indexers/registry.py` | Registry: `c_unified` → `CUnifiedIndexer` |
| `evals/indexers/stubs.py` | Stub C удалён (остался D) |
| `evals/indexers/factory.py` | Env override `EMBED_VL_MODEL` |
| `evals/scripts/multimodal_retrieval.py` | `QueryEmbedder` + `VLEmbedder` |
| `evals/scripts/run_multimodal_c_unified.py` | Orchestrator + report writer |
| `evals/configs/multimodal-c-unified.yaml` | Конфиг method C (dim 2048) |
| `evals/tests/test_vl_embed_client.py` | Тесты VL embed client |
| `evals/tests/test_c_unified_indexer.py` | Тесты индексатора |
| `evals/tests/test_indexer_registry.py` | Обновлён импорт C |
| `evals/reports/multimodal-c-unified.md` | Сводный отчёт C vs B |
| `evals/reports/runs/multimodal-c-unified-20260711T125339Z.json` | Run JSON |
| `Makefile` | Цель `eval-multimodal-c-unified` |
| `.env.example` | `EMBED_VL_MODEL` |
