# Summary: Task 01 — Fix GEval + task_completion

> **План:** [plan.md](./plan.md)
> **Дата закрытия:** 2026-06-14

---

## Что реализовано

- [`evals/scripts/evaluators.py`](../../../../../../evals/scripts/evaluators.py) — per-item `GEval` + `TaskCompletionMetric`; `evaluation_steps` / explicit `task` из `expected_output`
- [`evals/scripts/agent_task.py`](../../../../../../evals/scripts/agent_task.py) — `format_judge_input()` (акцент на последний user turn)
- [`evals/scripts/smoke_evaluators.py`](../../../../../../evals/scripts/smoke_evaluators.py) — smoke 3 кейса
- [`evals/tests/test_evaluators.py`](../../../../../../evals/tests/test_evaluators.py) — +7 тестов (28 total)

**Helpers (testable):** `build_evaluation_steps`, `build_geval_criteria`, `build_task_description`, `create_answer_correctness_metric`, `create_task_completion_metric`

---

## Результат smoke (2026-06-14)

| Case | Score | Comment |
|------|------:|---------|
| installment | 1.0 | рассрочка / не обещать — без payment link |
| september | 1.0 | временной барьер / нет даты в KB |
| payment | 1.0 | payment link для agents |

⛔ Пользователь подтвердил релевантность comments — 2026-06-14.

---

## Итог DoD

| # | Критерий | Результат |
|---|----------|-----------|
| 1 | pytest green | ✅ 28 passed |
| 2 | Smoke 3 items — comments по key_points | ✅ |
| 3 | Нет shared mutable GEval | ✅ |
| 4 | ⛔ Пользователь проверил comments | ✅ |

---

## Что дальше

- **Task 02:** re-baseline `e2e-qa` v001 на исправленных evaluators + analyze report
- Сравнить метрики с `baseline-react-chroma--e2e-qa--476018c9--20260614T182238Z` (0.135 — подозрительно низкий)
