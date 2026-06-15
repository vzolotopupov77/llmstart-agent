# Plan: Задача 03 — Candidate #2 (E-22 iter 2)

> **Статус:** ✅ закрыт
> **Compare baseline (A):** `candidate-rag-first-prompt--e2e-qa--476018c9--20260615T094647Z` (0.631)

---

## Выбор направления (E-22 iter 2)

Источник: analyze [candidate run](../../../../../../evals/reports/candidate-rag-first-prompt--e2e-qa--476018c9--20260615T094647Z.md), [compare vs baseline](../../../../../../evals/reports/compare--baseline-react-chroma--e2e-qa--476018c9--20260615T083100Z--vs--candidate-rag-first-prompt--e2e-qa--476018c9--20260615T094647Z.md), [exp-003](../../../../../../evals/reports/exp-003-candidate-rag-first-prompt.md).

| Вариант | Сигнал из данных | Оценка потенциала |
|---------|------------------|-------------------|
| **Смена модели** (`gpt-4o-mini` → `gpt-4o`) | Провалы с `faithfulness=1.0` и явным «нет данных» при вызванном RAG (#2, #23, #21) — не нехватка reasoning, а инструкции | Средний; дороже; смешивает model×prompt; `benchmark-gpt-4o` на v1, не на iter #1 |
| **Улучшение системного промпта** | После v2: **generation 10**, retrieval 5 (было 9); rec #1 «Generation (приоритет)»; `task_completion` 🔴 0.612 | **Высокий** |
| **Рекомендации analyze** | #1 generation/key_points · #3 behavior (payment #9, segment) · регрессии #3, #21 (intensive/schedule) | **Высокий** → реализуется через **prompt v3** |

**Решение:** iter #2 = **системный промпт v3** (следование rec #1 и #3 analyze). Модель, retrieval, judge — без изменений (E-7).

---

## Гипотеза

После v2 (RAG-first) агент **ищет в KB**, но **не синтезирует ответ по `answer_key_points`**: говорит «точных данных нет», хотя в KB есть ориентиры (длительность до 2 ч, вечер/выходные, записи); путает интенсивы (#21); не завершает mock-оплату (#9). **v3** добавит правила синтеза фактов из retrieval, disambiguation `vibe-coding-intensive` и усиленную воронку mock-payment → **рост `avg_answer_correctness`** и **`avg_task_completion`** без регрессии faithfulness.

**Целевые items (из analyze + compare):** #2, #3, #9, #21, #23 (+ снятие регрессий #3, #21 vs iter #1).

---

## Candidate-конфиг (предложение)

```yaml
# evals/configs/candidate-generation-keypoints-v3.yaml
config_id: candidate-generation-keypoints-v3
comment: "Iter #1 candidate + agent-system-prompt-v3 (generation/key_points, E-7)"
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
  name: agent-system-prompt-v3

datasets:
  e2e-qa: v001
```

**Единственное отличие vs `candidate-rag-first-prompt`:** `prompt.name` → `agent-system-prompt-v3`.

---

## Черновик `agent-system-prompt-v3` (v2 + блок)

```
Дополнительно (v3, eval-fix generation + behavior):

9. После search_knowledge_base включай в ответ все релевантные факты из результатов:
   расписание (вечер/выходные как ориентир), длительность (до ~2 часов), формат занятий,
   наличие записей. Не пиши «точных данных нет» / «уточните у поддержки», если KB
   содержит хотя бы ориентиры.

10. Вопросы про интенсив / семинары / vibe-coding — привязывай к продукту
    vibe-coding-intensive (code из каталога): структура (семинары, практика, чат-поддержка).

11. Mock-оплата: при явном текстовом «оплатил» / подтверждении без чека — вызови
    confirm_payment с product_id из контекста диалога; если инструмент вернул ошибку
    (нет pending payment) — поблагодари за оплату и запроси email/телефон/имя для save_lead.

12. Multi-turn: учитывай предыдущие реплики assistant; сначала ответь на исходный вопрос
    пользователя, затем предлагай альтернативы; не подменяй продукт без объяснения.
```

---

## Состав работ (после апрува)

- [x] `backend/app/agent/prompts.py` — `SYSTEM_PROMPT_V3` + registry
- [x] `backend/tests/test_prompts.py` — smoke v3
- [x] `evals/configs/candidate-generation-keypoints-v3.yaml`
- [x] Перезапуск backend (config_id подхватывается)
- [x] `make eval-experiment CONFIG=evals/configs/candidate-generation-keypoints-v3.yaml`
- [x] `make eval-compare` A=`…094647Z` B=`…144346Z`
- [x] `evals/reports/exp-004-candidate-generation-keypoints-v3.md` + строка в `experiments-log.md`
- [x] ⛔ Самопроверка DoD → summary

## DoD

| # | Критерий |
|---|----------|
| 1 | Candidate отличается от iter #1 **только** `prompt.name` (E-7) |
| 2 | Прогон 26 items на `e2e-qa` v001, JSON + analyze |
| 3 | Compare vs `…094647Z` (iter #1, не baseline v1) |
| 4 | exp-004 + experiments-log; E-22 → 2/2 |
| 5 | ⛔ Пользователь видит compare и решение |

---

## Scope

**Трогаем:** `prompts.py`, `test_prompts.py`, `evals/configs/candidate-generation-keypoints-v3.yaml`, reports.

**НЕ трогаем:** retrieval backend, judge, model, `e2e-qa` v001 items, iter #1 config.

---

## Риски

- Усиление prompt → новые регрессии на других items (16 стабильных в exp-003).
- Item #9 может требовать tool fix, не только prompt — если v3 не поможет, фиксируем в error analysis для eval-04.

---

## ⛔ Гейт

**Стоп до явного «ок» / «go» на гипотезу + config_id + v3 draft.**

После апрува — реализация и прогон без повторного согласования scope.
