# Sprint 06: rubrics-skills

> **Версия roadmap:** v0.4
> **Roadmap:** [../../roadmap.md](../../roadmap.md)
> **Статус:** ✅ Done
> **Открыт:** 2026-07-24
> **Закрыт:** 2026-07-24

---

## Цель спринта

Адаптировать проверку под тему задания: тематические рубрики для FastAPI и Python CLI, интеграция публичных навыков `fastapi-templates` и `modern-python` как экспертного контекста для субагентов, human-in-the-loop при неопределённой теме.

**Боль, которую закрывает:** после Sprint 05 все механики CE работают, но рубрика одна — `default.yaml`. FastAPI-сервис и CLI-утилита проверяются по одному списку вопросов без учёта специфики. Это снижает релевантность фидбэка.

**Deep-agent механизм:** навыки (skills) — переиспользуемые процедуры проверки. Рубрика описывает «что проверяем»; навык из `.agents/skills/` — «чем проверяем», добавляя в бриф субагенту конкретный экспертный контекст. Human-in-the-loop — deepagents interrupt для уточнения темы.

---

## Навыки

Перед началом прочитать:
- `.agents/skills/fastapi-templates/SKILL.md` — критерии качества FastAPI-сервисов (для содержания рубрики)
- `.agents/skills/modern-python/SKILL.md` — критерии качества Python-кода (для содержания рубрики)
- `.agents/skills/langgraph-human-in-the-loop/SKILL.md` — deepagents interrupt для паузы и ожидания ответа
- `.agents/skills/python-design-patterns/SKILL.md` — паттерн стратегии для выбора рубрики

---

## DoD спринта

Sprint считается завершённым, когда:

| # | Критерий | Способ проверки |
|---|----------|-----------------|
| 1 | Тема «FastAPI» активирует рубрику `fastapi-service.yaml`, тема «CLI» — `python-cli.yaml` | запустить с явным указанием темы, проверить `workspace/rubric.md` |
| 2 | Бриф субагента содержит контент из подключённого навыка | прочитать `workspace/briefs/brief-<aspect>.md` |
| 3 | Без темы агент задаёт один уточняющий вопрос, ждёт ответа и продолжает | запустить без темы, ответить на вопрос |
| 4 | Verbose-режим показывает, какие навыки подключились и к каким аспектам | запустить `--verbose` |
| 5 | Качество Feedback для FastAPI-работы заметно выросло по сравнению с `default.yaml` | сравнить feedback на одном репо |
| 6 | `make ci` → exit 0 | `make ci` |
| 7 | Аспект `documentation` в рубриках явно ссылается на `code/README.md`, не на корень workspace | прочитать `fastapi-service.yaml`, `python-cli.yaml` |

---

## Задачи

| # | Задача | Статус | Plan | Summary |
|---|--------|--------|------|---------|
| 01 | `thematic-rubrics` — рубрики FastAPI и Python CLI; детектор темы; селектор рубрики | ✅ | [plan](tasks/01-thematic-rubrics/plan.md) | [summary](./summary.md) |
| 02 | `skills-integration` — skill resolver; встраивание контента навыка в бриф субагента; verbose-панели | ✅ | [plan](tasks/02-skills-integration/plan.md) | [summary](./summary.md) |
| 03 | `human-in-the-loop` — deepagents interrupt при неопределённой теме; verbose показывает паузу и вопрос | ✅ | [plan](tasks/03-human-in-the-loop/plan.md) | [summary](./summary.md) |

---

## Задача 01: thematic-rubrics 📋

### Цель

Создать рубрики `fastapi-service.yaml` и `python-cli.yaml`; реализовать детектор темы по входному тексту и code-index; реализовать селектор рубрики с fallback на `default.yaml`.

> 💡 **Скиллы:** `fastapi-templates/SKILL.md` и `modern-python/SKILL.md` — прочитать перед заполнением рубрик, чтобы аспекты были экспертными, не generic.

### Состав работ

