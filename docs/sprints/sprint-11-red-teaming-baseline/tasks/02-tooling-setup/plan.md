# Task 02: tooling-setup

> **Sprint:** [../../README.md](../../README.md)
> **Тип:** chore
> **Ветка:** `chore/sprint-11-02-tooling-setup`
> **Spec:** без spec

---

## Цель

Работающий Promptfoo с запиненной версией, три установленных skill, живой таргет, canary в системном промпте и зелёный smoke-прогон.

**Боль предыдущего шага:** есть модель угроз, но нет инструмента и измерителя утечки.

---

## Решения (согласовано)

- Node.js: `^20.20.0` или `>=22.22.0` — **проверить** `node --version`; при необходимости установить (`winget install OpenJS.NodeJS.LTS`)
- Promptfoo: версию **запинить** после `npx promptfoo@latest --version`; далее только `@<pinned>`
- OpenRouter для Promptfoo: **нативный** `openrouter:<model>` + `OPENROUTER_API_KEY` в `.env`, плейсхолдер в `.env.example`
- Canary-токен: **runtime-обёртка** в `ReactRunner.__init__` (`backend/app/agent/react_runner.py`) поверх `system_prompt or SYSTEM_PROMPT` — покрывает и default-путь, и любой `config_id`; **вне** `SECURITY_ENABLED`; не меняется между прогонами «до/после». В текст версий `PROMPT_REGISTRY` не вписываем: иначе токен исчезает при другом `config_id` и V1–V5 перестают быть воспроизводимыми для eval'ов

---

## Состав работ

- [x] Проверить / установить Node.js нужной версии; зафиксировать в `tooling-setup.md`
- [x] `npx promptfoo@latest --version` → запинить; проверить `redteam --help`
- [x] Установить skills: `promptfoo-provider-setup`, `promptfoo-redteam-setup`, `promptfoo-redteam-run`; описать назначение каждого
- [x] Добавить три строки в `.cursor/rules/methodology/40-skills-router.mdc`
- [x] Настроить OpenRouter-провайдер; reasoning **выключен**; тестовый вызов
- [x] `make dev-backend`; `GET /health`, `GET /ready` → 200
- [x] Живой `POST /api/v1/chat` без `session_id` → 200, непустой `tools[]`
- [x] Вставить canary в `ReactRunner.__init__`; проверить, что он попадает в промпт и default-runner'а, и runner'а с `config_id`
- [x] Проверить отсутствие canary в обычном ответе на продуктовый вопрос
- [x] Зафиксировать значение canary в `.env` (`SECURITY_CANARY_TOKEN`) с плейсхолдером в `.env.example`; не хардкодить в исходник
- [x] Smoke: `practice/redteam/smoke/promptfooconfig.yaml` + `npx promptfoo@<pinned> eval` → exit 0
- [x] `practice/redteam/tooling-setup.md` — сводка
- [x] Самопроверка; после «ок» — `summary.md`

---

## Критерии готовности (DoD)

| # | Критерий | Способ проверки |
|---|----------|-----------------|
| 1 | Node.js в допустимом диапазоне | `node --version` |
| 2 | Promptfoo запинен в `tooling-setup.md` | сверка версий |
| 3 | 3 skill на диске | наличие `SKILL.md` |
| 4 | Skills в роутере | grep `promptfoo-` в `40-skills-router.mdc` |
| 5 | Backend жив | `curl :8003/health`, `/ready` |
| 6 | Реальный turn с tools | POST `/api/v1/chat` |
| 7 | OpenRouter отвечает, reasoning off | тест Promptfoo |
| 8 | Canary в промпте обоих путей (default и `config_id`), не в обычном ответе | unit-тест на `ReactRunner.system_prompt` + grep ответа |
| 9 | Smoke зелёный | exit 0 eval |
| 10 | Секреты не в git | `git diff` |

**Пользователь:** согласен с pin версии, smoke в реальный агент, canary вне `SECURITY_ENABLED`, запросы без `session_id`.

---

## Артефакты

- `practice/redteam/tooling-setup.md`
- `practice/redteam/smoke/promptfooconfig.yaml`
- `practice/redteam/smoke/smoke-output.txt`
- `backend/app/agent/react_runner.py` (canary в runtime-сборке промпта)
- `backend/app/core/config.py` (`SECURITY_CANARY_TOKEN`)
- `.env.example` (`OPENROUTER_API_KEY`, `SECURITY_CANARY_TOKEN`)
- `.cursor/rules/methodology/40-skills-router.mdc`

---

## Scope

**Трогаем:** перечисленные артефакты + smoke.

**НЕ трогаем:** red-team конфиг (задача 04), `SECURITY_ENABLED`, plugin-selection.

---

## Риски и допущения

- `nvm` может отсутствовать в PATH — fallback через `winget`.
- Локальный порт backend — `8003` (`Makefile`), не `8000` из api-contracts.
