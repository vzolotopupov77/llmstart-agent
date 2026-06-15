# Summary: Task 03 — Candidate #2 (prompt v3)

> **План:** [plan.md](./plan.md)
> **Дата закрытия:** 2026-06-15

---

## Что реализовано

- [`backend/app/agent/prompts.py`](../../../../../../backend/app/agent/prompts.py) — `SYSTEM_PROMPT_V3` + registry (`agent-system-prompt-v3`)
- [`backend/tests/test_prompts.py`](../../../../../../backend/tests/test_prompts.py), [`test_config_registry.py`](../../../../../../backend/tests/test_config_registry.py) — smoke v3 + config load
- [`evals/configs/candidate-generation-keypoints-v3.yaml`](../../../../../../evals/configs/candidate-generation-keypoints-v3.yaml)
- Run `candidate-generation-keypoints-v3--e2e-qa--476018c9--20260615T144346Z` (26 items, v001)
- [compare vs iter #1](../../../../../../evals/reports/compare--candidate-rag-first-prompt--e2e-qa--476018c9--20260615T094647Z--vs--candidate-generation-keypoints-v3--e2e-qa--476018c9--20260615T144346Z.md)
- [exp-004](../../../../../../evals/reports/exp-004-candidate-generation-keypoints-v3.md) + [experiments-log](../../../../../../evals/reports/experiments-log.md)

---

## Отклонения от плана

Нет. Гипотеза не подтвердилась по главной метрике — зафиксировано в exp-004 как **отклонение candidate**, не как отклонение от scope задачи.

---

## Принятые решения

| Решение | Причина |
|---------|---------|
| ❌ Отклонить v3 | `avg_answer_correctness` 0.615 vs 0.631 (−0.015); 11 регрессий |
| Winning config — `candidate-rag-first-prompt` | Единственный прирост главной метрики в eval-fix loop |
| E-22 закрыт 2/2 | Итерация #2 измерена и задокументирована, даже при отрицательной Δ |

---

## Проблемы и решения

| Проблема | Как решили |
|----------|-----------|
| v3 улучшил #3, #9, но сломал #10, #22, #24 | Отклонили; trade-off «больше KB-фактов» → eval-04 |
| Backend без reload не подхватывает prompt | Перезапуск `:8003` перед прогоном |

---

## Итог DoD

| # | Критерий | Результат |
|---|----------|-----------|
| 1 | E-7: только `prompt.name` | ✅ |
| 2 | Прогон 26 items v001 + analyze | ✅ |
| 3 | Compare vs `…094647Z` | ✅ |
| 4 | exp-004 + experiments-log; E-22 2/2 | ✅ |
| 5 | ⛔ Решение зафиксировано | ✅ |

---

## Что дальше

- **Task 04:** rebaseline `candidate-rag-first-prompt` на **v002**
- eval-04: tool-fix #9/#16, разбор регрессий v3 (#10, #22)

---

## Ссылки

- [exp-003 iter #1](../../../../../../evals/reports/exp-003-candidate-rag-first-prompt.md)
- [analyze v3](../../../../../../evals/reports/candidate-generation-keypoints-v3--e2e-qa--476018c9--20260615T144346Z.md)
- [Task 04 plan](../04-candidate-v1-v002-rebaseline/plan.md)