- [ ] Прочитать `fastapi-templates/SKILL.md` и `modern-python/SKILL.md` перед заполнением рубрик
- [ ] Заполнить `config/rubrics/fastapi-service.yaml`: аспекты (api-design, code-quality, error-handling, testing, security), для каждого — `skill` (ссылка на навык или `null`) и `prompt` (ссылка на YAML-промпт)
- [ ] Заполнить `config/rubrics/python-cli.yaml`: аспекты (cli-design, code-quality, error-handling, testing), для каждого — `skill` и `prompt`
- [ ] Реализовать `mentor/rubric.py`: функция `detect_topic(submission: Submission, code_index: str) -> str | None` — ищет сигналы в тексте задания и `code-index.md` (импорты fastapi, наличие `typer`, `click`, `argparse`)
- [ ] Реализовать `mentor/rubric.py`: функция `select_rubric(topic: str | None) -> Path` — маппинг темы на файл рубрики; `None` → `default.yaml`
- [ ] Обновить оркестратор: вызвать `detect_topic → select_rubric` и записать выбранную рубрику в `workspace/rubric.md`
- [ ] Написать unit-тесты: детектор темы на различных входах
- [ ] Самопроверка: `make lint && make typecheck && make test`

### Критерии готовности (DoD)

**Агент проверяет:**

| # | Критерий | Способ проверки |
|---|----------|-----------------|
| 1 | `detect_topic` корректно определяет FastAPI и Python CLI | unit-тест с mock code-index |
| 2 | `select_rubric(None)` возвращает `default.yaml` | unit-тест |
| 3 | `workspace/rubric.md` создаётся с именем рубрики и списком аспектов | запустить и проверить файл |
| 4 | Линтер и типы чистые | `make ci` |

**Пользователь проверяет:**

- Рубрика `fastapi-service.yaml` содержит экспертные аспекты, специфичные для FastAPI (не generic)
- Аспекты рубрики осмысленны и покрывают реальные ошибки студентов

### Артефакты

- `mentor/rubric.py`
- `mentor/config/rubrics/fastapi-service.yaml` (заполнен)
- `mentor/config/rubrics/python-cli.yaml` (заполнен)
- `tests/test_rubric.py`

---

## Задача 02: skills-integration 📋

### Цель

Реализовать skill resolver — загружает контент навыка из `.agents/skills/<name>/SKILL.md` и встраивает его в бриф субагента как экспертный контекст; verbose показывает панель подключённых навыков.

> 💡 **Скиллы:** `python-design-patterns/SKILL.md` — паттерн стратегии: бриф строится по-разному в зависимости от наличия навыка.

### Состав работ

- [ ] Реализовать `mentor/skills.py`: функция `resolve_skill(skill_name: str | None) -> str | None` — читает `.agents/skills/<name>/SKILL.md`, возвращает содержимое или `None` если навык не найден
- [ ] Обновить `mentor/brief.py`: функция `build_brief` принимает `skill_content: str | None`; если навык есть — добавляет секцию `## Экспертный контекст (навык: <name>)` с содержимым навыка
- [ ] Добавить `SkillEvent(aspect, skill_name, skill_found: bool)` в `mentor/events.py`
- [ ] Обновить `mentor/tracker.py`: эмитировать `SkillEvent` при построении каждого брифа
- [ ] Добавить в `VerboseRenderer` метод `on_skill(event: SkillEvent)`:
  ```
  📚 Навык: fastapi-templates → подключён к аспекту "api-design"
  📚 Навык: modern-python → подключён к аспекту "code-quality"
  ```
- [ ] Добавить в verbose итоговую секцию «Навыки сессии»: список аспектов с подключёнными навыками
- [ ] Самопроверка: `make lint && make typecheck`

### Критерии готовности (DoD)

**Агент проверяет:**

| # | Критерий | Способ проверки |
|---|----------|-----------------|
| 1 | `workspace/briefs/brief-api-design.md` содержит секцию с контентом `fastapi-templates` | прочитать файл |
| 2 | При отсутствующем навыке бриф строится без ошибок (fallback) | передать несуществующее имя навыка |
| 3 | `SkillEvent` эмитируется для каждого аспекта | unit-тест с mock |
| 4 | Линтер и типы чистые | `make ci` |

**Пользователь проверяет:**

- Бриф субагента с навыком содержит конкретные критерии (из SKILL.md), не generic вопросы
- Verbose-вывод показывает, какой навык к чему подключился

