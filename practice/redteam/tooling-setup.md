# Tooling setup — Sprint 11 red team

> **Задача:** [02-tooling-setup](../../docs/sprints/sprint-11-red-teaming-baseline/tasks/02-tooling-setup/plan.md)
> **Дата:** 2026-08-14

Сводка окружения Promptfoo и smoke-контура для спринта red-teaming-baseline.

---

## Node.js

| Параметр | Значение |
|---|---|
| Требование | `^20.20.0` или `>=22.22.0` |
| Фактическая версия | `v24.14.1` |
| Проверка | `node --version` |

---

## Promptfoo

| Параметр | Значение |
|---|---|
| Запиненная версия | **0.122.0** (`practice/redteam/package.json`, `devDependencies`, точная версия) |
| Установка | `npm install --prefix practice/redteam` с `PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1` (см. ниже) |
| Бинарь | `practice/redteam/node_modules/.bin/promptfoo` |
| Проверка CLI | `npm --prefix practice/redteam run promptfoo -- --version` |
| Red team CLI | `npm --prefix practice/redteam run promptfoo -- redteam --help` |

Дальше по спринту использовать только `@0.122.0`, не `@latest`.

**Почему локальная установка, а не `npx`:** `npx promptfoo@0.122.0` при каждом запуске раскладывает всё дерево зависимостей (~710 пакетов) в кэш npm — `_npx` и `_cacache`. За один день 2026-08-14 это дало ~1.4 ГБ и привело к `ENOSPC`: Cursor не смог записать даже лог терминала. Локальный `node_modules` (~1.6 ГБ) лежит на рабочем диске `D:` вместе с репозиторием и не растёт от повторных прогонов. `node_modules/` покрыт `.gitignore`; `package-lock.json` коммитим для воспроизводимости.

### Установка без Chromium

Транзитивная зависимость promptfoo — `@playwright/browser-chromium@1.62.1` со скриптом `install: node install.js`, который качает `chromium`, `chromium-headless-shell` и `ffmpeg`: **~700 МБ** (браузеры кладутся не в `node_modules`, а в кэш Playwright — см. `PLAYWRIGHT_BROWSERS_PATH` ниже). В спринте браузерные провайдеры не используются (таргет — HTTP + OpenRouter), поэтому загрузку подавляем.

PowerShell:

```powershell
$env:PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD = "1"
npm install --prefix practice\redteam
```

bash:

```bash
PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm install --prefix practice/redteam
```

Признак срабатывания в логе установки: `Skipping browsers download because PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD env variable is set`.

Переменная нужна **только на время установки** — на `eval` и `redteam generate` она не влияет. Если понадобится браузерный провайдер (`provider: browser`) — переустановить без неё.

### Дисковая гигиена (кэши)

После инцидента `ENOSPC` 2026-08-14 кэши уведены с `C:` на рабочий диск переменными окружения (User scope):

| Переменная | Значение |
|---|---|
| `TEMP` / `TMP` | `D:\Temp` |
| `HF_HOME` | `D:\caches\huggingface` |
| `UV_CACHE_DIR` | `D:\caches\uv` |
| `NPM_CONFIG_CACHE` | `D:\caches\npm` |
| `PLAYWRIGHT_BROWSERS_PATH` | `D:\caches\ms-playwright` |

`TEMP` здесь ключевая: Cursor перенаправляет кэши npm и uv внутрь `%TEMP%\cursor-sandbox-cache\<hash>\`, поэтому агентские установки идут туда, куда указывает `TEMP`, игнорируя `NPM_CONFIG_CACHE`. Переменные подхватываются только новыми процессами — после правки нужен перезапуск Cursor.

Кэши после установки не нужны, удаление безопасно — npm и Playwright скачают заново. Оговорки:

- Куда пишет текущая оболочка, проверяется через `npm config get cache` и `uv cache dir`.
- `npm cache clean --force` вычищает `_cacache` не полностью — остаток удаляется только вручную (`Remove-Item`).
- Снести весь `cursor-sandbox-cache` целиком — допустимо, Cursor пересоздаёт его сам. Именно это разблокировало терминал при `ENOSPC`.
- `pnpm` настраивать не нужно: он держит отдельный store на каждом диске (`D:\.pnpm-store`) ради хардлинков.
- uv-кэш обязан лежать на том же диске, что и `.venv`, иначе вместо хардлинков будут полные копии — то есть на `D:`, где и лежат venv'ы проектов.

---

## Skills (promptfoo)

Установлены из `skills.sh/promptfoo/promptfoo`:

| Skill | Назначение | Путь |
|---|---|---|
| `promptfoo-provider-setup` | HTTP-таргет, провайдеры, `transformResponse`, smoke против живого API | `.agents/skills/promptfoo-provider-setup/SKILL.md` |
| `promptfoo-redteam-setup` | Секция `redteam`, плагины, стратегии, параметры генерации | `.agents/skills/promptfoo-redteam-setup/SKILL.md` |
| `promptfoo-redteam-run` | `redteam generate` / `redteam eval`, экспорт, triage, rerun | `.agents/skills/promptfoo-redteam-run/SKILL.md` |

Установка (повтор):

```bash
npx skills add promptfoo/promptfoo \
  --skill promptfoo-provider-setup \
  --skill promptfoo-redteam-setup \
  --skill promptfoo-redteam-run \
  --yes
