# Plan: Задача 04 — Candidate #1 на `e2e-qa` v002 (re-baseline)

> **Статус:** ✅ закрыт
> **Предшественник:** Task 03 отклонил v3; winning config — `candidate-rag-first-prompt` (v2 prompt, 0.631 на v001)

---

## Цель

Зафиксировать **первый прогон winning candidate** (`candidate-rag-first-prompt`) на **v002** с уточнёнными criteria (Task 02) — отдельный замер, не смешивая с E-7 iter #2.

---

## Зачем (контекст)

| Факт | Следствие |
|------|-----------|
| v002 = те же 26 items, **7 items** с sharpened criteria | Скоры на v001 и v002 **несравнимы** через `compare` (E-16) |
| iter #1 run `…094647Z` только на **v001** | Нет baseline candidate на актуальной рубрике |
| v3 отклонён | Следующие улучшения агента оцениваем относительно **v002 baseline** |

**Не цель:** новая итерация eval-fix (E-7) или смена промпта/модели — только смена версии датасета в конфиге.

---

## Гипотеза

Тот же агент (v2 prompt) на v002 даст **другую** `avg_answer_correctness` vs 0.631 на v001: часть провалов (#9, #16, #3, #21…) может стать строже по rubric, часть — честнее отражать реальное качество. Нужен замер для eval-04 и следующих candidate-итераций.

---

## Конфиг (предложение)

Новый файл — **не** меняем `candidate-rag-first-prompt.yaml` (v001 pin immutable для истории exp-003).

```yaml
# evals/configs/candidate-rag-first-prompt-e2e-qa-v002.yaml
config_id: candidate-rag-first-prompt-e2e-qa-v002
comment: "Winning iter #1 candidate on e2e-qa v002 (criteria rebaseline, not E-7)"
benchmark_only: false

agent:
  impl: langchain-react
  api_url: http://127.0.0.1:8003/api/v1/chat

retrieval:
  backend: chroma-embedded

model:
  provider: openrouter
  name: openai/gpt-4o-mini
  temperature: 0.0

judge:
  provider: openrouter
  name: google/gemini-2.5-flash-lite
  temperature: 0.0

prompt:
  source: code
  name: agent-system-prompt-v2

datasets:
  e2e-qa: v002
```

**Единственное отличие vs iter #1 config:** `config_id` + `datasets.e2e-qa: v002`. Агент, prompt, judge, retrieval — идентичны.

---

## Состав работ (после апрува)

- [x] `evals/configs/candidate-rag-first-prompt-e2e-qa-v002.yaml`
- [x] `make eval-sync DATASET=e2e-qa` (v002 в Langfuse)
- [x] Backend перезапущен (`:8003`)
- [x] `make eval-experiment` → `…151141Z` (failed `…150903Z` — backend)
- [x] `make eval-analyze RUN=…151141Z`
- [x] `evals/reports/exp-005-candidate-rag-first-prompt-v002.md` + experiments-log
- [x] Fix `load_dataset_context` — pinned version → Langfuse dataset name
- [x] ⛔ Самопроверка DoD → summary

## DoD

| # | Критерий |
|---|----------|
| 1 | Конфиг: тот же prompt/model/judge, только `datasets.e2e-qa: v002` |
| 2 | Прогон 26 items на `e2e/e2e-qa/v002`, JSON + analyze |
| 3 | exp-005 с интерпретацией Δ vs v001 `…094647Z` (qualitative) |
| 4 | experiments-log обновлён |
| 5 | ⛔ Пользователь видит analyze + exp-report |

---

## Scope

**Трогаем:** `evals/configs/candidate-rag-first-prompt-e2e-qa-v002.yaml`, reports, sprint README.

**НЕ трогаем:** `prompts.py`, iter #1 config, v001/v002 manifests, agent code.

---

## Ограничения

- **`make eval-compare` v001↔v002 запрещён** (E-16) — только run-level таблица в exp-report.
- Это **не** закрывает новую E-7 итерацию; E-22 уже 2/2 (Task 03).
- Task 05 (закрытие спринта) — после Task 04.

---

## Риски

- Judge variance: v001 vs v002 Δ может частично быть шумом судьи на изменённых criteria — смотреть per-item на 7 diff items из [v002-changelog](../../../../../../evals/datasets/e2e/e2e-qa/v002-changelog.md).

---

## ⛔ Гейт

**Стоп до «ок» / «go» на config_id + scope.**
