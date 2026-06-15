# Plan: Задача 02 — Карта датасетов

> **Спринт:** [../../README.md](../../README.md) · **Методология:** [.methodology/eval/eval-methodology.md](../../../../../../.methodology/eval/eval-methodology.md)
> **Статус:** 📋 Planned

## Цель

Утверждённая карта `docs/eval/dataset-map.md`: **что** измеряем — датасеты по слоям E-11, выведенные из vision, реальных диалогов и отчёта G1–G9. Метрики **не** выбираются (задача 03).

## Соответствие методологии

- **E-11** — группы `e2e` / `rag` / `behavior` / `edge`
- **E-13/E-14** — в карте зафиксировать источник эталонов и ожидаемую долю verified vs approximate
- **К-3/К-4** — таксономия провалов из analysis-report → датасеты; один датасет — одна зона ответственности

**Противоречий:** нет. Черновые `datasets/b2c/v2/` и `datasets/b2b/v2/` — **материал**, не eval-манифест; маппинг в карту, не копирование JSONL.

---

## Входы (прочитать перед написанием карты)

| Источник | Путь | Что взять |
|----------|------|-----------|
| Vision, сценарии С-* | `docs/concept/vision.md` §3 | С-1…С-7 → матрица покрытия |
| Отчёт анализа | `datasets/extraction/analysis-report.md` | G1–G9, приоритеты, пробелы |
| Dataset plan (frozen) | `datasets/dataset-plan.md` | типы b2c-rag/product/segment/objection/tools, B2B ветка |
| Черновые датасеты | `datasets/b2c/v2/dataset.jsonl` (72), `datasets/b2b/v2/` (15) | объёмы, turn_mode, группы |
| Диалоги | `datasets/dialogs/` (5 чатов) | real_dialog источник |
| КБ | `data/b2c/`, `data/b2b/` | synthetic + verified эталоны |

---

## Состав работ

- [ ] **2.1** Матрица покрытия: сценарии vision (С-1…С-7, релевантные для eval) → датасеты
- [ ] **2.2** Черновик `docs/eval/dataset-map.md` по [шаблону](../../../../../../.methodology/templates/eval/dataset-map-template.md)
- [ ] **2.3** Для каждого датасета — все поля шаблона + «Обоснование» + «Чего сознательно НЕ покрываем»
- [ ] **2.4** Порядок реализации: vertical slice = `e2e/e2e-qa` (eval-01); остальное → eval-02
- [ ] **2.5** Самопроверка: каждый С-* покрыт; метрик в карте нет

---

## Предварительная структура датасетов (для согласования в карте)

| Датасет | Группа | Зона ответственности | Источник items (ориентир) | MVP размер |
|---------|--------|----------------------|---------------------------|------------|
| **e2e/e2e-qa** | e2e | С-1: сквозной Q&A — RAG + продукт + тон; репрезентативная выборка G1–G5 | real_dialog 4 чата + synthetic по KB | **≥20** (vertical slice) |
| **rag/rag-retrieval** | rag | G1 FAQ, факты из KB; retrieval layer | b2c-rag items из v2 | 15–25 |
| **behavior/segment-routing** | behavior | G7, С-5/С-7: B2B vs B2C, audience filter | b2c-segment + b2b-segment | 10–15 |
| **behavior/tool-trajectory** | behavior | G8–G9, С-2/С-3: tools IN_ORDER | b2c-tools + синтетика | 10–15 |
| **behavior/funnel-to-lead** | behavior | С-2→С-3: payment → confirm → lead (multi-turn, E-23) | synthetic + scenarios.yaml | 8–12 (eval-02 / v0.2) |
| **edge/edge-cases** | edge | G3–G4: возражения, демо, senior-skeptic, timezone | b2c-objection + синтетика G4 | 15–20 |
| **rag/b2b-rag** | rag | С-6: корп. обучение, бриф, не B2C checkout | b2b-rag из v2 + CHAT_0127 | 10–15 |

**Не дублировать** legacy JSONL как eval-манifest — items переносятся в `evals/datasets/<group>/<name>/v001_*.yaml` на задаче 04+ с `reviewed_by`.

---

## Scope

**Входит:** только `docs/eval/dataset-map.md`

**Не входит:** metrics-map, манифесты, sync, метрики, пороги

---

## DoD (из README спринта)

| # | Критерий | Способ проверки |
|---|----------|-----------------|
| 1 | Все секции шаблона заполнены | ревью файла |
| 2 | Обоснование у каждого датасета | ревью |
| 3 | «Чего сознательно НЕ покрываем» | ревью |
| 4 | Метрики не выбраны | отсутствие metrics-map полей |
| 5 | Каждый сценарий vision (С-1…С-7) покрыт | матрица покрытия |
| 6 | ⛔ Пользователь утвердил карту | апрув в чате |

---

## Самопроверка

- [ ] DoD построчно
- [ ] Правило агента №8: карта только в этой задаче после апрува плана

---

## Артефакты

- `docs/eval/dataset-map.md`
