# Summary: Task 03 — Карта метрик

> **План:** [plan.md](./plan.md)
> **Дата закрытия:** 2026-06-14

---

## Что реализовано

- [`docs/eval/metrics-map.md`](../../../../eval/metrics-map.md) — метрики для 7 датасетов из dataset-map
- Главная: `avg_answer_correctness` (GEval по key_points) на `e2e/e2e-qa`
- Guard: faithfulness, task_completion, error_rate
- Пороги baseline зафиксированы до первого прогона (E-20)
- ToolCorrectness IN_ORDER (E-21); Context Recall отложен

---

## Отклонения от плана

Нет отклонений.

---

## Принятые решения

| Решение | Причина |
|---------|---------|
| GEval вместо RAGAS Answer Correctness для key_points | Эталон — criteria list, не reference answer |
| Context Recall/Precision отложены | Нет chunk_ids в эталоне (dataset-map) |
| funnel-to-lead пороги зафиксированы заранее | E-20; прогон в v0.2 |
| Кастомных судей нет | E-17г — всё через RAGAS/DeepEval/GEval |

---

## Итог DoD

| # | Критерий | Результат |
|---|----------|-----------|
| 1 | Главная + guard (E-18) | ✅ |
| 2 | Метрики на 7 датасетов | ✅ |
| 3 | Фреймворк, порог, ссылка | ✅ |
| 4 | ADR = 0 | ✅ |
| 5 | Пороги до прогона (E-20) | ✅ |
| 6 | ⛔ Утверждение пользователем | ✅ 2026-06-14 |

---

## Что дальше

- **Задача 04:** манифест `e2e/e2e-qa` v001, review эталонов (⛔), sync Langfuse

---

## Ссылки

- [metrics-map.md](../../../../eval/metrics-map.md)
- [dataset-map.md](../../../../eval/dataset-map.md)
- [metrics-guide.md](../../../../../.methodology/eval/metrics-guide.md)
