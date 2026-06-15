# Summary: Task 06 — Отчёт анализа baseline

> **План:** [plan.md](./plan.md)
> **Дата:** 2026-06-14

---

## Что реализовано

- [`evals/scripts/analyze_run.py`](../../../../../../evals/scripts/analyze_run.py) — JSON → markdown (сводка, пороги, распределение, топ-5, рекомендации)
- [`evals/scripts/failure_analysis.py`](../../../../../../evals/scripts/failure_analysis.py) — таксономия retrieval / generation / behavior
- [`evals/scripts/trace_evidence.py`](../../../../../../evals/scripts/trace_evidence.py) — span-evidence из Langfuse session
- [`evals/tests/test_analyze_run.py`](../../../../../../evals/tests/test_analyze_run.py) — unit-тесты классификации и загрузки
- Fix: `evals/Makefile` — `-m scripts.analyze_run` / `-m scripts.run_experiment` (import path)

**Отчёт:** [`evals/reports/baseline-react-chroma--e2e-qa--476018c9--20260614T182238Z.md`](../../../../../../evals/reports/baseline-react-chroma--e2e-qa--476018c9--20260614T182238Z.md)

---

## Ключевые выводы baseline

| Метрика | Value | Порог 🟢 |
|---------|------:|---------:|
| avg_answer_correctness | 0.135 | ≥0.75 |
| avg_faithfulness | 0.608 | ≥0.85 |
| avg_task_completion | 0.438 | ≥0.80 |
| error_rate | 0.0 | <0.05 |

**Таксономия (26 items):** retrieval 11 · generation 13 · behavior 1 · unknown 1

**⚠️ Сигнал качества eval-контура:** комментарии GEval у многих items ссылаются на «payment link / agents», хотя input — другой вопрос (напр. «рассрочка», «расписание семинаров»). Вероятная причина — criteria из `expected_output.key_points` не совпадают с фактическим turn или judge путает multi-turn context. **Перед eval-fix loop — перепроверить GEval criteria и task_completion.**

---

## Итог DoD

| # | Критерий | Результат |
|---|----------|-----------|
| 1 | `make eval-analyze RUN=…` → `.md` | ✅ |
| 2 | Разделы: сводка, пороги, распределение, топ-5, рекомендации | ✅ |
| 3 | Слой провала + trace/session ссылки + span evidence | ✅ |
| 4 | ⛔ Пользователь читает отчёт и согласует top-fixes | ✅ 2026-06-14 |

---

## Что дальше (после апрува)

1. **Eval-infra:** починить GEval criteria / multi-turn input для answer_correctness
2. **Eval-fix v0.2:** generation prompt + retrieval coverage
3. **sprint-eval-02:** dataset_run_items в Langfuse UI, compare_runs

---

## Ссылки

- [baseline JSON](../../../../../../evals/reports/runs/baseline-react-chroma--e2e-qa--476018c9--20260614T182238Z.json)
- [metrics-map.md](../../../../eval/metrics-map.md)