```

Роутер: `.cursor/rules/methodology/40-skills-router.mdc` → секция «Red team (Promptfoo)».

---

## Переменные окружения

| Переменная | Назначение |
|---|---|
| `OPENROUTER_API_KEY` | Нативный провайдер Promptfoo `openrouter:<model>` (тот же ключ OpenRouter, что и `OPENAI_API_KEY`) |
| `OPENAI_API_KEY` | Backend и MCP (OpenRouter через OpenAI-compatible API) |
| `SECURITY_CANARY_TOKEN` | Canary для runtime-обёртки в `ReactRunner.__init__` |

Значение canary зафиксировано в [threat-model.md](./threat-model.md) §6: `LLMSTART-CANARY-7f3a91c2e5b04d68`. Плейсхолдер — в `.env.example`; в git не коммитить реальные ключи.

**Reasoning:** в smoke и будущем red-team конфиге — `reasoning.effort: none` для OpenRouter.

---

## Backend target

| Параметр | Значение |
|---|---|
| Health | `GET http://127.0.0.1:8003/health` → 200 |
| Ready | `GET http://127.0.0.1:8003/ready` → 200 |
| Chat | `POST http://127.0.0.1:8003/api/v1/chat` без `session_id` |
| Тело smoke | `{"message": "...", "channel": "telegram"}` |
| Поле для грейдинга | `message` (plain text) |

Запуск: `make dev-backend` (порт `8003` из `Makefile`).

---

## Canary в агенте

- Обёртка: `backend/app/agent/react_runner.py` → `build_system_prompt()` в `ReactRunner.__init__`
- Покрывает default-runner и все runner'ы через `config_id`
- **Вне** флага `SECURITY_ENABLED`
- Версии `SYSTEM_PROMPT_V1…V5` не меняются; hardening — `SYSTEM_PROMPT_V6`

---

## Как воспроизвести оба состояния защиты

Флаг `SECURITY_ENABLED` (default `true`, отсутствие переменной = включено):

| Состояние | Env | Ожидание |
|---|---|---|
| Baseline «до» / отладка фиксов | `SECURITY_ENABLED=false` | Промпт V1, входной/выходной guard и tool policy не вмешиваются, `config_id` публичный |
| Baseline «после» / production | `SECURITY_ENABLED=true` или переменная не задана | Промпт V6, guard'ы и policy активны; `config_id` только с `X-LLMStart-Eval-Key` = `EVAL_ACCESS_KEY` |

Eval-скрипт `evals/scripts/agent_task.py` сам добавляет заголовок, если `EVAL_ACCESS_KEY` задан в окружении.

Canary (`SECURITY_CANARY_TOKEN`) не зависит от флага и **не меняется** между прогонами «до» и «после».

---

## Smoke

Конфиг: [smoke/promptfooconfig.yaml](./smoke/promptfooconfig.yaml)

Проверяет:

1. HTTP-таргет агента — непустой `message`, canary **не** в ответе
2. OpenRouter-провайдер — ответ с `SMOKE_OK`, reasoning off

```bash
npm --prefix practice/redteam run validate
```

**Windows (UTF-8 лог):**

```powershell
.\practice\redteam\smoke\run-smoke.ps1
```

**Или вручную:**

```bash
npm --prefix practice/redteam run smoke
```

Полная команда, если нужны другие флаги:

```bash
practice/redteam/node_modules/.bin/promptfoo eval \
  -c practice/redteam/smoke/promptfooconfig.yaml \
  --env-file .env \
  -o practice/redteam/smoke/smoke-output.json \
  --no-cache --no-share --no-progress-bar
```

На Windows для `smoke-output.txt` не используйте `Tee-Object` без `-Encoding utf8` — кириллица и box-drawing символы ломаются. Скрипт `run-smoke.ps1` пишет лог в UTF-8 без BOM.

Требует: установленный promptfoo (`npm install --prefix practice/redteam`), backend на `:8003`, `OPENROUTER_API_KEY` (или `OPENAI_API_KEY` — тот же ключ OpenRouter) и `SECURITY_CANARY_TOKEN` в `.env`.

Вывод последнего прогона: [smoke/smoke-output.txt](./smoke/smoke-output.txt).

**Последний прогон:** 2026-08-14 — 2/2 passed, exit 0 (`eval-MvX-2026-08-14T08:49:46`).
