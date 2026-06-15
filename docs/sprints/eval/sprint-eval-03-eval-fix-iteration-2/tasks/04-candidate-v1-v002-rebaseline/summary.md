# Summary: Task 04 — Candidate #1 re-baseline на v002

> **План:** [plan.md](./plan.md)
> **Дата закрытия:** 2026-06-15

---

## Что реализовано

- [`evals/configs/candidate-rag-first-prompt-e2e-qa-v002.yaml`](../../../../../../evals/configs/candidate-rag-first-prompt-e2e-qa-v002.yaml)
- Fix [`evals/scripts/run_utils.py`](../../../../../../evals/scripts/run_utils.py) — `load_dataset_context` учитывает pinned version → `e2e/e2e-qa/v002`
- Test [`evals/tests/test_run_config.py`](../../../../../../evals/tests/test_run_config.py) — smoke v002 pin
- Valid run: `candidate-rag-first-prompt-e2e-qa-v002--e2e-qa--476018c9--20260615T151141Z`
- [exp-005](../../../../../../evals/reports/exp-005-candidate-rag-first-prompt-v002.md) + [analyze](../../../../../../evals/reports/candidate-rag-first-prompt-e2e-qa-v002--e2e-qa--476018c9--20260615T151141Z.md) + experiments-log

---

## Отклонения от плана

- Failed run `…150903Z` (backend без нового `config_id`) — повтор после restart; зафиксирован в exp-005 как вспомогательный (E-26).
- Доп. fix `run_utils.py` — без него Langfuse dataset оставался на v001 при pin v002 в конфиге.

---

## Принятые решения

| Решение | Причина |
|---------|---------|
| ✅ v002 baseline @ **0.662** | Официальная точка отсчёта на sharpened criteria |
| v001 iter #1 (0.631) не трогаем | История exp-003; compare v001↔v002 запрещён (E-16) |
| Δ +0.031 qualitative only | 7 items с другими criteria — не agent-fix эффект |

---

## Проблемы и решения

| Проблема | Как решили |
|----------|-----------|
| 100% task_error на первом прогоне | Restart backend → `…151141Z` |
| `langfuse_dataset` резолвился в v001 | Fix `load_dataset_context` после `find_manifest_path` |

---

## Итог DoD

| # | Критерий | Результат |
|---|----------|-----------|
| 1 | Конфиг: тот же agent, только v002 pin | ✅ |
| 2 | 26 items v002, JSON + analyze | ✅ |
| 3 | exp-005 + v001/v002 таблица (qualitative) | ✅ |
| 4 | experiments-log | ✅ |
| 5 | ⛔ Апрув | ✅ |

---

## Что дальше

- **Task 05:** закрытие спринта eval-03
- eval-04: новые candidate compare только vs `…151141Z` на **v002**

---

## Ссылки

- [exp-003 v001 iter #1](../../../../../../evals/reports/exp-003-candidate-rag-first-prompt.md)
- [v002-changelog](../../../../../../evals/datasets/e2e/e2e-qa/v002-changelog.md)
