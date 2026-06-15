# Summary: Task 05 — Runner + evaluators + baseline

> **План:** [plan.md](./plan.md)
> **Дата закрытия:** 2026-06-14

---

## Что реализовано

- [`evals/scripts/run_experiment.py`](../../../../../../evals/scripts/run_experiment.py) — Langfuse `dataset.run_experiment`, preflight, JSON report
- [`evals/scripts/evaluators.py`](../../../../../../evals/scripts/evaluators.py) — item/run metrics по metrics-map (e2e-qa)
- [`evals/scripts/agent_task.py`](../../../../../../evals/scripts/agent_task.py) — HTTP Agent Core, single/multi-turn
- [`evals/scripts/judge_client.py`](../../../../../../evals/scripts/judge_client.py) — DeepEval OpenRouter judge
- [`evals/scripts/trace_context.py`](../../../../../../evals/scripts/trace_context.py) — retrieval context из Langfuse trace
- [`evals/scripts/run_report.py`](../../../../../../evals/scripts/run_report.py) — локальный JSON schema v2 (E-27)
- [`evals/scripts/run_utils.py`](../../../../../../evals/scripts/run_utils.py) — run name E-9, dataset resolve
- Зависимости: `httpx`, `deepeval` в [`evals/pyproject.toml`](../../../../../../evals/pyproject.toml)
- Тесты: [`evals/tests/test_evaluators.py`](../../../../../../evals/tests/test_evaluators.py) — 17 passed total

**Baseline-прогон:** `baseline-react-chroma--e2e-qa--476018c9--20260614T182238Z` (26 items)

| Run-level | Score |
|-----------|-------|
| avg_answer_correctness | 0.135 |
| avg_faithfulness | 0.608 |
| avg_task_completion | 0.438 |
| error_rate | 0.0 |
| segment_match_rate | 0.654 |

**Evidence:** [`evals/reports/runs/baseline-react-chroma--e2e-qa--476018c9--20260614T182238Z.json`](../../../../../../evals/reports/runs/baseline-react-chroma--e2e-qa--476018c9--20260614T182238Z.json)

**Langfuse Dataset Run ID:** `8982b43c-3923-4fa1-9fb7-d66b53e271f4` (26 items) — UI: Datasets → `e2e/e2e-qa/v001` → Runs

---

## Отклонения от плана

| План | Факт | Причина |
|------|------|---------|
| RAGAS Faithfulness | DeepEval `FaithfulnessMetric` | `ragas` не ставится на Windows без MSVC (scikit-network build) |
| `dataset_run_url` в JSON | часто `null` | SDK v3; ID run есть, URL — через UI |

---

## Принятые решения

| Решение | Причина |
|---------|---------|
| DeepEval OpenRouterModel + `OPENAI_API_KEY` | Совместимость с `.env` проекта |
| Multi-turn: replay только user turns | API не replay'ит assistant prefix |
| Slim Langfuse metadata (E-30) | Полный config — только в local JSON |
| segment heuristic из B2C tools | trace без `audience` на payment tools |
| Judge errors → score 0 + comment | E-19: не ронять прогон |

---

## Итог DoD

| # | Критерий | Результат |
|---|----------|-----------|
| 1 | `make eval-experiment` exit 0 | ✅ full run 26 items |
| 2 | Langfuse Dataset Run + scores | ✅ |
| 3 | `run_metadata` в JSON | ✅ full snapshot |
| 4 | task_error / error_rate | ✅ 0% errors |
| 5 | Judge reasoning в comment | ✅ GEval/Faithfulness comments |
| 6 | Local JSON v2 | ✅ |
| 7 | pytest green | ✅ 17 passed |
| 8 | ⛔ Пользователь проверил ран | ✅ (2026-06-14, «Ок» + переход к task 06) |

---

## Что дальше

- **Задача 06:** `analyze_run.py` + отчёт по baseline
- **Eval-fix (v0.2):** baseline 0.135 << порог 0.75 — ожидаемо для первого прогона

---

## Ссылки

- [metrics-map.md](../../../../eval/metrics-map.md)
- [experiments-log.md](../../../../../../evals/reports/experiments-log.md)
