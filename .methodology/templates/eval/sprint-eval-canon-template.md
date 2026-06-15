# Sprint eval-01: vertical-slice

> **Версия roadmap:** v0.1 (roadmap-eval)
> **Roadmap:** [../../roadmap-eval.md](../../roadmap-eval.md) · **Методология:** [.methodology/eval/eval-methodology.md](../../../../.methodology/eval/eval-methodology.md)
> **Статус:** 📋 Planned
> **Открыт:** YYYY-MM-DD · **Закрыт:** —

---

## Цель спринта

Команда впервые получает измеренное качество агента — baseline-оценку ответов на реальные вопросы клиентов, воспроизводимую одной командой.

---

## DoD спринта

| # | Критерий | Способ проверки |
|---|----------|-----------------|
| 1 | Цели validate / sync / experiment / analyze отрабатывают на `e2e-qa` | последовательный запуск команд |
| 2 | В Langfuse — датасет `e2e/e2e-qa/vNNN` с ≥ 20 items, у всех `reviewed_by` | вывод items через Langfuse CLI/UI |
| 3 | Существует ран `baseline-*--e2e-qa--{sha}--{ts}` с полным конфигом в `run_metadata` (E-9) | metadata рана в UI/CLI |
| 4 | Item- и run-level scores записаны, включая `task_error`/`error_rate` (E-19); reasoning судьи в comment | scores на items рана |
| 5 | Отчёт анализа в `evals/reports/`: сводка, распределение, топ-5 худших со слоем провала | файл и его разделы |
| 6 | Негативный тест: item без `reviewed_by` падает на валидации (E-13) | подложный item → validate |
| 7 | Повторный sync идемпотентен: 0 новых items | повторный запуск sync |
| 8 | Drill-down: спаны агента вложены в trace item | открыть item рана в UI |

---

## Задачи

| # | Задача | Статус | Plan | Summary |
|---|--------|--------|------|---------|
| 01 | Реестр конфигов + каркас | 📋 | [plan](tasks/01-registry-skeleton/plan.md) | — |
| 02 | Карта датасетов | 📋 | [plan](tasks/02-dataset-map/plan.md) | — |
| 03 | Карта метрик | 📋 | [plan](tasks/03-metrics-map/plan.md) | — |
| 04 | Манифест e2e-qa + review + sync | 📋 | [plan](tasks/04-dataset-e2e-qa/plan.md) | — |
| 05 | Runner + evaluators + baseline | 📋 | [plan](tasks/05-runner-baseline/plan.md) | — |
| 06 | Отчёт анализа | 📋 | [plan](tasks/06-analyze/plan.md) | — |

> ⚠️ Задачи 02 и 03 — строго последовательные: метрики проектируются под **утверждённый** dataset-map, не параллельно с ним. Создание dataset-map/metrics-map вне этих задач (например, при генерации roadmap) — нарушение правила агента №8.

---

## Задача 01: Реестр конфигов + каркас 📋

### Цель
Конфигурация запуска реально управляет агентом, операции контура воспроизводимы одной командой.

> 💡 **Скиллы:** langfuse (CLI/датасеты/прогоны).

### Состав работ
- [ ] Agent Core принимает `config_id` (параметр запроса или фабрика) и применяет конфигурацию (E-6)
- [ ] Структура `evals/` по «Структуре файлов» методологии; команды validate/sync/experiment/analyze/compare (E-2, [Makefile-template](../../../../.methodology/templates/eval/Makefile-template))
- [ ] Скелеты скриптов (`models.py`, `sync_datasets.py`, `run_experiment.py`, `analyze_run.py`, `compare_runs.py` — скелет)
- [ ] Baseline-конфиг по [run-config-template.yaml](../../../../.methodology/templates/eval/run-config-template.yaml)
- [ ] Самопроверка по DoD

### DoD
**Агент:** запрос с разными `config_id` даёт разное поведение (например, другую модель в трейсе) — проверка по трейсам; все make-цели запускаются без ошибок (заглушечно).
**Пользователь (⛔ гейт):** прочитать baseline-конфиг и подтвердить, что он полностью описывает текущую систему (E-5) и исполняем (E-6).

### Артефакты
`evals/Makefile`, `evals/configs/baseline-*.yaml`, `evals/scripts/*`, правка Agent Core (реестр).

---

## Задача 02: Карта датасетов 📋

### Цель
Утверждённая карта: ЧТО мы измеряем — датасеты по слоям, выведенные из проектной документации и реальных данных.

> 💡 **Скиллы:** langfuse (методология); концепции К-3/К-4 методологии.

### Состав работ
- [ ] Изучить входы: концепт-доку (idea/vision — сценарии С-*/П-*), реальные диалоги, отчёт анализа диалогов
- [ ] `docs/eval/dataset-map.md` по [шаблону](../../../../.methodology/templates/eval/dataset-map-template.md): датасеты по группам e2e/rag/behavior/edge (E-11), для каждого — обоснование (какой сценарий/категория провалов закрывается), источники items, схема, размер по К-4 (10–30)
- [ ] Проверка покрытия: каждый пользовательский сценарий из vision покрыт хотя бы одним датасетом
- [ ] Самопроверка по DoD

