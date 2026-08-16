# Summary: Task 02 — tooling-setup

> **План:** [plan.md](./plan.md)
> **Sprint:** [../../README.md](../../README.md)
> **Артефакты:** [`practice/redteam/tooling-setup.md`](../../../../../practice/redteam/tooling-setup.md), [`practice/redteam/smoke/`](../../../../../practice/redteam/smoke/)
> **Дата закрытия:** 2026-08-14

---

## Что реализовано

- **Promptfoo 0.122.0** — версия запинена в `tooling-setup.md`; дальше только `npx promptfoo@0.122.0`.
- **Три skills** в `.agents/skills/` + `skills-lock.json`; секция «Red team (Promptfoo)» в `40-skills-router.mdc`.
- **Canary** — `build_system_prompt()` в `ReactRunner.__init__`, значение из `SECURITY_CANARY_TOKEN`; unit-тесты `test_react_runner_canary.py` (5 passed).
- **Smoke** — `practice/redteam/smoke/promptfooconfig.yaml`: HTTP-таргет `:8003/api/v1/chat` + OpenRouter `reasoning.effort: none`; прогон `eval-MvX-2026-08-14T08:49:46`, 2/2 passed.
- **Конфиг** — `SECURITY_CANARY_TOKEN`, `OPENROUTER_API_KEY` в `.env.example`.
- **Вспомогательное** — `practice/redteam/smoke/run-smoke.ps1` (UTF-8 лог на Windows); `scripts/uv.cmd` + `UV` в `Makefile` (обход отсутствия `uv` в PATH на Windows).

---

## Отклонения от плана

| План | Факт | Причина |
|---|---|---|
| Артефакт `backend/app/agent/prompts.py` в README спринта | Изменён `react_runner.py` | По согласованному решению: runtime-обёртка в конструкторе, не в версиях V1–V5 |
| — | `scripts/uv.cmd`, правка `Makefile` | `make dev-backend` падал: `uv` не в PATH Windows-терминала |
| — | `run-smoke.ps1`, UTF-8 `smoke-output.txt` | `Tee-Object` без `-Encoding utf8` ломал кириллицу в логе |

---

## Принятые решения

| Решение | Причина |
|---|---|
| Canary через `build_system_prompt()`, не в `PROMPT_REGISTRY` | Покрывает default и `config_id`; V1–V5 остаются воспроизводимыми для eval |
| Smoke: `transformResponse: json.message`, `channel: telegram` | Соответствует грейдингу спринта (plain `message`) |
| `OPENROUTER_API_KEY` в smoke; тот же ключ, что `OPENAI_API_KEY` | Один ключ OpenRouter на backend и Promptfoo |
| Pin **0.122.0**, не `@latest` | Воспроизводимость прогонов «до/после» |

---

## Проблемы и решения

| Проблема | Как решили |
|---|---|
| `uv` не в PATH → `make dev-backend` падает | Официальный установщик uv + `scripts/uv.cmd` в Makefile на Windows |
| PowerShell `curl` — алиас `Invoke-WebRequest` | В чек-листе: `curl.exe` или `Invoke-RestMethod` |
| Mojibake в `smoke-output.txt` | UTF-8 отчёт + `run-smoke.ps1` |
| `not-contains` с `{{env.SECURITY_CANARY_TOKEN}}` в assert | Заменён на javascript-assert с `process.env` |

---

## Итог DoD

| # | Критерий | Результат |
|---|---|---|
| 1 | Node.js в диапазоне | ✅ v24.14.1 |
| 2 | Promptfoo запинен | ✅ 0.122.0 в `tooling-setup.md` |
| 3 | 3 skill на диске | ✅ `.agents/skills/promptfoo-*` |
| 4 | Skills в роутере | ✅ `40-skills-router.mdc` |
| 5 | Backend жив | ✅ `/health`, `/ready` → 200 |
| 6 | Реальный turn с tools | ✅ smoke + ручная проверка |
| 7 | OpenRouter, reasoning off | ✅ `SMOKE_OK`, `effort: none` |
| 8 | Canary в промпте, не в ответе | ✅ unit-тесты + smoke assert |
| 9 | Smoke зелёный | ✅ exit 0, 2/2 |
| 10 | Секреты не в git | ✅ |

**Пользователь:** ✅ подтверждено 2026-08-14.

---

## Что дальше

- **Задача 03 — plugin-selection:** таблица «риск → плагин → почему» из `threat-model.md` §7; исключения `bola`/`bfla` из §7.2–7.3.
- **Задача 04:** `defaultTest` assert на canary-строку из §7.1; `purpose` из §5.
- **Задача 08+:** smoke-команда и pin версии из `tooling-setup.md`; canary в run-manifest.

---

## Ссылки

- `practice/redteam/tooling-setup.md`
- `practice/redteam/smoke/promptfooconfig.yaml`
- `backend/app/agent/react_runner.py`, `backend/app/core/config.py`
- `backend/tests/test_react_runner_canary.py`
