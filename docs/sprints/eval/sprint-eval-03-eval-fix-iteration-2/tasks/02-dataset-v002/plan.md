# Plan: Задача 02 — `e2e-qa` v002 (criteria из таксономии)

> **Статус:** ✅ Done
> **Вход:** [error analysis](../../../../../../evals/reports/error-analysis-e2e-qa-v001-2026-06-15.md) §5 · [Task 01 summary](../01-error-analysis/summary.md)

---

## Цель

Иммутабельный **`v002_2026-06-15.yaml`**: уточнённые `expected_output` для items, выявленных error analysis (К-4), без изменения `input` и без новых item id. Sync в Langfuse `e2e/e2e-qa/v002`.

**Не цель Task 02:** прогон candidate v3 (Task 03–04) — v002 готовит judge/criteria; compare iter #2 остаётся на **v001** (E-7: один параметр = prompt).

---

## Scope v002

| Режим | Items | Обоснование |
|-------|------:|-------------|
| **Изменить criteria** | 7 | 4× P1 из error analysis + 2× G4.x borderline + 1× G1.3 schedule |
| **Без изменений (copy as-is)** | 19 | stable / вне таксономии P1 |
| **Новые item id** | 0 | YAGNI; остаток таксономии → eval-04 |

---

## Изменения по item (черновик criteria)

### P1 — error analysis (обязательные)

**`e2e-qa-0005`** (PROD-MAP + GEN-NO-DATA, регрессия Δ−0.40)

- `answer_key_points` += «даже при TBD расписании — назвать структуру: семинары, практика, чат»
- `must_not` += «отказ „нет данных о расписании“ без структуры intensive»
- `product_codes`: явно `vibe-coding-intensive` в key_points (не только «интенсив»)

**`e2e-qa-0023`** (BEH-MULTI, регрессия Δ−0.20)

- `must_not` += «предлагать другой продукт / intensive без ответа на sync-objection»
- `answer_key_points` += «не игнорировать последний user turn про вечерние созвоны»
- `metadata.gt_quality`: остаётся approximate → **verified** только если пользователь подтвердит формулировки

**`e2e-qa-0017`** (BEH-FUNNEL, AC=0)

- `tools`: явно `confirm_payment` (IN_ORDER в metrics-map уже default)
- `must_not` += «только запрос контактов без попытки confirm_payment»
- `answer_key_points` += «поблагодарить за оплату и перейти к save_lead при mock-подтверждении»
- `gt_quality`: **verified** (уже; criteria уточняются)

**`e2e-qa-0024`** (GEN-NO-DATA, timezone)

- `answer_key_points`: разнести «время в MSK» и «комментарий для SF / travel» (уже есть — усилить формулировки)
- `must_not` += «„расписание неизвестно“ без ориентиров из KB (выходной слот, MSK)»
- опц. `metadata`: `kb_verified: true` если привязка к faq

### P1 — G1.3 schedule (partner к 0024)

**`e2e-qa-0003`** (GEN-NO-DATA, AC=0)

- `answer_key_points` += явный маркер «ориентир вечер/выходные допустим при TBD»
- `must_not` += «полный отказ без упоминания длительности (~2 ч) и записей»

### P1 — BEH-OBJECTION (borderline AC=0.7)

**`e2e-qa-0011`** (G4.5, AC=0.2)

- `must_not` += «повторный вопрос про цель/опыт после явного отказа user»
- (key_points уже достаточны — минимальный diff)

**`e2e-qa-0021`** (G4.1, AC=0.7)

- `must_not` += «обещать прислать урок / демо-URL» (дубль guard)
- `answer_key_points`: «кратко перечислить 1–2 программы из каталога» — явнее

---

## Состав работ

### Фаза A — манифест v002 без `reviewed_by`

- [ ] **2.1** Скрипт или make-цель: copy `v001_2026-06-14.yaml` → `v002_2026-06-15.yaml`, `version: v002`, правки 7 items (diff-friendly)
- [ ] **2.2** Changelog-секция в начале v002 (comment block) или `v002-changelog.md` рядом — таблица id + что изменилось
- [ ] **2.3** Integrity-тесты: extend `test_dataset_integrity.py` — параметризация по версии или отдельный `test_e2e_qa_v002.py` (≥26 items, ids stable vs v001)
- [ ] **2.4** `make eval-validate DATASET=e2e/e2e-qa` на v002 (validate-only, **без** reviewed_by — ожидаем fail на E-13 или skip gate до фазы B)
- [ ] **2.5** ⛔ **СТОП:** показать пользователю diff 7 items (таблица was→became) — **без** `reviewed_by`

### Фаза B — после апрува эталонов

- [ ] **2.6** `reviewed_by: product-owner` на всех 26 items v002
- [ ] **2.7** `make eval-validate` + `make eval-sync DATASET=e2e/e2e-qa` (resolves v002)
- [ ] **2.8** Идемпотентность sync (повтор = 0 new)
- [ ] **2.9** Обновить [`evals/datasets/e2e/e2e-qa/README.md`](../../../../../../evals/datasets/e2e/e2e-qa/README.md) — текущая версия v002, changelog
- [ ] **2.10** Самопроверка DoD → summary

---

## DoD

| # | Критерий | Проверка |
|---|----------|----------|
| 1 | `v002_2026-06-15.yaml` — 26 items, те же `id` что v001 | integrity |
| 2 | 7 items с уточнёнными criteria по таблице выше | diff review |
| 3 | v001 **не редактируется** (E-11) | git diff |
| 4 | ⛔ Пользователь апрувил criteria diff | гейт |
| 5 | 100% `reviewed_by`, validate green | `make eval-validate` |
| 6 | Langfuse `e2e/e2e-qa/v002`, sync идемпотентен | sync ×2 |
| 7 | README датасета обновлён | файл |

---

## Связь с Task 03–04

| Вопрос | Решение |
|--------|---------|
| Compare v3 vs iter #1 | **v001** — иначе два параметра (prompt + dataset) |
| Зачем v002 сейчас | Judge alignment, регрессии #0005/#0023, post-v3 re-baseline |
| Когда прогон на v002 | После Task 04 или отдельный re-baseline exp (не блокер Task 03) |

---

## Артефакты

- `evals/datasets/e2e/e2e-qa/v002_2026-06-15.yaml`
- `evals/datasets/e2e/e2e-qa/README.md` (версия + changelog)
- `evals/tests/test_dataset_integrity.py` или `test_e2e_qa_v002.py`
- (опц.) `evals/scripts/bump_dataset_version.py` — copy v001→v002 helper

---

## Scope

**Трогаем:** `evals/datasets/e2e/e2e-qa/`, integrity tests, (опц.) scripts.

**НЕ трогаем:** v001 yaml, backend/prompts, `evals/configs/*`, Task 03 прогон.

---

## Риски

| Риск | Митигация |
|------|-----------|
| Ужесточение criteria → искусственный рост/падение scores | v001 для E-7 compare; v002 для следующего baseline |
| Judge всё ещё variance на borderline 0.70 | must_not + явные key_points; не гнаться за score в Task 02 |
| 7 items — субъективный апрув | diff table в фазе A |

---

## ⛔ Гейт

Старт реализации — после **«ок»** на plan. Task 03 код — после закрытия Task 02 **или** явного waiving v002 («prompt-only на v001»).
