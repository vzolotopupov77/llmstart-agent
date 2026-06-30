# Task 08 — Fix Generation Loop + Regression Set (sub-plan)

> **Sprint:** [../../README.md](../../README.md) · **Parent plan:** [plan.md](plan.md)
> **Тип:** fix · **Ветка:** `feat/graphrag-08-agent-routing`
> **Контекст:** [graphrag-final.md](../../../../../evals/reports/graphrag-final.md) §Known gaps

---

## Цель

Закрыть остаточный single-hop gate (`answer_correctness ≥ 0.642`), не пройденный в основном прогоне Task 08
(retained 0.596, best 0.627). Для быстрой итерации ввести **regression set** по low-e2e items и отдельный
**fix generation loop**, разделив две независимые причины просадки.

---

## Диагноз (из 5 e2e-routing прогонов, per-item)

### A. Реальные провалы генерации (sales QA)

| item | тема | корень |
|------|------|--------|
| 0001 | формат комбо | общий список форматов; не назван состав комбо и consultation |
| 0003 | время/длительность | расписания курсов вместо «слоты TBD + записи будут» |
| 0005 | интенсив | не распознан vibe-coding-intensive, нет структуры (созвоны/практика/чат), нет code |
| 0008 | вечерний поток | «нет вечерних потоков» → запись вместо alt (вечер/выходные) |
| 0012 | CPO комбо | ответ не по существу, нет честной оговорки про код |
| 0022 | рассрочка | нет mock-оплаты MVP / планируемых провайдеров |
| 0023/0024 | sync/таймзона (multi) | не отвечает на последний user-turn |

### B. Артефакт измерения (НЕ генерация)

Судья `gemini-2.5-flash-lite` иногда отдаёт невалидный JSON → `evaluators.py` ловит исключение и ставит **0.0**.

- `0006` → 0.00 в retained, но **1.00 в 3/5 прогонов** (упал только из-за judge error).
- `0012` → 0.00 (`Judge error: invalid JSON`).

Эти нули «съедают» ~0.05 от среднего по 26 items.

---

## Состав работ

1. **Regression dataset** `evals/datasets/e2e/e2e-regression/v001_<date>.yaml` (~11 items):
   low-cluster (0001, 0003, 0005, 0008, 0012, 0022, 0023, 0024) + guard-green (0014, 0016, 0026).
   Новые id `e2e-reg-*` (Langfuse item id — project-global), `legacy_id` → исходный `e2e-qa-*`.
   `expected_output` копируются из v002 без правок. + `README.md` + `v001-changelog.md`.
2. **Judge-hardening** `evals/scripts/evaluators.py`: retry судьи на invalid-JSON (≤2),
   при стойком фейле — `None`/skip (не 0.0). Касается e2e- и graphrag-бандлов. + unit-тест.
3. **Eval wiring**: `evals/configs/graphrag-regression.yaml` (clone routing; prompt v4→v5),
   `e2e-regression: v001` в `datasets`; Makefile target `eval-graph-regression`.
4. **Baseline** regression-прогон на v4 (с hardening) — честный per-item зафиксировать.
5. **`agent-system-prompt-v5`** (поверх v4): post-tool answer rules под кластер
   (состав комбо; «TBD → ориентир + записи»; структура интенсива; mock-оплата/рассрочка MVP;
   alt-поток вечер/выходные вместо записи) + registry + `test_prompts.py`.
6. **Rerun** regression на v5 → per-item diff.
7. **Финал**: полный `e2e-qa v002` на v5 → подтвердить gate.
8. **Отчёты**: `evals/reports/graphrag-regression.md`; дополнить `graphrag-final.md` (decision log D10+).
9. **Sanitize**: ruff + `make test-backend`.

---

## DoD

| # | Критерий | Проверка |
|---|----------|----------|
| 1 | Regression set валиден и синкается в Langfuse | `make eval-graph-regression` без ошибок |
| 2 | Judge-hardening: invalid-JSON не даёт ложный 0.0 | unit-тест зелёный |
| 3 | На regression set целевой кластер вырос; guard-green не регрессировал | regression report |
| 4 | Финальный `e2e-qa v002` (v5): single-hop AC ≥ 0.642 **или** зафиксирован остаточный gap с разбором | eval run |
| 5 | `make test-backend` зелёный; отчёты обновлены | CI local + docs review |

---

## Scope

**In:** regression dataset, evaluator-hardening, prompt v5, eval config/target, отчёты.

**Out:** смена модели судьи, правка эталонов v002, изменение retriever-веток, закрытие спринта
(отдельным шагом после «ок» по DoD).
