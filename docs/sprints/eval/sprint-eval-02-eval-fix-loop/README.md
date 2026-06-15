# Sprint eval-02: eval-fix-loop

> **Версия roadmap:** v0.2 (roadmap-eval)
> **Roadmap:** [../../../roadmap-eval.md](../../../roadmap-eval.md) · **Методология:** [.methodology/eval/eval-methodology.md](../../../../.methodology/eval/eval-methodology.md)
> **Статус:** ✅ Done
> **Открыт:** 2026-06-14 · **Закрыт:** 2026-06-15

---

## Цель спринта

Достоверные метрики + первый измеримый цикл улучшения: починить evaluators, пересчитать baseline, сравнить с candidate-конфигом (E-7, E-22).

**Вход:** baseline sprint-eval-01 — `baseline-react-chroma--e2e-qa--476018c9--20260614T182238Z` (answer_correctness 0.135, подозрение на баг GEval).

---

## DoD спринта

| # | Критерий | Способ проверки | ✅ |
|---|----------|-----------------|---|
| 1 | GEval/task_completion оценивают по `answer_key_points` текущего item, не «payment link» на FAQ | unit-тесты + sample items из baseline | ✅ Task 01 |
| 2 | Re-baseline `e2e-qa` v001 с исправленными evaluators | `make eval-experiment` + JSON | ✅ [exp-002](../../../../evals/reports/exp-002-rebaseline-fixed-judge.md) `…083100Z` |
| 3 | `make eval-compare RUN_A=… RUN_B=…` — markdown с дельтой метрик (E-16) | compare report | ✅ Task 03 |
| 4 | ≥ 1 candidate-конфиг (один параметр vs baseline) прогнан и сравнён | experiments-log | ✅ [exp-003](../../../../evals/reports/exp-003-candidate-rag-first-prompt.md) |
| 5 | Отчёт analyze для re-baseline; top-fixes для агента обновлены | `evals/reports/*.md` | ✅ analyze + compare reports |

---

## Задачи

| # | Задача | Статус | Plan | Summary |
|---|--------|--------|------|---------|
| 01 | Fix GEval + task_completion | ✅ | [plan](tasks/01-fix-evaluators/plan.md) | [summary](tasks/01-fix-evaluators/summary.md) |
| 02 | Re-baseline + analyze | ✅ | [plan](tasks/02-rebaseline/plan.md) | [summary](tasks/02-rebaseline/summary.md) |
| 03 | compare_runs | ✅ | [plan](tasks/03-compare-runs/plan.md) | [summary](tasks/03-compare-runs/summary.md) |
| 04 | Candidate RAG-first prompt | ✅ | [plan](tasks/04-candidate-config/plan.md) | [summary](tasks/04-candidate-config/summary.md) |
| 05 | Langfuse dataset_run_items + UI scores | ✅ | [plan](tasks/05-langfuse-dataset-run-items/plan.md) | [summary](tasks/05-langfuse-dataset-run-items/summary.md) |

> **Порядок:** 01 → 02 → 03 → 04 → 05. Agent-fix (04) только после достоверного re-baseline.

---

## Ограничения

- Датасет `e2e/e2e-qa/v001` — без изменения items (только evaluators/agent).
- Candidate меняет **один** параметр (E-7): prompt **или** retrieval **или** judge — не всё сразу.
- `dataset_run_items` в Langfuse UI — ✅ Task 05 (+ `make eval-backfill-runs`)

---

## Итог

**Реализовано:** достоверные evaluators, канонический re-baseline, `compare_runs`, первая итерация eval-fix (RAG-first prompt v2), Langfuse UI linking + backfill исторических прогонов.

### Метрики (e2e-qa v001, `avg_answer_correctness`)

| Этап | Run / эксперимент | Главная метрика |
|------|-------------------|-----------------|
| Sprint-01 (битый judge) | `…182238Z` | 0.135 ❌ superseded |
| Re-baseline (Task 02) | `…083100Z` · [exp-002](../../../../evals/reports/exp-002-rebaseline-fixed-judge.md) | **0.527** — канон baseline |
| Candidate v2 prompt (Task 04) | `…094647Z` · [exp-003](../../../../evals/reports/exp-003-candidate-rag-first-prompt.md) | **0.631** (+0.104 vs baseline) |

Порог E-18 (0.75) **не достигнут**. Candidate `candidate-rag-first-prompt` зафиксирован для траектории eval-fix, **не** production.

### Инфра (Task 05)

- Langfuse web/worker выровнены до **3.185.0** (без `down -v`)
- Preflight: `check_langfuse_versions`, `check_langfuse_contracts` в `make eval-validate`
- `make eval-backfill-runs` — восстановлены items/scores для всех JSON в `reports/runs/`

### Продолжение: eval-03 ✅ · eval-04 📋

**eval-03** ([sprint-eval-03](../sprint-eval-03-eval-fix-iteration-2/README.md)) — **выполнено 2026-06-15:**

- E-22 2/2: iter #2 (v3 prompt) отклонён; iter #1 `candidate-rag-first-prompt` @ **0.631** сохранён
- Error analysis (7 категорий), `e2e-qa` v002, v002 baseline **0.662** ([exp-005](../../../../evals/reports/exp-005-candidate-rag-first-prompt-v002.md))
- North-star 0.75 — не достигнут

**eval-04** ([sprint-eval-04](../sprint-eval-04-datasets-coverage/README.md)) — **следующий:**

- Component-датасеты по [dataset-map.md](../../../eval/dataset-map.md)
- `funnel-to-lead` + user simulation (E-23)
- Compare baseline для e2e: **v002** `…151141Z` (0.662)
- P0 handoff: tool-fix, generation, retrieval items из таксономии eval-03
