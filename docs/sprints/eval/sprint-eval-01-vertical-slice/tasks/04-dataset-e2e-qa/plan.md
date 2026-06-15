# Plan: Задача 04 — Манифест e2e-qa + review + sync

> **Спринт:** [../../README.md](../../README.md) · **Методология:** [.methodology/eval/eval-methodology.md](../../../../../../.methodology/eval/eval-methodology.md)
> **Статус:** ✅ Done

## Цель

Первый eval-манifest `evals/datasets/e2e/e2e-qa/v001_2026-06-14.yaml` (≥20 items), Pydantic + integrity-тесты, **утверждённые** эталоны с `reviewed_by`, sync в Langfuse (`e2e/e2e-qa/v001`, E-16).

## Соответствие методологии

- **E-11** — иммутабельный файл-версия `v001_*`
- **E-12** — YAML, criteria в `expected_output` без декодера
- **E-13** — ⛔ review эталонов до `reviewed_by`
- **E-14** — `gt_quality: verified | approximate`
- **E-15** — Pydantic + integrity-тесты
- **E-16** — folders-as-versions в Langfuse

**Входы:** ✅ [dataset-map.md](../../../../eval/dataset-map.md), ✅ [metrics-map.md](../../../../eval/metrics-map.md), `datasets/b2c/v2/dataset.jsonl`, `data/b2c/`

---

## Состав работ

### Фаза A — манифест без `reviewed_by`

- [ ] **4.1** Pydantic: `DatasetManifest`, `DatasetItem`, `load_manifest()` в `evals/scripts/dataset_models.py` (отдельно от `RunConfig`)
- [ ] **4.2** Отбор **≥22 items** из `datasets/b2c/v2/dataset.jsonl` для e2e-репрезентативности:
  - G1 (формат): ≥4 · G2 (продукт): ≥3 · G3/G4 (objection): ≥4 · G5: ≥2 · G7 (segment): ≥2 · tools subset: ≥2 · synthetic: ≥5
  - ~60% extraction / ~40% synthetic; ~75% single / ~25% multi-turn
  - Стабильные `id`: префикс `e2e-qa-`, маппинг из legacy id где возможно
- [ ] **4.3** Конвертация schema: legacy `input` (string|array) → manifest `input`; `expected_output` — criteria pattern (key_points, segment, product_codes, tools, must_not)
- [ ] **4.4** `evals/datasets/e2e/e2e-qa/v001_2026-06-14.yaml` + `README.md`
- [ ] **4.5** Integrity-тесты `evals/tests/test_dataset_integrity.py` (≥20 items, id unique, **без** reviewed_by пока — отдельный test file или skip gate test)
- [ ] **4.6** ⛔ **СТОП:** показать пользователю сводку эталонов (таблица 5–10 sample items + ссылка на полный файл) — **без** `reviewed_by`

### Фаза B — после апрува эталонов

- [ ] **4.7** Проставить `reviewed_by` + финальный `gt_quality` по item
- [ ] **4.8** Негативный тест: item без `reviewed_by` → validate fail
- [ ] **4.9** Реализовать `sync_datasets.py`: upsert по `id`, dataset name `e2e/e2e-qa/v001`, auth_check
- [ ] **4.10** `make eval-sync DATASET=e2e/e2e-qa` — идемпотентность (повтор = 0 new)
- [ ] **4.11** Самопроверка DoD

---

## Scope

**Входит:** e2e-qa v001, dataset models, integrity tests, sync (один датасет)

**Не входит:** evaluators, baseline run (задача 05), остальные датасеты (eval-02)

---

## DoD

| # | Критерий | Проверка |
|---|----------|----------|
| 1 | ≥20 items, 100% reviewed_by после гейта | integrity + Langfuse UI |
| 2 | Pydantic + integrity зелёные | `make eval-validate` |
| 3 | Sync идемпотентен | повторный sync |
| 4 | Негативный тест reviewed_by | pytest |
| 5 | ⛔ Эталоны утверждены пользователем | до reviewed_by |
| 6 | Пользователь: 5 items в Langfuse UI | summary evidence |

---

## Артефакты

- `evals/datasets/e2e/e2e-qa/v001_2026-06-14.yaml`
- `evals/datasets/e2e/e2e-qa/README.md`
- `evals/scripts/dataset_models.py`
- `evals/scripts/sync_datasets.py` (реализация)
- `evals/tests/test_dataset_integrity.py`

---

## Риски

| Риск | Митигация |
|------|-----------|
| Legacy multi-turn ChatML vs manifest input | Сохранить массив messages в YAML as-is |
| approximate эталоны | gt_quality=approximate; baseline — относительное сравнение (E-14) |
| Langfuse auth | fail-fast в sync; `.env` keys |
