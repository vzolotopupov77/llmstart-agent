# Summary: Task 03 — compare_runs

> **План:** [plan.md](./plan.md)
> **Дата:** 2026-06-15

---

## Что реализовано

- [`evals/scripts/compare_runs.py`](../../../../../../evals/scripts/compare_runs.py) — E-16 guard, run/item deltas, **факторный анализ**, markdown (RU)
- [`evals/tests/test_compare_runs.py`](../../../../../../evals/tests/test_compare_runs.py) — 7 тестов (35 total)
- `evals/Makefile` — `-m scripts.compare_runs`

**Demo compare:** [`evals/reports/compare--baseline-react-chroma--e2e-qa--476018c9--20260614T182238Z--vs--baseline-react-chroma--e2e-qa--476018c9--20260615T083100Z.md`](../../../../../../evals/reports/compare--baseline-react-chroma--e2e-qa--476018c9--20260614T182238Z--vs--baseline-react-chroma--e2e-qa--476018c9--20260615T083100Z.md)

---

## Ключевые дельты (broken judge → fixed re-baseline)

| Метрика | A (old) | B (new) | Δ |
|---------|--------:|--------:|--:|
| avg_answer_correctness | 0.135 | 0.527 | +0.392 |
| avg_faithfulness | 0.608 | 0.644 | +0.036 |
| avg_task_completion | 0.438 | 0.573 | +0.135 |

Compare помечает warning: same config/git/judge — дельта от evaluators, не agent.

---

## Итог DoD

| # | Критерий | Результат |
|---|----------|-----------|
| 1 | `make eval-compare` → `.md` | ✅ |
| 2 | E-16 guard | ✅ tested |
| 3 | Run-level + top improved/regressed | ✅ |
| 4 | ⛔ Пользователь просмотрел report | ✅ 2026-06-15 |

---

## Что дальше

- **Task 04:** candidate-конfig (один параметр) + compare vs `…20260615T083100Z`

**Команда:**
```bash
make eval-compare RUN_A=<baseline> RUN_B=<candidate>
```