### Артефакты

- `mentor/skills.py`
- `mentor/brief.py` (обновлён)
- `mentor/events.py` (дополнен `SkillEvent`)
- `mentor/tracker.py` (дополнен)
- `mentor/renderer.py` (дополнен `on_skill`, секция «Навыки сессии»)

---

## Задача 03: human-in-the-loop 📋

### Цель

Реализовать паузу оркестратора при неопределённой теме через deepagents interrupt: агент задаёт один уточняющий вопрос, CLI показывает его пользователю, ждёт ответа и продолжает с уточнённой темой.

> 💡 **Скиллы:** `langgraph-human-in-the-loop/SKILL.md` — паттерн `interrupt_on` в `create_deep_agent`; формат ответа пользователя.

### Состав работ

- [ ] Настроить `interrupt_on` в `create_deep_agent` оркестратора: пауза, когда агент вызывает tool `ask_user(question)`
- [ ] Реализовать tool `ask_user(question: str) -> str` — при вызове эмитирует `UserQuestionEvent(question)` и блокирует выполнение до получения ответа
- [ ] Добавить `UserQuestionEvent(question: str)` в `mentor/events.py`
- [ ] Добавить в `VerboseRenderer` и compact-renderer метод `on_user_question(event)`: вывести вопрос в панели, прочитать ответ из stdin через `typer.prompt`
- [ ] Обновить system prompt оркестратора: вызывать `ask_user` только если тема не определена детектором и не указана явно в CLI; один вопрос, не серия
- [ ] Обновить compact-вывод: при human-in-the-loop показать вопрос и ждать ответа (без подавления)
- [ ] Самопроверка: `make lint && make typecheck`

### Критерии готовности (DoD)

**Агент проверяет:**

| # | Критерий | Способ проверки |
|---|----------|-----------------|
| 1 | Без темы агент задаёт ровно один вопрос | запустить без темы, убедиться что вопрос один |
| 2 | После ответа агент продолжает с правильной рубрикой | ответить «FastAPI», проверить `workspace/rubric.md` |
| 3 | С явной темой в CLI вопрос не задаётся | передать тему в аргументе, убедиться нет вопроса |
| 4 | Линтер и типы чистые | `make ci` |

**Пользователь проверяет:**

- Вопрос понятен и требует ответа одним словом или фразой
- После ответа проверка продолжается без перезапуска

### Артефакты

- `mentor/events.py` (дополнен `UserQuestionEvent`)
- `mentor/agent.py` (дополнен `interrupt_on`, tool `ask_user`)
- `mentor/renderer.py` (дополнен `on_user_question`)
- `mentor/config/prompts/orchestrator-system.yaml` (обновлён)

### Демонстрация через Rich CLI (verbose-режим)

По завершении Sprint 06 пользователь видит два сценария:

**Сценарий А — тема определена автоматически:**
```
$ mentor check ./fastapi-project/ "Задание: REST API" --verbose

  📋 Тема: FastAPI (определена автоматически)
  📖 Рубрика: fastapi-service.yaml  (5 аспектов)

  📚 Навык: fastapi-templates → подключён к аспекту "api-design"
  📚 Навык: modern-python    → подключён к аспекту "code-quality"
  📚 Навык: —                → аспект "testing" (собственный промпт)
```

**Сценарий Б — тема не определена, human-in-the-loop:**
```
$ mentor check ./mystery-project/ --verbose

  ⚠  Тема задания не определена автоматически.

╭─ Уточняющий вопрос ──────────────────────────────────────────────────╮
│  Это FastAPI-сервис, CLI-утилита или другой тип Python-проекта?      │
╰──────────────────────────────────────────────────────────────────────╯
  Ваш ответ: FastAPI-сервис

  📖 Рубрика: fastapi-service.yaml  (5 аспектов)
  [... продолжение как в сценарии А ...]
```

---

## Итог (заполняется после закрытия)

Sprint 06 закрыт 2026-07-24. Тематические рубрики FastAPI/CLI, интеграция skills в брифы, HITL при неопределённой теме. Dogfooding на `./`, внешнем FastAPI-репо и HITL-stub. Подробности: [summary.md](./summary.md).
