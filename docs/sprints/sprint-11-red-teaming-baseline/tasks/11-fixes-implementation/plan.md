# Task 11: fixes-implementation

> **Sprint:** [../../README.md](../../README.md)
> **Тип:** feat
> **Ветка:** `feat/sprint-11-11-fixes-implementation`
> **Spec:** без spec — реализация по `practice/redteam/fix-decisions.md`

---

## Цель

Реализовать решения из задачи 10 за флагом `SECURITY_ENABLED` (по умолчанию включён), не тронув ни конфиг, ни набор кейсов, ни canary.

**Боль предыдущего шага:** решения без кода не меняют baseline. Но реализация «в лоб» ломает сам эксперимент: достаточно поставить выходной guard только в JSON-ветке — и прогон «после» станет зелёным при незащищённом веб-виджете. Или закрутить входной guard так, что агент начнёт отказывать легитимным вопросам про оплату: формально безопасность выросла, фактически продукт перестал работать.

**Флаг — инструмент методологии, не украшение:** при `SECURITY_ENABLED=false` агент обязан вести себя ровно как в baseline «до». Это единственный способ доказать, что разница между прогонами объясняется фиксами.

**Ограничение из архитектуры проекта:** версии `SYSTEM_PROMPT_V1…V5` зафиксированы под воспроизводимость eval'ов предыдущих спринтов. Править их нельзя — hardening оформляется новой версией.

> 💡 **Skills:** `python-testing-patterns` (тесты guard'ов), `sharp-edges` (проверить, что новые флаги не создают опасных конфигураций по умолчанию).

---

## Состав работ

**1. Флаг**

- [ ] В `Settings` (`core/config.py`) поле `security_enabled` с алиасом `SECURITY_ENABLED`, default `true`
- [ ] `SECURITY_ENABLED` и `SECURITY_CANARY_TOKEN` в `.env.example` с пояснениями
- [ ] Fail-safe: отсутствие переменной означает «защита включена», а не «выключена»

**2. Реализация по слоям строго из `fix-decisions.md`**

- [ ] Промпт-хардненинг — **новая** `SYSTEM_PROMPT_V6` в `agent/prompts.py` + запись в `PROMPT_REGISTRY`; V1–V5 не трогать
- [ ] Выбор промпта под флагом в `agent/react_runner.py`: флаг включён → default-путь использует V6; выключен → прежний V1
- [ ] Входной guard — в `api/routes/chat.py` или middleware в `factory.py`, по решению задачи 10
- [ ] Выходной guard — **в обоих путях**: `run_chat_turn` и `_iter_tail_sse_events` в `services/agent_service.py`; логику вынести в отдельный модуль, не дублировать
- [ ] Policy инструментов — в `mcp_client/tool_adapter.py::_run_sync`, до вызова `execute_tool`, с использованием `TurnContext`
- [ ] Гейт `config_id` — по варианту из задачи 10
- [ ] Все блокировки возвращают пользователю ровно маркер `[SECURITY_BLOCKED]` из конфига задачи 04

**3. Симметрия путей и эквивалентность при выключенном флаге**

- [ ] Проверить оба канала: JSON (`Accept: application/json`) и SSE (`Accept: text/event-stream`) — guard срабатывает одинаково
- [ ] Проверить, что при `SECURITY_ENABLED=false` поведение совпадает с baseline «до»: промпт V1, guard'ы неактивны, policy не вмешивается
- [ ] Зафиксировать отдельным тестом, а не проверкой на глаз

**4. Тесты**

- [ ] На каждый guard — pytest в двух состояниях флага: включён блокирует, выключен пропускает
- [ ] Policy платёжного сценария: подтверждение оплаты без предшествующей ссылки не приводит к `save_lead`
- [ ] Выходной guard: canary и имена инструментов не покидают приложение ни в JSON, ни в SSE
- [ ] Регрессия happy-path: воронка B2C от вопроса до лида работает при включённом флаге
- [ ] Для каждого файла Edit → Sanitize → Verify: `uv run ruff check --fix`, `uv run ruff format`, затем `make test-backend`

**5. Документация и фиксация**

- [ ] Описать флаги и поведение guard'ов в `backend/README.md`
- [ ] Дополнить `practice/redteam/tooling-setup.md` разделом «как воспроизвести оба состояния»
- [ ] Записать commit фиксов — он попадёт в манифест прогона задачи 12
- [ ] Самопроверка по DoD; после «ок» — `summary.md`

---

## Критерии готовности (DoD)

**Агент проверяет:**

| # | Критерий | Способ проверки |
|---|----------|-----------------|
| 1 | Каждая находка из `fix-decisions.md` имеет реализацию либо явный `defer` | сверка перечней |
| 2 | `SECURITY_ENABLED` по умолчанию `true` | тест на `Settings` без переменной в окружении |
| 3 | Все новые guard'ы проверяют флаг | grep по местам внедрения + тесты в двух состояниях |
| 4 | Выходной guard работает в обоих путях | тесты на JSON и на SSE |
| 5 | Блокировка возвращает ровно `[SECURITY_BLOCKED]` | тест на текст ответа |
| 6 | Версии промпта V1–V5 не изменены | `git diff backend/app/agent/prompts.py` — только добавление V6 |
| 7 | При `SECURITY_ENABLED=false` поведение эквивалентно baseline «до» | тест эквивалентности |
| 8 | Happy-path воронка работает при включённом флаге | регрессионный тест |
| 9 | `make lint` и `make test-backend` зелёные | команды |
| 10 | `promptfooconfig.yaml` и `redteam-tests.yaml` не изменены | `git diff` пустой, sha256 совпадают |
| 11 | Значение canary не изменено | сравнение с `run-manifest.md` задачи 08 |
| 12 | Секреты не попали в репозиторий | `git diff` не содержит значений ключей и canary |

**Пользователь проверяет:**

- Принимает trade-off по false positives входного guard'а: видел примеры легитимных вопросов, которые он блокирует
- Убедился, что guard стоит в обоих путях, а не только в том, по которому бьёт red team
- Согласен с реализацией гейта `config_id` и с влиянием на eval-процесс
- Проверил вручную одну-две находки из triage при `SECURITY_ENABLED=true`
- Проверил, что воронка от вопроса до лида по-прежнему проходит

---

## Артефакты

- `backend/app/core/config.py` — флаг `SECURITY_ENABLED`
- `backend/app/agent/prompts.py` — `SYSTEM_PROMPT_V6`
- `backend/app/agent/react_runner.py` — выбор промпта под флагом
- `backend/app/api/routes/chat.py` и/или `factory.py` — входной guard, гейт `config_id`
- `backend/app/services/agent_service.py` + выделенный модуль guard'ов — выходной guard в обоих путях
- `backend/app/mcp_client/tool_adapter.py` — policy инструментов
- Тесты в `backend/tests/`
- `.env.example`, `backend/README.md`, дополнение `practice/redteam/tooling-setup.md`

---

## Scope

**Трогаем:** `backend/` (и `mcp_server/` при необходимости по `fix-decisions.md`), тесты, `.env.example`, документацию флагов.

**НЕ трогаем:** `practice/redteam/promptfooconfig.yaml`, `redteam-tests.yaml`, значение canary, содержимое `baseline-before/`, фиксы из списка `defer`.

---

## Риски и допущения

- Слишком агрессивный guard ломает легитимную воронку — регрессионный тест happy-path обязателен, а не опционален.
- Guard только в JSON-пути даст ложно-зелёный прогон «после» при незащищённом виджете.
- Гейт `config_id` может сломать существующий eval-процесс — вариант выбран в задаче 10 с учётом этого.