### DoD
**Агент:** у каждого датасета заполнены все секции шаблона, включая «Обоснование» и «Чего сознательно НЕ покрываем»; метрики в карте НЕ выбираются (это задача 03).
**Пользователь (⛔ гейт):** утвердить карту датасетов. Без апрува задача 03 не начинается.

### Артефакты
`docs/eval/dataset-map.md`.

---

## Задача 03: Карта метрик 📋

### Цель
Утверждённая карта: ЧЕМ мы измеряем — метрики с порогами под утверждённые датасеты.

> 💡 **Скиллы:** langfuse; справочник metrics-guide.md (E-17).

### Состав работ
- [ ] Вход — **утверждённый** dataset-map (задача 02) и metrics-guide
- [ ] `docs/eval/metrics-map.md` по [шаблону](../../../../.methodology/templates/eval/metrics-map-template.md): 1–3 метрики на датасет строго по framework-first (E-17), главная и guard-метрики (E-18), пороги (E-20), режим ToolCorrectness (E-21)
- [ ] Кастомный судья (если потребуется) — сначала [ADR](../../../../.methodology/templates/eval/adr-custom-metric-template.md), ⛔ СТОП на апрув
- [ ] Самопроверка по DoD

### DoD
**Агент:** у каждой метрики — фреймворк, точное имя, ссылка на доку, тип score, порог, обоснование выбора; кастомных судей без ADR — ноль; каждая метрика привязана к датасету из утверждённого dataset-map.
**Пользователь (⛔ гейт):** утвердить карту метрик.

### Артефакты
`docs/eval/metrics-map.md`, (опц.) `docs/decisions/ADR-*`.

---

## Задача 04: Манифест e2e-qa + review + sync 📋

### Цель
Первый датасет с утверждёнными человеком эталонами синхронизирован в Langfuse.

### Состав работ
- [ ] `evals/datasets/e2e/e2e-qa/v001_YYYY-MM-DD.yaml` по [шаблону манифеста](../../../../.methodology/templates/eval/dataset-manifest-template.yaml): ≥ 20 items (real_dialog из диалогов + synthetic по КБ), `gt_quality` по E-14
- [ ] `README.md` датасета по [шаблону](../../../../.methodology/templates/eval/dataset-readme-template.md)
- [ ] Pydantic-модели + integrity-тесты по [шаблону](../../../../.methodology/templates/eval/test-dataset-integrity-template.py) (E-15)
- [ ] ⛔ Эталоны показаны пользователю и утверждены ДО простановки `reviewed_by` (E-13)
- [ ] Sync (зеркалирование версии по E-16); повторный запуск — идемпотентен
- [ ] Негативный тест валидатора `reviewed_by`
- [ ] Самопроверка по DoD

### DoD
**Агент:** integrity-тесты зелёные; повторный sync = 0 новых items; подложный item без `reviewed_by` валит validate.
**Пользователь:** выборочно проверить 5 items в Langfuse UI.

### Артефакты
`evals/datasets/e2e/e2e-qa/{v001_*.yaml,README.md}`, `evals/scripts/models.py`, `evals/tests/test_dataset_integrity.py`.

---

## Задача 05: Runner + evaluators + baseline 📋

### Цель
Baseline-прогон реального агента по датасету с метриками — воспроизводимый одной командой.

### Состав работ
- [ ] `run_experiment.py`: task → Agent Core с `config_id` (E-3/E-6); имя рана и `run_metadata` по E-9
- [ ] Item- и run-evaluators по metrics-map, включая `task_error`/`error_rate` (E-19), по [шаблону evaluators](../../../../.methodology/templates/eval/evaluators-template.py)
- [ ] Run-level ключи — только в `run_metadata` (E-25); версия `langfuse` запинена в lockfile
- [ ] Прогон baseline; evidence (скрин Dataset Run + drill-down) в summary
- [ ] Самопроверка по DoD

### DoD
**Агент:** ран виден в Langfuse, scores на items, по `run_metadata` восстановима конфигурация.
**Пользователь:** открыть ран и убедиться, что по metadata понятно, ЧТО именно прогонялось.

### Артефакты
`evals/scripts/run_experiment.py`, `evals/scripts/evaluators.py`, lockfile, evidence в `summary.md`.

---

## Задача 06: Отчёт анализа 📋

### Цель
Из рана — actionable отчёт: где система проваливается и что чинить первым.

### Состав работ
- [ ] `analyze_run.py`: сводка метрик, распределение, топ-5 худших items со слоем провала (retrieval / generation / behavior) по трейсу
- [ ] Отчёт в `evals/reports/`; разговорный разбор худших items через Langfuse skill/CLI
- [ ] Самопроверка по DoD

### DoD
**Агент:** отчёт содержит все разделы; слой провала у каждого из топ-5 обоснован ссылкой на спан трейса.
**Пользователь:** прочитать отчёт; согласовать top-исправления (вход в eval-fix loop, v0.2).

### Артефакты
`evals/scripts/analyze_run.py`, `evals/reports/<run>.md`.

---

## Ограничения спринта

- Только `e2e-qa` — остальные датасеты в sprint-eval-02 (вертикальный срез важнее покрытия).
- `compare_runs.py` — скелет; наполнение в v0.2.
- Кастомные судьи без ADR запрещены (E-17); пороги после утверждения metrics-map не двигать (E-20).

---

## Итог (заполняется после закрытия)

[Что реализовано. Отклонения. Что взято в sprint-eval-02.]
