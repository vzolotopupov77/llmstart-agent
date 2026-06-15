# Эксперимент: winning candidate re-baseline на e2e-qa v002

> **Дата:** 2026-06-15 · **Автор:** eval-agent · **Статус:** ✅ завершён
> **Журнал:** [`experiments-log.md`](experiments-log.md) (E-26)
> **Задача/спринт:** [sprint-eval-03 Task 04](../../../docs/sprints/eval/sprint-eval-03-eval-fix-iteration-2/tasks/04-candidate-v1-v002-rebaseline/plan.md)

---

## Гипотеза / вопрос

Тот же winning candidate (`candidate-rag-first-prompt`, v2 prompt) на **v002** (7 items с sharpened criteria) даст другой `avg_answer_correctness` vs 0.631 на v001. Нужен baseline на актуальной рубрике для eval-04.

## Конфигурация

| Параметр | Значение |
|---|---|
| Ран (valid) | `candidate-rag-first-prompt-e2e-qa-v002--e2e-qa--476018c9--20260615T151141Z` |
| config_id | `candidate-rag-first-prompt-e2e-qa-v002` |
| Промпт | `agent-system-prompt-v2` (идентичен iter #1) |
| Датасет | `e2e/e2e-qa` **v002** |
| git_sha | `476018c9` |

Ссылки: [analyze](candidate-rag-first-prompt-e2e-qa-v002--e2e-qa--476018c9--20260615T151141Z.md) · [JSON](runs/candidate-rag-first-prompt-e2e-qa-v002--e2e-qa--476018c9--20260615T151141Z.json)

**Неудачный прогон (вспомогательный):** `…150903Z` — 100% `task_error` (backend не подхватил новый `config_id`); повтор после restart → `…151141Z`.

---

## v001 vs v002 (run-level, qualitative — E-16)

> ⚠️ **Не compare:** разные версии датасета. Таблица — ориентир, не факторный анализ.

| Метрика | v001 iter #1 (`…094647Z`) | v002 rebaseline (`…151141Z`) | Δ (v002−v001) |
|---|---:|---:|---:|
| avg_answer_correctness | 0.631 | **0.662** | +0.031 |
| avg_faithfulness | 0.840 | 0.830 | −0.010 |
| avg_task_completion | 0.612 | 0.608 | −0.004 |
| error_rate | 0.000 | 0.000 | — |
| segment_match_rate | 0.846 | 0.846 | — |

**Интерпретация:** главная метрика **выше** на v002 (+0.031), guard стабильны. Часть Δ — эффект уточнённых criteria на 7 items ([v002-changelog](../../datasets/e2e/e2e-qa/v002-changelog.md), не изменение агента). Agent output тот же конфиг — сравнение v001↔v002 **не изолирует** agent-fix.

---

## Результаты v002 (valid run)

| Метрика | Роль | Порог | Value | Статус |
|---|---|---|---|:---:|
| avg_answer_correctness | **главная** | ≥ 0.75 | **0.662** | 🟡 |
| avg_faithfulness | guard | ≥ 0.85 | 0.830 | 🟡 |
| avg_task_completion | guard | ≥ 0.80 | 0.608 | 🔴 |
| error_rate | infra | ≤ 0.05 | 0.000 | 🟢 |

Таксономия: retrieval 5 · generation 11 · behavior 4 · unknown 6.

---

## Решение

**✅ Зафиксировать v002 baseline** `candidate-rag-first-prompt-e2e-qa-v002` @ **0.662**

- Официальная точка отсчёта для следующих экспериментов на **v002** (E-18 на актуальной рубрике).
- Winning agent config по-прежнему `candidate-rag-first-prompt` (v001 pin в exp-003 не трогаем).

## Следующие шаги

- [ ] Task 05: закрытие спринта eval-03
- [ ] eval-04: compare новых candidate только на **v002** vs `…151141Z`
- [ ] Tool-fix / retrieval для #9, #16, generation items из analyze
