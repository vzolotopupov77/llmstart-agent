# Plan: Задача 01 — Error analysis + таксономия провалов

> **Статус:** ✅ Done (⛔ ждёт апрува таксономии для Task 02)
> **Методология:** К-3 · [Error Analysis](https://langfuse.com/academy/monitoring/error-analysis)
> **Следующая задача:** Task 02 (items v002) · Task 03 (candidate v3 — plan уже апрувнут, реализация после 01–02)

---

## Цель

Первый **структурный** error analysis по `e2e/e2e-qa` v001: доменная таксономия провалов (не только heuristic retrieval/generation/behavior), failure rate по категориям, actionable «decide & act» для Task 02–03.

**Отличие от `analyze_run.py`:** per-run отчёт даёт слой провала и топ-5; здесь — **open coding → cluster → label & measure** по всем провальным items с опорой на traces, judge comments и metadata `intent` (G1–G9).

---

## Входные данные

| Артефакт | Run | Роль |
|----------|-----|------|
| Re-baseline | `baseline-react-chroma--e2e-qa--476018c9--20260615T083100Z` | до v2 prompt; retrieval-heavy провалы |
| Iter #1 candidate | `candidate-rag-first-prompt--e2e-qa--476018c9--20260615T094647Z` | текущий лучший конфиг (0.631) |
| Compare | [compare …083100Z vs …094647Z](../../../../../../evals/reports/compare--baseline-react-chroma--e2e-qa--476018c9--20260615T083100Z--vs--candidate-rag-first-prompt--e2e-qa--476018c9--20260615T094647Z.md) | fixed / regressed / stable |
| Манифест | `evals/datasets/e2e/e2e-qa/v001_2026-06-14.yaml` | `id`, `intent`, `answer_key_points`, `metadata` |
| Доменная таксономия (справка) | [analysis-report.md](../../../../../../datasets/extraction/analysis-report.md) G1–G9 | выравнивание категорий, не копировать слепо |

**Порог «провальный item» для разбора:** `answer_correctness` < **0.75** (north-star E-18) на **candidate run**; дополнительно все **регрессии** Δ≤−0.05 vs baseline и **improved** Δ≥+0.05 (чтобы понять, что v2 починил).

---

## Метод (5 шагов К-3)

### 1. Gather

- Загрузить оба JSON из `evals/reports/runs/`.
- Join по item index + `dataset_item_id` / input hash (если есть в JSON).
- Для каждого провального item candidate: `output.message`, tools, `retrieval_context`, scores, judge comments, Langfuse `session_id` / trace (через `trace_evidence` или UI).
- Выписать **missing key_points** (diff expected vs факт ответа — вручную по 1–2 предложения).

### 2. Open coding

Таблица (минимум 26 строк candidate, акцент на AC<0.75):

| index | item_id | intent | AC | layer (heuristic) | open note («что первым пошло не так») |
|-------|---------|--------|-----|-------------------|----------------------------------------|

Правило: notes **без** заранее заданных категорий; одна первичная причина на item.

### 3. Cluster

Сгруппировать open notes → **5–8 категорий** с коротким definition + пример item_id.

Ожидаемые кластеры (гипотеза до разбора — проверить, не навязывать):

| Код (черновик) | Definition |
|----------------|------------|
| `GEN-KP-MISS` | RAG/каталог есть, ответ не покрывает `answer_key_points` |
| `GEN-NO-DATA` | Отказ «нет данных» при непустом retrieval |
| `RET-SKIP` | Не вызван `search_knowledge_base` когда нужен |
| `RET-EMPTY` | RAG вызван, контекст пуст/нерелевантен |
| `BEH-FUNNEL` | Mock payment / confirm / lead — неверная траектория |
| `BEH-SEGMENT` | B2B/B2C routing, segment_match |
| `BEH-MULTI` | Multi-turn: игнор контекста, подмена продукта |
| `PROD-MAP` | Неверный продукт / intensive disambiguation |

Имена финализировать на шаге cluster; допустимо слияние/ split.

### 4. Label & measure

- Каждый item с AC<0.75 на candidate → **одна primary category**.
- Метрики: count и **failure rate** = count / 26; breakdown по `intent` (G1.x, G8.x…).
- Таблица **baseline vs candidate** по категориям (где v2 сдвинул массу).
- Отдельная секция **regressions #3, #21** — root cause.

### 5. Decide & act

| Приоритет | Категория | Действие | Куда |
|-----------|-----------|----------|------|
| P0 | … | prompt v3 / tool / dataset item | Task 03 / 02 / eval-04 |
| P1 | … | … | … |

- Валидировать или скорректировать гипотезу Task 03 (prompt v3).
- Список items-кандидатов в **v002** (Task 02) — id + что менять в criteria.

---

## Состав работ

- [ ] **1.1** Скрипт или notebook-шаблон `evals/scripts/build_error_analysis.py` (или расширение `failure_analysis.py`): экспорт CSV/markdown-таблицы open-coding из двух runs + merge compare deltas
- [ ] **1.2** Open coding всех items candidate (AC<0.75 + regressions + sample stable high)
- [ ] **1.3** Clustering → финальная таксономия с definitions
- [ ] **1.4** Label & measure + таблицы failure rate
- [ ] **1.5** Trace review топ-10 провалов (Langfuse spans) — подтвердить layer vs domain category
- [ ] **1.6** Отчёт `evals/reports/error-analysis-e2e-qa-v001-2026-06-15.md` — секции: метод, таксономия, таблицы, decide & act, связь с Task 03
- [ ] **1.7** (опц.) Unit-тест на merge/compare helper если добавлен код
- [ ] **1.8** Самопроверка DoD
- [ ] ⛔ Апрув пользователя на таксономию + top-3 actions → Task 02 plan

---

## DoD

| # | Критерий | Способ проверки |
|---|----------|-----------------|
| 1 | Отчёт `error-analysis-e2e-qa-v001-*.md` существует, все 5 шагов К-3 | файл + оглавление секций |
| 2 | 5–8 именованных категорий с definition + ≥1 example item_id каждая | секция «Таксономия» |
| 3 | Все items с AC<0.75 на candidate run промаркированы primary category | таблица label |
| 4 | Failure rate по категориям + срез baseline→candidate | таблица measure |
| 5 | Decide & act: top-3 с привязкой к Task 02/03 | секция «Рекомендации» |
| 6 | Task 03 hypothesis явно validated или скорректирована | параграф в отчёте |
| 7 | ⛔ Пользователь апрувит таксономию и приоритеты | гейт перед Task 02 |

---

## Артефакты

| Файл | Назначение |
|------|------------|
| `evals/reports/error-analysis-e2e-qa-v001-2026-06-15.md` | главный deliverable |
| `evals/scripts/build_error_analysis.py` | генерация таблицы из JSON (если проще без скрипта — таблица только в md, зафиксировать в summary) |
| `evals/tests/test_error_analysis.py` | smoke merge/delta (опц.) |

---

## Scope

**Трогаем:** `evals/scripts/`, `evals/reports/`, `evals/tests/` (если скрипт).

**НЕ трогаем:**
- `backend/` (agent, prompts) — Task 03 отложена
- `evals/datasets/e2e/e2e-qa/v001_*` — immutable
- v002 манифест — Task 02
- Новые eval-прогоны

---

## Риски и допущения

- **Heuristic layer ≠ domain category** — в отчёте держим обе оси; расхождения — сигнал для уточнения таксономии.
- **26 items** — статистика категорий ориентировочная (как в analysis-report); failure rate — для приоритизации, не для CI-gate.
- **Judge variance** — items 0.70–0.74 помечать `gt_quality`/«borderline»; не строить категорию «judge noise» без trace evidence.
- Скрипт **не обязателен**, если таблица 26 строк делается вручную; предпочтение — минимальный helper для merge двух JSON (DRY).

---

## Открытые вопросы (⛔ до старта)

- [ ] **Primary run для label:** candidate only для primary category, baseline — для «что v2 починил»? *(рекомендация plan: да)*
- [ ] **Скрипт vs ручной md:** достаточно helper merge + ручной open coding в md? *(рекомендация: helper + ручной cluster)*

---

## ⛔ Гейт

Старт реализации — после **«ок»** на этот plan. Task 02 не начинается до апрува таксономии из deliverable Task 01.
