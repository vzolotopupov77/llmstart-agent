# Plan: Задача 03 — Карта метрик

> **Спринт:** [../../README.md](../../README.md) · **Методология:** [.methodology/eval/eval-methodology.md](../../../../../../.methodology/eval/eval-methodology.md)
> **Статус:** 📋 Planned

## Цель

Утверждённая карта `docs/eval/metrics-map.md`: **чем** измеряем каждый датасет из [dataset-map.md](../../../../eval/dataset-map.md) — framework-first (E-17), главная + guard (E-18), пороги до прогона (E-20).

## Соответствие методологии

- **E-17** — порядок: детерминированная → RAGAS/DeepEval → G-Eval → ADR
- **E-18** — главная: `avg_answer_correctness` на `e2e/e2e-qa`; guard: faithfulness, task_completion, error_rate
- **E-19** — item-level + run-level; `task_error` обязателен
- **E-20** — пороги фиксируются в карте до baseline-прогона
- **E-21** — ToolCorrectness IN_ORDER по умолчанию

**Вход:** ✅ [dataset-map.md](../../../../eval/dataset-map.md) утверждена 2026-06-14

---

## Состав работ

- [ ] **3.1** Прочитать [metrics-guide.md](../../../../../../.methodology/eval/metrics-guide.md) §0, F
- [ ] **3.2** Черновик `docs/eval/metrics-map.md` по [шаблону](../../../../../../.methodology/templates/eval/metrics-map-template.md)
- [ ] **3.3** Главная + guard с обоснованием
- [ ] **3.4** 1–3 метрики на каждый из 7 датасетов — без кастомных судей (ADR не нужен)
- [ ] **3.5** Пороги 🟢/🔴 для каждой метрики
- [ ] **3.6** Самопроверка: каждая метрика привязана к датасету из dataset-map

---

## Предварительный выбор метрик (для согласования)

### Главная и guard (E-18)

| Роль | Метрика | Датасет | Фреймворк |
|------|---------|---------|-----------|
| **Главная** | `avg_answer_correctness` | `e2e/e2e-qa` | RAGAS Answer Correctness / DeepEval GEval по `answer_key_points` |
| Guard | `avg_faithfulness` | `e2e/e2e-qa` | RAGAS Faithfulness |
| Guard | `error_rate` | все | run-level (E-19) |
| Guard | `avg_task_completion` | `e2e/e2e-qa` | DeepEval TaskCompletionMetric (subset) |

### По датасетам

| Датасет | Метрики (E-17) | Порог (draft) |
|---------|----------------|---------------|
| **e2e/e2e-qa** | Answer Correctness (б) + Faithfulness (б) + segment exact (а) + task_error (а) | correctness ≥0.75 🟢 / <0.60 🔴 |
| **rag/rag-retrieval** | Answer Correctness (б) + Faithfulness span (б) | correctness ≥0.80 |
| **rag/b2b-rag** | Answer Correctness (б) + segment exact (а) | segment 100% |
| **behavior/segment-routing** | exact_match segment (а) | 100% 🟢 |
| **behavior/tool-trajectory** | ToolCorrectness IN_ORDER (б/C) + executed_tools_count (а) | ToolCorrectness ≥0.90 |
| **behavior/funnel-to-lead** | state_check leads (а) + TaskCompletion (б) | v0.2 — пороги TBD |
| **edge/edge-cases** | GEval must_not + Answer Correctness (в/E) | must_not pass 100%; correctness ≥0.70 |

**GEval для edge:** criteria «не обещал демо-URL, не настаивал на цели после отказа» — категория E, без ADR.

**Отложено:** Context Recall/Precision на `rag-retrieval` — нет chunk_ids в эталоне (dataset-map).

---

## Scope

**Входит:** только `docs/eval/metrics-map.md`

**Не входит:** evaluators.py, baseline-прогон, ADR (кастомных судей нет)

---

## DoD

| # | Критерий | Проверка |
|---|----------|----------|
| 1 | Главная + guard (E-18) | секция в карте |
| 2 | Метрика на каждый датасет из dataset-map | 7 блоков |
| 3 | Фреймворк, имя, ссылка, порог — у каждой | ревью |
| 4 | Кастомных судей без ADR — 0 | ревью |
| 5 | Пороги до прогона (E-20) | таблица порогов |
| 6 | ⛔ Утверждение пользователем | апрув |

---

## Артефакты

- `docs/eval/metrics-map.md`
