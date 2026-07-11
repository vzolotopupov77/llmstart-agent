# Summary: Task 03 — indexer-contract-configs

> **План:** [plan.md](./plan.md)
> **Дата закрытия:** 2026-07-05

---

## Что реализовано

- Контракт `Indexer.build_index(corpus_dir) -> IndexCost` и `validate_corpus_dir()` (только `.pdf`/`.png`)
- `INDEXER_REGISTRY` + `make_indexer(cfg)` — baseline + stub A/B/C/D
- `BaselineIndexer`: PDF text layer (не OCR) → `evals/artifacts/corpus/text_naive/` → e5 → Qdrant
- Общий downstream: `multimodal_retrieval.py`, runner `run_multimodal_eval.py`
- 5 YAML-конфигов; env `OCR_ENGINE`, `CAPTION_MODEL`, `D_MAX_SIDE` в `.env.example`
- `tests/test_indexer_registry.py` (8 тестов); baseline re-run + секция ingestion failure

---

## Принятые решения

| Решение | Причина |
|---------|---------|
| `evals/artifacts/corpus/text_naive/` вместо `corpus/text_naive/` | Единое дерево с `evals/artifacts/ocr/`, `captions/` |
| `indexer.corpus_dir` = вход (`data/multimodal-rag`), `artifact_dir` = выход | Pre-flight не пускает `.txt` в входной корпус |
| Stub A–D с `NotImplementedError` | Task 03 — контракт; реализация в Task 04–07 |
| Collection `multimodal_text_naive_v002` без переименования | Меньше diff с Task 02 |
| `mcp_server/` не тронут | Prod RAG отдельно от eval-контура |

---

## Отклонения от плана

- Модуль `config.py` добавлен (разрыв circular import factory ↔ baseline)
- `registry.py` + `factory.py` + `baseline.py` + `stubs.py` вместо трёх файлов из README
- Метрики baseline между прогонами варьируют (шум пустого индекса) — ingestion-failure по **0 PDF chars** стабилен

---

## Итог DoD

| # | Критерий | Результат |
|---|----------|-----------|
| 1 | Контракт `Indexer` + `IndexCost` | ✅ `evals/indexers/base.py` |
| 2 | `make_indexer` для 5 конфигов | ✅ pytest |
| 3 | `validate_corpus_dir` reject `.txt` | ✅ |
| 4 | Baseline через новый runner | ✅ `make eval-multimodal-baseline` |
| 5 | 3 chart-failure примеров в отчёте | ✅ slides 10/11/9 |
| 6 | `mcp_server/` не менялся | ✅ |
| 7 | evals tests + ruff | ✅ 75 passed |
| — | User: контракт понятен | ✅ 2026-07-05 |

---

## Ссылки

- [multimodal-baseline.md](../../../../../evals/reports/multimodal-baseline.md)
- Следующая задача: [Task 04 — method-a-ocr](../../README.md#task-04-method-a-ocr)

---

## Артефакты

| Путь | Описание |
|------|----------|
| `evals/indexers/` | base, config, factory, registry, baseline, stubs |
| `evals/scripts/multimodal_retrieval.py` | Общий search + eval |
| `evals/scripts/run_multimodal_eval.py` | Generic runner |
| `evals/scripts/run_multimodal_baseline.py` | Thin wrapper |
| `evals/configs/multimodal-*.yaml` | 5 конфигов (baseline + A–D) |
| `evals/tests/test_indexer_registry.py` | Тесты реестра |
| `evals/artifacts/corpus/text_naive/slide-*.txt` | Baseline corpus (66, PDF layer пуст) |
| `evals/reports/multimodal-baseline.md` | Re-run Task 03 |
| `evals/reports/runs/multimodal-baseline-20260705T161917Z.json` | Run JSON |
| `.env.example` | OCR/CAPTION/D env |
| `Makefile` | `eval-multimodal-baseline`, `eval-multimodal` |
| `docs/eval.md` | Обновлённая точка входа |
