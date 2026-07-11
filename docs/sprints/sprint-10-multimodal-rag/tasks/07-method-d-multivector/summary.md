# Summary: Task 07 — method-d-multivector

> **План:** [plan.md](./plan.md)
> **Дата закрытия:** 2026-07-11

---

## Что реализовано

- `DMultivectorIndexer` (PNG → Jina v4 multivector → Qdrant MAX_SIM) через контракт Task 03
- Модель: `jina-embeddings-v4`, `token_dim=128`, `return_multivector=true`
- `evals/indexers/jina_multivector/` — Jina API client (image passage + text query, batch, preflight)
- `JinaMultivectorEmbedder` в `multimodal_retrieval.py` (query-side multivector + ветка MAX_SIM search)
- TEDS pipeline: golden manifest + VLM structure extract + `teds_score.py` (slides 10/11)
- `run_multimodal_d_multivector.py` — preflight/smoke → index → eval → TEDS → отчёт D vs C/B
- Qdrant: `multimodal_multivector_jina_v002` (66 points)
- Отчёт: `evals/reports/multimodal-d-multivector.md`

---

## Принятые решения

| Решение | Причина |
|---------|---------|
| `embedding_dim: 128` (не 768 из stub Task 03) | Фактическая per-token размерность Jina v4 multivector |
| Upsert по 1 point | Лимит Qdrant ~33 MB на batch с multivector |
| Отдельный orchestrator (как B/C) | Не трогаем generic `run_multimodal_eval.py` |
| TEDS как диагностика ingestion | Не смешивается с retrieval-скором (metric_map) |
| VLM-HTML для hyp (не OCR) | Отдельный diagnostic-шаг структуры chart-слайдов |

---

## Отклонения от плана

- **Jina API response:** multivector в поле `embeddings`, не `embedding` — поправлен client.
- **`.env`:** inline-комментарий на строке `JINA_API_KEY` ломал httpx — strip при чтении.
- **Гипотеза S2/S3:** ожидался прирост multivector на chart/layout — **не подтверждена** (S2 паритет с C/B, S3 = C).
- **TEDS=0.000:** VLM-HTML не совпал с ручным golden — метрика зафиксирована, но интерпретация ограничена качеством hyp-pipeline.

---

## Итог DoD

| # | Критерий | Результат |
|---|----------|-----------|
| 1 | Коллекция 66 points, MAX_SIM | ✅ |
| 2 | Eval 38 items, поиск без ошибок | ✅ |
| 3 | Eval по всем 5 сегментам | ✅ |
| 4 | `build_time_s`, `index_size_mb`, `est_cost_usd`, `api_calls` | ✅ 631.11s / 24.202 MB / $0.026 / 66 |
| 5 | TEDS slides 10/11 + golden + hyp | ✅ TEDS=0.000 |
| 6 | Отчёт D vs C/B по сегментам + cost multipliers | ✅ |
| 7 | §Гипотеза S2/S3 с числами | ✅ не подтверждена |
| 8 | `mcp_server/` не менялся | ✅ |
| 9 | Тесты evals | ✅ 96 passed |
| 10 | Вывод пользователя | ✅ (2026-07-11) |

---

## Ключевые метрики (из отчёта)

| Сегмент | D Recall@5 | C Recall@5 | best B Recall@5 |
|---------|----------:|-----------:|----------------:|
| S1_text | 1.000 | 1.000 | 0.857 |
| S2_chart | 1.000 | 1.000 | 1.000 |
| S3_layout | 0.900 | 0.900 | 0.800 |
| S4_multi | 1.000 | 0.833 | 1.000 |

**Cost:** `index_size_mb` **24.2** (46.9× vs C), `build_time_s` **631** (3.0× vs C), `est_cost_usd` **$0.026**.

**Вывод:** multivector не оправдан по цене на S2/S3. Единственный явный прирост D над C — S4 Recall +0.167. Для этого корпуса late-interaction не даёт выигрыша на chart/layout при ~47× storage.

---

## Запуск

```bash
make eval-multimodal-d-multivector
cd evals && uv run python -m scripts.run_multimodal_d_multivector --skip-index   # только eval + TEDS
```

Требуется `JINA_API_KEY` в `.env` (только значение ключа, без inline-комментария).

---

## Артефакты

| Путь | Описание |
|------|----------|
| `evals/indexers/jina_multivector/` | Jina multivector client (client, preprocess, factory) |
| `evals/indexers/d_multivector.py` | `DMultivectorIndexer` |
| `evals/indexers/registry.py` | Registry: `d_multivector` → `DMultivectorIndexer` |
| `evals/indexers/factory.py` | `require_jina_key`, `D_MAX_SIDE` env |
| `evals/scripts/multimodal_retrieval.py` | `JinaMultivectorEmbedder` + MAX_SIM search |
| `evals/scripts/run_multimodal_d_multivector.py` | Orchestrator + report writer |
| `evals/scripts/teds_score.py` | TEDS scoring |
| `evals/scripts/teds_structure_extract.py` | VLM → HTML structure extract |
| `evals/configs/multimodal-d-multivector.yaml` | Конфиг method D (dim 128) |
| `evals/datasets/multimodal/teds-golden/v001_2026-07-11.json` | TEDS golden manifest |
| `evals/datasets/multimodal/teds-golden/refs/slide-10.html` | Ручная эталонная разметка slide 10 |
| `evals/datasets/multimodal/teds-golden/refs/slide-11.html` | Ручная эталонная разметка slide 11 |
| `evals/artifacts/multivector/teds-hyp/slide-10.html` | VLM hypothesis slide 10 |
| `evals/artifacts/multivector/teds-hyp/slide-11.html` | VLM hypothesis slide 11 |
| `evals/tests/test_jina_multivector_client.py` | Тесты Jina client |
| `evals/tests/test_d_multivector_indexer.py` | Тесты индексатора |
| `evals/tests/test_indexer_registry.py` | Registry update |
| `evals/reports/multimodal-d-multivector.md` | Сводный отчёт D vs C/B + TEDS |
| `evals/reports/runs/multimodal-d-multivector-20260711T155309Z.json` | Run JSON |
| `Makefile` | Цель `eval-multimodal-d-multivector` |
| `.env.example` | `JINA_API_KEY`, `D_MAX_SIDE` |
