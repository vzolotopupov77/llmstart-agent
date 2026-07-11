# Summary: Task 05 — method-b-caption

> **План:** [plan.md](./plan.md)
> **Дата закрытия:** 2026-07-10

---

## Что реализовано

- `BCaptionIndexer` (VLM caption → `evals/artifacts/captions/{model_slug}/` → e5 → Qdrant) через контракт Task 03
- Две VLM: **nemotron** (`nvidia/nemotron-nano-12b-v2-vl:free`) и **gemini** (`google/gemini-2.5-flash-lite`) через OpenRouter
- `evals/indexers/caption/` — OpenRouter vision client, pricing cache, preflight, batch с resume
- Hallucination-check: manifest `caption-hallucination/v001_2026-07-10.json` + `caption_hallucination_check.py`
- Конфиги `multimodal-b-caption-nemotron.yaml`, `multimodal-b-caption-gemini.yaml`
- `run_multimodal_b_caption.py` — preflight/smoke → index/eval обеих моделей → hallucination-check → сводный отчёт
- Артефакты: 66×2 `.txt`; Qdrant: `multimodal_caption_nemotron_v002`, `multimodal_caption_gemini_v002`
- Отчёт: `evals/reports/multimodal-b-caption.md`

---

## Принятые решения

| Решение | Причина |
|---------|---------|
| OpenRouter OpenAI-compatible vision API | Единый `OPENAI_API_KEY` / `OPENAI_BASE_URL` как в проекте |
| Промпт: дословные числа, temperature=0 | Снижение риска «молчаливой правки» на S2 |
| Resume: skip existing artifacts | Долгий прогон 66×2; восстановление после сбоев |
| Fallback `qwen/qwen3-vl-8b-instruct` при 429 на `:free` | Лимит OpenRouter free tier 50 req/day на nemotron |
| Отдельные папки артефактов по `model_slug` | Разбор галлюцинаций и сравнение подписей |
| Eval-тесты через `make eval-validate` / `cd evals && uv run pytest` | `make test-backend` не включает `evals/tests/` |

---

## Отклонения от плана

- **Nemotron slides 50–66:** не nemotron, а fallback `qwen/qwen3-vl-8b-instruct` из-за `rate_limit_429_free_tier` (50 req/day). Зафиксировано в header артефактов и отчёте.
- **Пустые `choices` у nemotron free:** периодические retry; не все слайды с первого раза.
- **Gemini быстрее nemotron** (0.66× по `build_time_s`), хотя в плане ожидалась «мощная = медленнее» — факт прогона.

---

## Итог DoD

| # | Критерий | Результат |
|---|----------|-----------|
| 1 | 66 artifacts × 2 + Qdrant + eval 5 сегментов | ✅ |
| 2 | `build_time_s`, `est_cost_usd`, `api_calls` по модели | ✅ nemotron 606s/$0.006; gemini 399s/$0.021 |
| 3 | `hallucination-check.md` slides 10/11 | ✅ 4× «совпадает» |
| 4 | Ответ «да/нет» с цифрами S2/S3 + speed | ✅ **Да** — прирост на S3 (+10pp Recall@5) |
| 5 | Подписи адекватны S2/S3 | ✅ (пользователь) |
| 6 | `mcp_server/` не менялся | ✅ |
| 7 | Тесты evals | ✅ 15 caption-related + 89 total `eval-validate` |

---

## Ключевые метрики (из отчёта)

| | S2 Recall@5 | S3 Recall@5 | build_time_s | est_cost_usd |
|---|---:|---:|---:|---:|
| nemotron | 1.000 | 0.700 | 606 | 0.006 |
| gemini | 1.000 | **0.800** | **399** | 0.021 |

**Вывод:** Gemini оправдывает себя на **S3** (layout); на S2 паритет. Быстрее в 0.66×, дороже ~3.5×. Hallucination-check на chart-слайдах 10/11 — без расхождений чисел.

---

## Запуск

```bash
make eval-multimodal-b-caption        # полный цикл (API cost)
make eval-multimodal CONFIG=configs/multimodal-b-caption-nemotron.yaml
make eval-multimodal CONFIG=configs/multimodal-b-caption-gemini.yaml
```

Тесты Task 05:

```bash
cd evals && uv run pytest tests/test_caption_client.py tests/test_b_caption_indexer.py tests/test_indexer_registry.py -q
```

---

## Артефакты

| Путь | Описание |
|------|----------|
| `evals/indexers/caption/` | VLM client (OpenRouter, pricing, batch) |
| `evals/indexers/b_caption.py` | `BCaptionIndexer` |
| `evals/indexers/registry.py`, `evals/indexers/stubs.py` | Registry update, stub removed |
| `evals/configs/multimodal-b-caption-nemotron.yaml` | Конфиг nemotron |
| `evals/configs/multimodal-b-caption-gemini.yaml` | Конфиг gemini |
| `evals/configs/multimodal-b-caption.yaml` | Deprecated stub |
| `evals/scripts/caption_hallucination_check.py` | Hallucination-check runner |
| `evals/scripts/run_multimodal_b_caption.py` | Orchestrator A/B |
| `evals/datasets/multimodal/caption-hallucination/v001_2026-07-10.json` | Manifest S2 чисел |
| `evals/tests/test_caption_client.py` | Тесты pricing/slug |
| `evals/tests/test_b_caption_indexer.py` | Тесты индексатора |
| `evals/artifacts/captions/nemotron-nano-12b-v2-vl/slide-*.txt` | 66 caption artifacts |
| `evals/artifacts/captions/gemini-2.5-flash-lite/slide-*.txt` | 66 caption artifacts |
| `evals/artifacts/captions/hallucination-check.md` | Вердикты slides 10/11 |
| `evals/reports/multimodal-b-caption.md` | Сводный отчёт |
| `evals/reports/runs/multimodal-b-caption-*.json` | Run JSON |
| `Makefile` | Цель `eval-multimodal-b-caption` |
| `.env.example` | `CAPTION_MODEL`, `OPENAI_API_KEY` |
