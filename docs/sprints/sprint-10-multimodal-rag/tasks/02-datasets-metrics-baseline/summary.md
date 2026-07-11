# Summary: Task 02 — datasets-metrics-baseline

> **План:** [plan.md](./plan.md)
> **Дата закрытия:** 2026-07-05
> **Changelog датасета:** [v002-changelog.md](../../../../../evals/datasets/multimodal/multimodal-rag/v002-changelog.md)

---

## Что реализовано

- Eval-датасет **v002** (38 items, 5 сегментов S1–S5), эталоны с PNG
- `metric_map.md` — три группы метрик (retrieval / ingestion-quality / generation)
- Naive text baseline: PDF layer (0/66) → `multilingual-e5-base` → Qdrant `multimodal_text_naive_v002`
- Скрипты eval, конфиг, тесты, отчёт baseline по сегментам
- Интеграция в `docs/eval/README.md`, `docs/eval/metrics-map.md`, `docs/eval/dataset-map.md`

---

## Что сделано (кратко)

- v001 → **v002** после dataset-reviewer: `trap_slides` для S5, `multi_type` для S4, перефразы, S2-9 (slide 10).
- User edits: S1-6 (slide 27, 10x), S4-2 (5 gold-slides, упрощённый вопрос).
- Validation sample PNG: S5×6, S2-9, S1-6/7, S4-2 — пользователь, 2026-07-05.
- Baseline re-run на v002; нулевая линия зафиксирована (≈0 + шум при пустом PDF).

---

## Отклонения от плана

- Финальный датасет — **v002**, не v001 (иммутабельность + reviewer).
- S2: **9** items (не 8) — добавлен S2-9.
- Collection Qdrant: `multimodal_text_naive_v002` (не v001).
- `summary.md` и закрытие — после явного «ок» пользователя.

---

## Принятые решения

| Решение | Причина |
|---------|---------|
| S5: `trap_slides`, не `required_slides` | Разная семантика gold vs ловушка |
| S5 primary = `correct_refusal_rate`, не nDCG | Отказ — generation, не retrieval |
| e5 pinned в Task 02 | Общий эмбеддер baseline/A/B до Task 03 |
| S4-2: max 5 gold-slides | set-Recall@k при k=5 |
| Baseline без notes | Честный eval визуального корпуса |

---

## Итог DoD

| # | Критерий | Результат |
|---|----------|-----------|
| 1 | Датасет: 5 сегментов, эталоны с PNG | ✅ v002, 38 items |
| 2 | `metric_map.md`: 3 группы метрик | ✅ |
| 3 | Baseline прогоняется; метрики по сегментам | ✅ re-run 2026-07-05 |
| 4 | S5: refusal primary, retrieval — diagnostic | ✅ |
| — | User validation sample | ✅ |
| — | User-check baseline правдоподобен | ✅ |

---

## Ссылки

- [metric_map.md](../../metric_map.md)
- [multimodal-baseline.md](../../../../../evals/reports/multimodal-baseline.md)
- Следующая задача: [Task 03](../../README.md#task-03-indexer-contract-configs)

---

## Артефакты

| Путь | Описание |
|------|----------|
| `evals/datasets/multimodal/multimodal-rag/v002_2026-07-05.json` | Eval-датасет v002 |
| `evals/datasets/multimodal/multimodal-rag/v001_2026-07-05.json` | Предыдущая версия (immutable) |
| `evals/datasets/multimodal/multimodal-rag/v002-changelog.md` | Changelog v001→v002 |
| `evals/datasets/multimodal/multimodal-rag/README.md` | Схема, версионирование |
| `docs/sprints/sprint-10-multimodal-rag/metric_map.md` | Три группы метрик |
| `evals/configs/multimodal-baseline.yaml` | Конфиг baseline |
| `corpus/text_naive/slide-*.txt` | Naive corpus (66 файлов) |
| `evals/scripts/run_multimodal_baseline.py` | Corpus + index + eval |
| `evals/scripts/multimodal_models.py` | Pydantic-схема датасета |
| `evals/scripts/multimodal_metrics.py` | Retrieval-метрики по сегментам |
| `evals/tests/test_multimodal_dataset.py` | Smoke-тесты (6 passed) |
| `evals/reports/multimodal-baseline.md` | Baseline-отчёт |
| `evals/reports/runs/multimodal-baseline-20260705T154657Z.json` | Run JSON v002 |
| `docs/eval/README.md` | Точка входа eval |
| `docs/eval/metrics-map.md` | Секция multimodal-rag |
| `docs/eval/dataset-map.md` | Секция rag/multimodal-rag |
| `Makefile` | Цель `eval-multimodal-baseline` |
