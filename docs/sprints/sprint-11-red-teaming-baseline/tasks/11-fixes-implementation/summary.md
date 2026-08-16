# Summary: Task 11 — fixes-implementation

> **План:** [plan.md](./plan.md)
> **Sprint:** [../../README.md](../../README.md)
> **Дата закрытия:** 2026-08-15

---

## Что реализовано

Пакеты FIX-1…FIX-5 из `practice/redteam/fix-decisions.md` за флагом `SECURITY_ENABLED` (default `true`).

- Флаг и `EVAL_ACCESS_KEY` в `Settings` / `.env.example`
- Входной guard (`HACKED:`, обёртки `<system>` / `System:` / `[SYSTEM]`, форматный медтест) в `chat()` до развилки JSON/SSE
- Выходной guard в общем модуле: `run_chat_turn` и `_iter_tail_sse_events`
- Policy `confirm_payment` / `save_lead` в `tool_adapter._run_sync` до `execute_tool`
- `SYSTEM_PROMPT_V6` + выбор default-промпта под флагом (выкл. → V1); V1–V5 не менялись
- Гейт `config_id`: заголовок `X-LLMStart-Eval-Key`; `evals/scripts/agent_task.py` шлёт ключ, если он задан
- Документация флагов: `backend/README.md`, раздел в `practice/redteam/tooling-setup.md`

`promptfooconfig.yaml`, `redteam-tests.yaml`, значение canary и `baseline-before/` не менялись.

---

## Отклонения от плана

- Ветка `feat/sprint-11-11-fixes-implementation` не создавалась: спринт 11 незакоммичен на `main`, как задачи 01–10.
- Коммит фиксов не делался в этой задаче — пользователь коммитит сам (хеш попадёт в манифест задачи 12).
- `make test-mcp`: `test_neo4j_smoke` падает при недоступном Neo4j; к фиксам не относится. `make test-backend` и `make lint-backend` зелёные.

---

## Принятые решения

Решения задачи 10 не пересматривались. Реализация без новых развилок.

---

## Проблемы и решения

| Проблема | Как решили |
|---|---|
| `mcp_server` в backend venv ставится копией wheel | после правки `payments.py` нужен `uv sync --reinstall-package llmstart-agent-mcp-server` |
| Windows `curl` / `curl.exe` ломает JSON в `-d` | ручные проверки через `Invoke-RestMethod` / `Invoke-WebRequest` + UTF-8 с сырого тела |

---

## Итог DoD

**Агент проверяет:**

| # | Критерий | Результат |
|---|---|---|
| 1 | Находки FIX или defer | ✅ FIX-1…5; D-01…D-12 не трогались |
| 2 | `SECURITY_ENABLED` default `true` | ✅ |
| 3 | Guard'ы смотрят флаг | ✅ тесты on/off |
| 4 | Выходной guard JSON и SSE | ✅ |
| 5 | Маркер ровно `[SECURITY_BLOCKED]` | ✅ |
| 6 | V1–V5 не изменены | ✅ diff `prompts.py` — только V6 |
| 7 | Эквивалентность при флаге `false` | ✅ |
| 8 | Happy-path воронки | ✅ policy B2C/B2B + API |
| 9 | lint + backend tests | ✅ `make lint-backend`; pytest 87 passed / 3 skipped |
| 10 | yaml не изменены | ✅ |
| 11 | Canary не изменён | ✅ |
| 12 | Секреты не в репо | ✅ пустой `EVAL_ACCESS_KEY` в example |

**Пользователь проверяет:** ✅ 2026-08-15 (trade-off входа, симметрия путей, гейт `config_id`, ручной «я оплатил» без маркера).

---

## Что дальше

- **Задача 12** — `promptfoo redteam eval` на тех же сценариях при `SECURITY_ENABLED=true`; в манифест — commit фиксов после того, как пользователь его создаст.
- В `.env` для eval: `EVAL_ACCESS_KEY` и заголовок (скрипт подставит сам).

---

## Ссылки

- Решения: `practice/redteam/fix-decisions.md`
- Предыдущая: [summary задачи 10](../10-fix-decisions/summary.md)
- Следующая: [plan задачи 12](../12-baseline-after-run/plan.md)
