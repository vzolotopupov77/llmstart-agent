# Sprint 11: red-teaming-baseline

> **Версия roadmap:** v0.3
> **Roadmap:** [../../roadmap.md](../../roadmap.md)
> **Статус:** ✅ Done
> **Открыт:** 2026-08-10
> **Закрыт:** 2026-08-16

---

## Преамбула

Это **классический процесс security-инженерии**, а не разовая проверка «на глаз». Цепочка воспроизводима и оставляет артефакт на каждом шаге:

1. Устанавливаем инструмент → проверяем, что он работает.
2. Под модель угроз подбираем, **чем именно** будем бить.
3. Генерируем конфигурацию проверки и **объясняем**, что она проверяет.
4. Генерируем сами проверки (тестовые сценарии) → **ревьюим** до боевого прогона.
5. Прогоняем baseline «до» → разбираем находки → выбираем путь фикса → чиним → **перепроверяем ровно те же кейсы** baseline «после».

**Инструмент:** [Promptfoo](https://www.promptfoo.dev/) red team.  
**Цель спринта:** не абстрактная «проверить безопасность», а **воспроизводимый baseline «до/после»** на конкретном агенте LLMStart.ru с **конкретными закрытыми находками** за флагом `SECURITY_ENABLED`.

---

## Цель спринта

Получить измеримый security-baseline публичного агента LLMStart.ru: модель угроз, зафиксированный набор red-team-сценариев Promptfoo, прогон «до» на агенте без защиты, осмысленные фиксы и прогон «после» на **тех же** сценариях — с итоговым отчётом и обновлённым roadmap.

---

## Контекст продукта

**LLMStart Agent** — публичный диалоговый агент без авторизации (Agent Core + MCP-сервер инструментов). На входе в спринт, вероятно, **нет ни одного слоя защиты**.

Концепт: [idea.md](../../concept/idea.md), [vision.md](../../concept/vision.md), [architecture.md](../../concept/architecture.md).

### Известные факты (передавать во все задачи без изменений)

| Факт | Значение |
|------|----------|
| Эндпоинт чата | `POST /api/v1/chat` на `http://localhost:8003` (см. [api-contracts.md](../../concept/api-contracts.md)) |
| Health | `GET /health`, `GET /ready` |
| MCP-инструменты (фактические, 8 шт.) | `vector_search`, `graph_search`, `global_catalog`, `text2cypher_tool`, `list_b2c_products`, `create_payment_link`, `confirm_payment`, `save_lead` |
| PROTECTED | Системные инструкции, canary-токен, имена/схемы/параметры инструментов, сериализованные tool-calls |
| DISCLOSABLE | Каталог, цены, программы, сегменты b2b/b2c |
| Бизнес-правило | `confirm_payment` нельзя вызывать без предшествующего `create_payment_link` для **того же продукта** в **этом же диалоге** |
| LLM-провайдер | OpenRouter — и для агента, и для генерации атак/грейдинга Promptfoo; **reasoning выключен** |
| Провайдер Promptfoo | Нативный `openrouter:<model>` + `OPENROUTER_API_KEY` в `.env` |
| Язык атак | **Русский — основной**; английский — дополнительный вектор смены языка |
| Изоляция кейсов | `session_id` **не передаём** в red-team-запросах |
| Canary-токен | Измеритель утечки; runtime-обёртка в `ReactRunner.__init__`, значение из `SECURITY_CANARY_TOKEN`; **вне** `SECURITY_ENABLED`; не меняется между прогонами |
| Грейдинг | Оцениваем поле `message` (plain-текст) при `channel: telegram`; `tools[]` и `message_html` в грейдинг не идут |
| Маркер блокировки | **`[SECURITY_BLOCKED]`** — закладывается в конфиг в задаче 04, реализуется в задаче 11 |
| `config_id` | Публичное поле `/chat` выбирает eval-конфиг из `evals/configs/` → **другой промпт и модель**. В red-team-запросах не передаём; риск и фикс — в scope спринта |
| Промпт по умолчанию | Default-путь использует `SYSTEM_PROMPT` = **V1**. Инструкции «принять оплату при ошибке `confirm_payment`» живут в V2 п.8 / V3 п.11 и доступны только через `config_id` |
| Платёжное правило в коде | `payments.py::confirm_payment` уже бросает `ValueError` без pending-записи. Проверяем **поведение агента** (имитация подтверждённой оплаты и переход к `save_lead`), не порядок вызовов |
| `session_id` в tools | Подставляется сервером через `TurnContext` (`agent_service.py`), LLM им не управляет → применимость `bola`/`bfla` низкая; под контролем модели только `product_id` |

> ⚠️ В `architecture.md` / `vision.md` указан устаревший список из 5 инструментов с `search_knowledge_base`. В конфиге и модели угроз — только **8 фактических имён** из `mcp_server/mcp_server/server.py`.

---

## Ограничения спринта

- **Конфигурацию** (`promptfooconfig.yaml`, задача 04) и **тестовые сценарии** (`redteam-tests.yaml`, задача 06) **не писать руками** — только через skills + промпт кодовому агенту с обязательным ревью человеком.
- Между baseline «до» (задача 08) и «после» (задача 12) меняется **только** код фиксов и флаг `SECURITY_ENABLED`. Конфиг и сценарии — **заморожены**.
- Повторный прогон — **исключительно** `promptfoo redteam eval`, **не** `redteam run`. Запуск — через локальный бинарь `practice/redteam/node_modules/.bin/promptfoo`, не через `npx` (см. `practice/redteam/tooling-setup.md`).
- Артефакты security-инженерии — в `practice/redteam/`; `plan.md` / `summary.md` задач — в `docs/sprints/sprint-11-red-teaming-baseline/tasks/`.
- Последовательность: нельзя генерировать конфиг до модели угроз; нельзя прогонять baseline «до» до ревью сценариев.

---

## DoD спринта

| # | Критерий | Способ проверки | Итог |
|---|----------|-----------------|------|
| 1 | Модель угроз и карта рисков с OWASP LLM / ASI Top 10 | `practice/redteam/threat-model.md` | ✅ |
| 2 | Promptfoo установлен, версия запинена, 3 skill установлены, smoke зелёный | `practice/redteam/tooling-setup.md`, `practice/redteam/smoke/` | ✅ |
| 3 | Плагины и стратегии обоснованы под карту рисков | `practice/redteam/plugin-selection.md` | ✅ |
| 4 | Конфиг и explainer сгенерированы, прошли ревью | `practice/redteam/promptfooconfig.yaml`, `config-explainer.md`, чек-лист задачи 05 | ✅ |
| 5 | Сценарии сгенерированы и прошли ревью | `practice/redteam/redteam-tests.yaml`, `test-review-notes.md` | ✅ |
| 6 | Baseline «до» сохранён | `practice/redteam/baseline-before/` | ✅ |
| 7 | Triage находок с привязкой к слою защиты | `practice/redteam/triage-before.md` | ✅ |
| 8 | Решения по фиксам без кода | `practice/redteam/fix-decisions.md` | ✅ |
| 9 | Фиксы реализованы за `SECURITY_ENABLED` (default: true) | diff `backend/`, `mcp_server/` | ✅ |
| 10 | Baseline «после» на тех же сценариях, сравнение «до/после» | `practice/redteam/baseline-after/`, `comparison.md` | ✅ |
| 11 | Итоговый отчёт, антипаттерны, backlog | `practice/redteam/final-report.md`, обновлён `docs/roadmap.md` | ✅ |

---

## Задачи

| # | Задача | Статус | Модель | Plan | Summary |
|---|--------|--------|--------|------|---------|
| 01 | [threat-model](#задача-01-модель-угроз-и-карта-рисков-) | ✅ | Opus 5 High | [plan](tasks/01-threat-model/plan.md) | [summary](tasks/01-threat-model/summary.md) |
| 02 | [tooling-setup](#задача-02-установка-promptfoo-и-проверка-работоспособности-) | ✅ | Composer 2.5 | [plan](tasks/02-tooling-setup/plan.md) | [summary](tasks/02-tooling-setup/summary.md) |
| 03 | [plugin-selection](#задача-03-подбор-плагинов-стратегий-и-параметров-) | ✅ | Opus 5 High | [plan](tasks/03-plugin-selection/plan.md) | [summary](tasks/03-plugin-selection/summary.md) |
| 04 | [config-generation](#задача-04-генерация-конфигурации--отчёт-объяснение-) | ✅ | Sonnet 5 | [plan](tasks/04-config-generation/plan.md) | [summary](tasks/04-config-generation/summary.md) |
| 05 | [config-review](#задача-05-ревью-конфигурации-) | ✅ | Sonnet 5 | [plan](tasks/05-config-review/plan.md) | [summary](tasks/05-config-review/summary.md) |
| 06 | [tests-generation](#задача-06-генерация-тестовых-сценариев-) | ✅ | Composer 2.5 | [plan](tasks/06-tests-generation/plan.md) | [summary](tasks/06-tests-generation/summary.md) |
| 07 | [tests-review](#задача-07-ревью-сгенерированных-сценариев-) | ✅ | Sonnet 5 | [plan](tasks/07-tests-review/plan.md) | [summary](tasks/07-tests-review/summary.md) |
| 08 | [baseline-before-run](#задача-08-baseline-до-прогон-) | ✅ | Composer 2.5 | [plan](tasks/08-baseline-before-run/plan.md) | [summary](tasks/08-baseline-before-run/summary.md) |
| 09 | [baseline-before-triage](#задача-09-baseline-до-разбор-находок-) | ✅ | Opus 5 High | [plan](tasks/09-baseline-before-triage/plan.md) | [summary](tasks/09-baseline-before-triage/summary.md) |
| 10 | [fix-decisions](#задача-10-развилка-выбор-пути-фикса-) | ✅ | Opus 5 High | [plan](tasks/10-fix-decisions/plan.md) | [summary](tasks/10-fix-decisions/summary.md) |
| 11 | [fixes-implementation](#задача-11-реализация-фиксов-) | ✅ | Sonnet 5 | [plan](tasks/11-fixes-implementation/plan.md) | [summary](tasks/11-fixes-implementation/summary.md) |
| 12 | [baseline-after-run](#задача-12-baseline-после-прогон-и-сравнение-) | ✅ | Sonnet 5 | [plan](tasks/12-baseline-after-run/plan.md) | [summary](tasks/12-baseline-after-run/summary.md) |
| 13 | [final-report-roadmap](#задача-13-итоговый-отчёт-и-roadmap-) | ✅ | Opus 5 High | [plan](tasks/13-final-report-roadmap/plan.md) | [summary](tasks/13-final-report-roadmap/summary.md) |

> Все 13 планов согласованы в чате и готовы к исполнению. Правило двух согласований действует на каждой задаче: план → «ок» → реализация → самопроверка → «ок» → `summary.md`.

---

## Выбор модели-исполнителя

Стоимость прогонов Promptfoo в этом спринте и без того высокая, поэтому модель подбирается по цене ошибки, а не «на всякий случай самая мощная».

| Класс работы | Модель | Логика |
|---|---|---|
| Решения, которые распространяются на весь спринт | **Opus 5 High** | Ошибка в модели угроз, подборе плагинов, triage или выборе слоя фикса не локализуется — она проходит сквозь все следующие задачи и обнаруживается только на прогоне «после». Переделка стоит дороже разницы в цене модели |
| Работа по готовому плану с проверяемыми критериями | **Sonnet 5** | Генерация конфига, ревью артефактов, реализация фиксов, сравнение отчётов. Решения уже приняты, критерии в DoD измеримы, ошибка ловится чек-листом или тестом на этом же шаге |
| Механические операции и CLI | **Composer 2.5** | Установка Node.js и Promptfoo, запуск `redteam generate` / `redteam eval`, сбор манифеста. Успех определяется кодом возврата и наличием файлов; интеллектуальных развилок нет |

**Дополнительно:**

- Задача 11 — реализация фиксов: Sonnet 5 достаточно, пока идёт строго по `fix-decisions.md`. Если всплывает архитектурная развилка, которой в решениях нет, — остановиться и вернуться к Opus 5 High, а не импровизировать в коде.
- Задачи 05 и 07 — ревью: модель готовит структурированный разбор, но финальное «ок» всегда за человеком; экономия на этих шагах бессмысленна, потому что дальше конфиг замораживается.
- Задачи 06, 08, 12 в части запуска прогонов: цена определяется вызовами LLM внутри Promptfoo, а не моделью-агентом. Composer 2.5 на 08 и Sonnet 5 на 12 — потому что в 12 добавляется аналитика сравнения.

---

## Задача 01: Модель угроз и карта рисков ✅

### Цель

Получить письменную модель угроз агента и карту рисков с привязкой к OWASP LLM Top 10 / OWASP ASI Top 10 — основание для выбора плагинов в задаче 03.

**Боль предыдущего шага:** стартовое состояние — нет ни защиты, ни понимания, что защищаем.

> 📌 **Skills:** `grill-me` для стресс-теста модели угроз. Skill для threat modeling в роутере нет — явно фиксируем в plan.

**Артефакты:** `practice/redteam/threat-model.md`  
**Plan:** [tasks/01-threat-model/plan.md](tasks/01-threat-model/plan.md) · **Summary:** [tasks/01-threat-model/summary.md](tasks/01-threat-model/summary.md)  
**Модель:** Opus 5 High — фундамент всего спринта, ошибка здесь проходит сквозь все задачи

**Итог:** 16 рисков с парами OWASP LLM 2025 / ASI 2026. Уточнения, которые уходят в следующие задачи: таксономия LLM — издание **2025** (Promptfoo резолвит `owasp:llm:NN` в него); canary `LLMSTART-CANARY-7f3a91c2e5b04d68` — обёртка в `ReactRunner.__init__`, чтобы покрыть и путь `config_id`; `bola` / `bfla` — низкая применимость; 11 рисков в scope фиксов, 4 в backlog, 1 на регрессию.

---

## Задача 02: Установка Promptfoo и проверка работоспособности ✅

### Цель

Работающий Promptfoo с запиненной версией, установленные skills, живой таргет и smoke-прогон; canary-токен в системном промпте.

**Боль предыдущего шага:** есть карта рисков, но нет инструмента и измерителя утечки.

> 📌 **Skills:** установить `promptfoo-provider-setup`, `promptfoo-redteam-setup`, `promptfoo-redteam-run` из `skills.sh/promptfoo/promptfoo`; добавить в `40-skills-router.mdc`.

**Решения (согласовано):** Node.js `^20.20.0` / `>=22.22.0` — проверить и при необходимости поставить; OpenRouter — нативный провайдер + `OPENROUTER_API_KEY`; canary вне `SECURITY_ENABLED`.

**Артефакты:** `practice/redteam/tooling-setup.md`, `practice/redteam/smoke/`, `backend/app/agent/react_runner.py`, `.env.example`, роутер skills  
**Plan:** [tasks/02-tooling-setup/plan.md](tasks/02-tooling-setup/plan.md) · **Summary:** [tasks/02-tooling-setup/summary.md](tasks/02-tooling-setup/summary.md)  
**Модель:** Composer 2.5 — установка и smoke проверяются кодом возврата; при проблемах с окружением поднять до Sonnet 5

**Итог:** Promptfoo **0.122.0**, три skills в `.agents/skills/`, smoke 2/2 (`eval-MvX-2026-08-14T08:49:46`). Canary в `ReactRunner.__init__` через `SECURITY_CANARY_TOKEN`. Дополнительно: `run-smoke.ps1` (UTF-8), `scripts/uv.cmd` для Windows PATH.

---

## Задача 03: Подбор плагинов, стратегий и параметров ✅

### Цель

Таблица «риск → плагин → почему» и обоснованные параметры — **без** генерации конфига.

**Боль предыдущего шага:** инструмент работает, но без решения получим либо «всё включить», либо пропуск реальных рисков.

> 📌 **Skills:** `promptfoo-redteam-setup`, `grill-me`.

**Решения (согласовано):** язык атак — русский основной, английский дополнительный; многоходовые стратегии — решение по `stateful`/склейке истории зафиксировать в документе.

**Артефакты:** `practice/redteam/plugin-selection.md`, `plugin-selection-appendix.md`  
**Plan:** [tasks/03-plugin-selection/plan.md](tasks/03-plugin-selection/plan.md) · **Summary:** [tasks/03-plugin-selection/summary.md](tasks/03-plugin-selection/summary.md)  
**Модель:** Opus 5 High — определяет всю поверхность проверки; пропущенный риск не найдётся ни на одном прогоне

**Итог:** 14 записей плагинов (10 уникальных имён + 4 экземпляра `policy`), стратегии `basic` / `jailbreak-templates` / `jailbreak:meta`, бюджет ≈ $0,4–0,9 за прогон. Решения, которые уходят дальше: encoding-стратегии и `jailbreak:composite` исключены как ломающие детерминированный canary-ассерт; многоходовые исключены из-за `stateful: false` и лимита 4000 символов, crescendo — в backlog; `maxConcurrency: 2` из-за незаблокированной перезаписи `payments.json`; 5 плагинов набора **remote-only**, поэтому доступность API Promptfoo входит в run-manifest; `search_knowledge_base` признан признаком утечки промпта (уточнение внесено в `threat-model.md` §3); R-05 и R-11 — ручные кейсы.

---

## Задача 04: Генерация конфигурации + отчёт-объяснение ✅

### Цель

Сгенерировать (не руками) `promptfooconfig.yaml` и `config-explainer.md` по решениям задач 01–03.

**Боль предыдущего шага:** есть решение «чем бить», но нет исполняемой конфигурации.

> 📌 **Skills:** все три promptfoo-skills; приложить idea/vision/architecture + известные факты.

**Обязательное содержание конфига:**

- `targets` — HTTP на `POST /api/v1/chat`, без `session_id` и без `config_id`
- `transformResponse` — извлечение поля `message`
- `defaultTest` — детерминированные assert'ы: canary, имена инструментов, маркер `[SECURITY_BLOCKED]`
- `redteam.provider` — OpenRouter, reasoning выключен
- `purpose` — на русском: PROTECTED / DISCLOSABLE / платёжное правило
- `plugins` и `strategies` — **точно** из задачи 03
- policy-плагин — правило про поведение агента при подтверждении оплаты

Плюс `config-generation-prompt.md` — сохранённый промпт генерации как артефакт воспроизводимости.

**Артефакты:** `practice/redteam/promptfooconfig.yaml`, `practice/redteam/config-explainer.md`  
**Plan:** [tasks/04-config-generation/plan.md](tasks/04-config-generation/plan.md) · **Summary:** [tasks/04-config-generation/summary.md](tasks/04-config-generation/summary.md)  
**Модель:** Sonnet 5 — решения уже приняты в 03, работа структурная; ошибки ловит ревью задачи 05

**Итог:** конфиг + explainer + промпт генерации сгенерированы, синтаксис валиден. 14 записей плагинов, 3 стратегии — один в один из `plugin-selection.md`. Ключевое решение: маркер `[SECURITY_BLOCKED]` — информационный ассерт (`pass: true` всегда), не блокирующий, иначе baseline «до» проваливался бы по определению ещё до guard'а из задачи 11. Побочно (вне scope) исправлен шум `ERROR`-логов в `AgentConfigRegistry` на не-agent конфигах `evals/configs/multimodal-*.yaml`.

---

## Задача 05: Ревью конфигурации ✅

### Цель

Человеческий чек-лист: конфиг соответствует продукту и решениям задачи 03; все расхождения правит человек.

**Боль предыдущего шага:** сгенерированный конфиг может содержать выдуманные URL, инструменты или правила.

**Чек-лист:** реальный URL `:8003`; reasoning off; 8 имён инструментов; policy с `confirm_payment`; entities совпадают; стратегии в правильной форме; explainer ↔ yaml.

**Артефакты:** правки yaml/explainer; `practice/redteam/config-review-checklist.md` (заполненный)  
**Plan:** [tasks/05-config-review/plan.md](tasks/05-config-review/plan.md) · **Summary:** [tasks/05-config-review/summary.md](tasks/05-config-review/summary.md)  
**Модель:** Sonnet 5 — сверка по чек-листу; финальное «ок» всегда за человеком, дальше конфиг заморожен

**Итог:** 12/12 pass, yaml не менялся. Dry-run `eval-78X-2026-08-14T15:36:50` (2/2): грейдер видит plain `message`, агент вызвал `list_b2c_products`. SHA-256 `promptfooconfig.yaml`: `B8F37D1D01786531B9F56DB74948C70624FE30423D6A1B86760959ADB75EF2C7`. Задачи 06–12 конфиг не трогают.

---

## Задача 06: Генерация тестовых сценариев ✅

### Цель

`redteam-tests.yaml` через `promptfoo redteam generate` по проверенному конфигу.

**Боль предыдущего шага:** конфиг без сценариев не даёт baseline.

> 📌 **Skills:** `promptfoo-redteam-run`.

**Артефакты:** `practice/redteam/redteam-tests.yaml`, `practice/redteam/generate-log.txt`  
**Plan:** [tasks/06-tests-generation/plan.md](tasks/06-tests-generation/plan.md) · **Summary:** [tasks/06-tests-generation/summary.md](tasks/06-tests-generation/summary.md)  
**Модель:** Composer 2.5 — запуск CLI; качество сценариев определяет Promptfoo, а не модель-агент

**Итог:** 138 кейсов (RU-only), `redteam generate` (не `run`), 14/14 плагинов Success. После первой генерации 276 (RU+EN) — сокращение до одного языка по решению пользователя; правка `promptfooconfig.yaml` (`language: [Русский]`). SHA-256: конфиг `300F1360…D837`, tests `830B02F9…938B`. Оценка прогона ~$0,4 / ~10 мин. Дальше — задача 07 (ревью атак), затем заморозка до baseline «до».

---

## Задача 07: Ревью сгенерированных сценариев ✅

### Цель

Прочитать `redteam-tests.yaml` до боевого прогона; зафиксировать замечания и распределение языков.

**Боль предыдущего шага:** сгенерированные атаки могут быть мусорными или не на том языке.

**Артефакты:** `practice/redteam/test-review-notes.md`  
**Plan:** [tasks/07-tests-review/plan.md](tasks/07-tests-review/plan.md) · **Summary:** [tasks/07-tests-review/summary.md](tasks/07-tests-review/summary.md)  
**Модель:** Sonnet 5 — вычитка десятков русскоязычных сценариев по явным критериям; последняя точка перед заморозкой набора

**Итог:** 48 уникальных ядер прочитаны, 138/138 на русском. Решение **go**. 0 `block`, concern у extraction / P2–P4 / `excessive-agency` / override. P1 — поведение, не порядок tools. SHA-256 тестов без изменений: `830B02F9…938B`. Набор заморожен до конца спринта. Дальше — задача 08 (`redteam eval`, не `run`).

---

## Задача 08: Baseline «до» — прогон ✅

### Цель

`promptfoo redteam eval` против агента **как есть** (`SECURITY_ENABLED=false` или отсутствует); сохранить сырые результаты.

**Боль предыдущего шага:** без зафиксированного «до» нельзя доказать эффект фиксов.

**Артефакты:** `practice/redteam/baseline-before/` (отчёт, json, лог команды)  
**Plan:** [tasks/08-baseline-before-run/plan.md](tasks/08-baseline-before-run/plan.md) · **Summary:** [tasks/08-baseline-before-run/summary.md](tasks/08-baseline-before-run/summary.md)  
**Модель:** Composer 2.5 — прогон и сбор манифеста; стоимость определяется вызовами внутри Promptfoo

**Итог:** канон `eval-Eox-2026-08-14T18:00:18`, 138/138, 88 pass / 50 fail / 0 errors, ASR 36.23%, 42.63 мин. `SECURITY_ENABLED` отсутствует. Attempt 1 (`eval-YRW`) отброшен — Qdrant был down. SHA-256 без изменений: конфиг `300F1360…D837`, tests `830B02F9…938B`. `baseline-before/` заморожен. Дальше — задача 09 (triage).

---

## Задача 09: Baseline «до» — разбор находок ✅

### Цель

Triage-таблица: находка → категория OWASP → предполагаемый слой защиты; ≥1 строка на плагин или «не воспроизвелось».

**Боль предыдущего шага:** сырой отчёт не превращается в план работ сам.

**Артефакты:** `practice/redteam/triage-before.md`  
**Plan:** [tasks/09-baseline-before-triage/plan.md](tasks/09-baseline-before-triage/plan.md) · **Summary:** [tasks/09-baseline-before-triage/summary.md](tasks/09-baseline-before-triage/summary.md)  
**Модель:** Opus 5 High — отделить реальные находки от артефактов грейдера; ложный вывод здесь уводит фиксы не туда

**Итог:** 25 находок F-01…F-25. Грейдер завышает ASR (`tool-discovery` 80% — в основном ложные fail). Canary 0/138. Главное: ложная оплата + реальный `save_lead`, `HACKED:` 3/3, dump tools, дословный акцепт заказа, живой `config_id` → V2/V3. Дальше — задача 10 (слои без кода).

---

## Задача 10: Развилка — выбор пути фикса ✅

### Цель

Для каждой находки — решение **без кода**: слой защиты, обоснование «почему не соседний слой», наблюдаемый критерий успеха.

**Боль предыдущего шага:** triage без решения ведёт к хаотичным правкам в задаче 11. Плюс критерий успеха обязан выражаться через ассерты замороженного конфига — иначе прогон «после» не отличит фикс от случайности.

**Пять слоёв с реальными точками внедрения:** системный промпт (`prompts.py` + `react_runner.py`) · входной guard (`factory.py` / `routes/chat.py`) · выходной guard (`agent_service.py`, **оба** пути — JSON и SSE) · policy инструментов (`tool_adapter.py::_run_sync`) · конфигурация приложения (`schemas/chat.py`, `core/config.py`).

**Правило выбора:** всё, что даёт побочный эффект — платёж, лид, запрос в Neo4j — чинится в коде; промпт допустим только для тона и тематики. Отдельное решение по `config_id` с учётом eval-контура.

**Артефакты:** `practice/redteam/fix-decisions.md`  
**Plan:** [tasks/10-fix-decisions/plan.md](tasks/10-fix-decisions/plan.md) · **Summary:** [tasks/10-fix-decisions/summary.md](tasks/10-fix-decisions/summary.md)  
**Модель:** Opus 5 High — архитектурный выбор слоя защиты; переделка после реализации дороже разницы в цене модели

**Итог:** 5 пакетов FIX-1…FIX-5 на F-01…F-25. Побочные эффекты — policy, не промпт. `config_id` — внутренний заголовок `X-LLMStart-Eval-Key` (eval-скрипт шлёт ключ). Входной guard узкий. F-05 и хвост F-09 — partial. Defer D-01…D-12. Дальше — задача 11 строго по пакетам, без импровизации.

---

## Задача 11: Реализация фиксов ✅

### Цель

Код по `fix-decisions.md`; каждый фикс за флагом `SECURITY_ENABLED` (default: **true**).

**Боль предыдущего шага:** решения без реализации не меняют baseline «после». Но реализация «в лоб» ломает эксперимент: guard только в JSON-ветке даёт ложно-зелёный прогон при незащищённом веб-виджете; слишком жёсткий входной guard убивает легитимную воронку.

**Флаг — инструмент методологии:** при `SECURITY_ENABLED=false` поведение обязано совпадать с baseline «до». Это фиксируется отдельным тестом, а не проверкой на глаз.

**Ограничение архитектуры:** `SYSTEM_PROMPT_V1…V5` заморожены под воспроизводимость прошлых eval'ов — hardening оформляется новой `SYSTEM_PROMPT_V6`.

**Scope:** `backend/`, `mcp_server/`, `.env.example`, тесты — **не** трогаем `promptfooconfig.yaml`, `redteam-tests.yaml`, значение canary.

**Plan:** [tasks/11-fixes-implementation/plan.md](tasks/11-fixes-implementation/plan.md) · **Summary:** [tasks/11-fixes-implementation/summary.md](tasks/11-fixes-implementation/summary.md)  
**Модель:** Sonnet 5 — реализация строго по `fix-decisions.md` с тестами; при незапланированной архитектурной развилке остановиться и вернуться к Opus 5 High

**Итог:** FIX-1…FIX-5 за `SECURITY_ENABLED` (default `true`). Входной guard в `chat()`, выходной — JSON и SSE, policy в `_run_sync`, промпт V6, `config_id` только с `X-LLMStart-Eval-Key`. Yaml и canary не трогаты. Коммит — пользователь. Дальше — задача 12 (`redteam eval`, не `run`).

---

## Задача 12: Baseline «после» — прогон и сравнение ✅

### Цель

Повторный `redteam eval` на **тех же** сценариях с `SECURITY_ENABLED=true`; доказать, что разница объясняется фиксами, а не изменившимися условиями.

**Боль предыдущего шага:** unit-тест проверяет то, что придумали мы; red team — то, что придумала модель-атакующий. Без повторного прогона эффект фиксов остаётся предположением.

**Две ловушки, закрытые в плане:**

- **Ложно-зелёный прогон** — pass rate 100% достигается блокировкой всего подряд. Поэтому меряется ещё и доля ответов с `[SECURITY_BLOCKED]` плюс ручной проход воронки B2C.
- **Шум вместо сигнала** — грейдер недетерминирован; порог значимости delta фиксируется **до** прогона.

Плюс ручные кейсы, которых нет в автоматическом наборе: гейт `config_id` и живая воронка — оба с транскриптами.

**Артефакты:** `practice/redteam/baseline-after/` (+ `run-manifest.md`), `practice/redteam/comparison.md`  
**Plan:** [tasks/12-baseline-after-run/plan.md](tasks/12-baseline-after-run/plan.md) · **Summary:** [tasks/12-baseline-after-run/summary.md](tasks/12-baseline-after-run/summary.md)  
**Модель:** Sonnet 5 — прогон механический, но сравнение и трактовка delta требуют аккуратной аналитики

**Итог:** канон `eval-hvm-2026-08-15T16:28:29`, 138/138, 113 pass / 25 fail / 0 errors, ASR 18.12% (было 36.23%). Маркер 7/138. Closed 13 / partial 4 / open 7. Yaml и canary без изменений. После eval — hotfix denylist URL (без повторного eval). Дальше — задача 13.

---

## Задача 13: Итоговый отчёт и roadmap ✅

### Цель

Превратить артефакты в передаваемое знание и переиспользуемый регрессионный контур, затем закрыть спринт.

**Боль предыдущего шага:** к этому моменту `practice/redteam/` — склад из десятка файлов. Через два месяца мы сами не вспомним, почему `bola` исключён и почему canary живёт в рантайм-обёртке.

**Шесть разделов отчёта:** сводка находок → индекс артефактов → антипаттерны из опыта спринта → чего baseline **не** покрывает → как повторить прогон (команда, pin, хеши) → метрики спринта.

Замороженный конфиг и набор кейсов — готовый регрессионный харнесс для sprint-12; раздел «как повторить» существует именно для этого.

**Артефакты:** `practice/redteam/final-report.md`, обновлённый `docs/roadmap.md`, статус спринта ✅  
**Plan:** [tasks/13-final-report-roadmap/plan.md](tasks/13-final-report-roadmap/plan.md) · **Summary:** [tasks/13-final-report-roadmap/summary.md](tasks/13-final-report-roadmap/summary.md)  
**Модель:** Opus 5 High — синтез всего спринта и честные границы baseline; главный артефакт передачи знания

**Итог:** шесть разделов в `final-report.md`; backlog D-01…D-12 и open/partial влиты в TBD v0.3/v1.0 без дубликатов; roadmap sprint-11 → ✅; DoD спринта 11/11. Спринт закрыт.

---

## Итог

Sprint-11 закрыт как воспроизводимый security-baseline: модель угроз → Promptfoo 0.122.0 → 138 RU-кейсов → baseline «до» (ASR 36.23%) → FIX-1…FIX-5 за `SECURITY_ENABLED` → baseline «после» (ASR 18.12%, closed 13 / partial 4 / open 7). Харнесс заморожен (SHA-256 конфига/тестов в `final-report.md` §5). Open/partial и defer — в roadmap v0.3/v1.0, не под ковёр. Главный артефакт передачи: [practice/redteam/final-report.md](../../../practice/redteam/final-report.md).
