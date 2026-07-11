# Task 02: datasets-metrics-baseline

> **Sprint:** [../../README.md](../../README.md)
> **Тип:** eval + docs
> **Spec:** [analysis.md](../../analysis.md)

---

## Цель

Собрать сегментный eval-датасет (38→36 вопросов после правок Task 01), описать три группы метрик, прогнать naive text baseline (PDF text layer → e5 → Qdrant) и зафиксировать боль по сегментам.

---

## Состав работ

- [x] Финализировать `evals/datasets/multimodal/multimodal-rag/v001_2026-07-05.json`: `required_slides`, эталоны сверены с PNG; исключены S1-5, S2-1/2, S3-11; S1 дополнен до 7.
- [x] `metric_map.md`: retrieval / ingestion-quality (CER, TEDS) / generation (опц.); S5 — `correct_refusal_rate`, не nDCG.
- [x] Эмбеддер: `intfloat/multilingual-e5-base` (pinned), dim=768, префиксы query/passage.
- [x] `corpus/text_naive/` — извлечение PDF (66 стр., text layer пуст → пустые `.txt` + метаданные).
- [x] Скрипт `run_multimodal_baseline.py`: индекс Qdrant `multimodal_text_naive_v001`, retrieval eval по сегментам.
- [x] `evals/configs/multimodal-baseline.yaml`, отчёт `evals/reports/multimodal-baseline.md`, ссылка в `docs/eval/README.md`.

---

## DoD

| # | Критерий |
|---|----------|
| 1 | Датасет: 5 сегментов, `required_slides` заполнены, эталоны с PNG |
| 2 | `metric_map.md`: 3 группы метрик с формулами |
| 3 | Baseline прогоняется; отчёт — метрики **по сегментам**, не общий средний |
| 4 | S5: primary metric = refusal (generation); retrieval — только diagnostic |

---

## Scope

**Трогаем:** `evals/datasets/multimodal/**`, `evals/scripts/multimodal_*`, `evals/configs/multimodal-baseline.yaml`, `corpus/text_naive/**`, sprint `metric_map.md`, `docs/eval/README.md`, `Makefile` (цель baseline).

**НЕ трогаем:** `mcp_server` retriever/indexer (Task 03), `notes.md` в eval.
