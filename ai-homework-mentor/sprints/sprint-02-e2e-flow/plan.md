# Sprint 02: e2e-flow

> **Версия roadmap:** v0.1
> **Roadmap:** [../../roadmap.md](../../roadmap.md)
> **Статус:** ✅ Done
> **Открыт:** 2026-07-17
> **Закрыт:** 2026-07-17

---

## Цель спринта

Закрыть сквозной сценарий проверки в одном агенте: принять вход → получить код → построить наблюдаемый план → проверить по дефолтной рубрике → вывести actionable Feedback в compact-режиме.

**Боль, которую закрывает:** после Sprint 01 есть только скелет и health-check. Нет никакой реальной проверки. Sprint 02 делает продукт работающим end-to-end.

**Deep-agent механизм:** планирование через `write_todos` (наблюдаемый план) + файловая система как рабочая память (`workspace/`). Оркестратор ведёт todo-список и пишет все артефакты в файлы — в окне только ссылки.

---

## Навыки

Перед началом прочитать:
- `.agents/skills/deep-agents-core/SKILL.md` — `create_deep_agent`, tools, filesystem backend
- `.agents/skills/deep-agents-orchestration/SKILL.md` — планирование, `write_todos`, управление состоянием
- `.agents/skills/langchain-fundamentals/SKILL.md` — инструменты, tool-calling loop
- `.agents/skills/python-design-patterns/SKILL.md` — SoC: парсинг / retrieval / агент / рендеринг — отдельно

### Актуализация относительно Sprint 01

| Пункт плана | Было | Стало |
|-------------|------|-------|
| CLI-сигнатура | `parse_input(raw: str)` — один аргумент | `mentor check <source> [topic]` — source и topic раздельно; `parse_input(source, topic)` |
| LLM-провайдер | не указано | `langchain-openrouter` + модель `openrouter:{model}` из конфига |
| Рубрика в workspace | не указано | копировать `config/rubrics/default.yaml` → `workspace/rubric.md` до запуска агента |
| Sprint 01 CLI | один positional `input_path` | расширить до двух positional: source + optional topic |

---

## DoD спринта

Sprint считается завершённым, когда:

| # | Критерий | Способ проверки |
|---|----------|-----------------|
| 1 | `mentor check ./dir/ "тема"` — агент строит план и выводит статусы шагов | запустить на любой локальной директории с кодом |
| 2 | `mentor check <github-url> "тема"` — агент клонирует репо и проверяет | запустить с публичным GitHub-репо |
| 3 | В `workspace/` создаются все ожидаемые файлы | проверить наличие `submission.md`, `code-index.md`, `plan.md`, `notes/`, `feedback.md` |
| 4 | Compact-вывод содержит: «Хорошо», «Обязательно исправить», Fix Plan | прочитать вывод в терминале |
| 5 | При отсутствии темы — агент завершается с понятным сообщением (уточнение — Sprint 06) | передать вход без темы |
| 6 | `make lint && make typecheck` → exit 0 | `make ci` |
| 7 | Есть smoke-тест на парсинг входа | `make test` → exit 0 |

---

## Задачи

| # | Задача | Статус | Plan | Summary |
|---|--------|--------|------|---------|
| 01 | `input-parser` — разобрать вход: URL или путь, тема задания | ✅ | [plan](tasks/01-input-parser/plan.md) | [summary](./summary.md) |
| 02 | `code-retrieval` — получить код в `workspace/code/` | ✅ | [plan](tasks/02-code-retrieval/plan.md) | [summary](./summary.md) |
| 03 | `orchestrator-e2e` — полный агент: план → рубрика → проверка → синтез + compact-вывод | ✅ | [plan](tasks/03-orchestrator-e2e/plan.md) | [summary](./summary.md) |

---

## Задача 01: input-parser 📋

### Цель

Разобрать CLI-вход (`input: str`): определить тип (GitHub URL или локальный путь), извлечь тему задания, записать в `workspace/submission.md`.

> 💡 **Скиллы:** `python-design-patterns/SKILL.md` — чистый модуль без side-effects, только парсинг и возврат dataclass.

### Состав работ

- [x] Реализовать `mentor/parser.py`: функция `parse_input(source: str, topic: str | None = None) -> Submission`
- [x] `Submission` — dataclass: `source_type: Literal["github", "local"]`, `source: str`, `topic: str | None`
- [x] Определить GitHub URL: `re`-паттерн для `github.com/<user>/<repo>`
- [x] Определить локальный путь: `pathlib.Path(source).exists()`
- [x] Если тип не определён — `raise ValueError` с понятным сообщением
- [x] Записать результат в `workspace/submission.md` (Markdown с полями)
- [x] Написать unit-тесты: GitHub URL, локальный путь, невалидный вход
- [x] Самопроверка: `make lint && make typecheck && make test`

### Критерии готовности (DoD)

**Агент проверяет:**

| # | Критерий | Способ проверки |
|---|----------|-----------------|
| 1 | GitHub URL распознаётся корректно | unit-тест |
| 2 | Локальный путь распознаётся корректно | unit-тест |
| 3 | Невалидный вход → `ValueError` с текстом | unit-тест |
| 4 | Линтер и типы чистые | `make ci` |

**Пользователь проверяет:**

- `workspace/submission.md` после парсинга содержит читаемые поля

### Артефакты

- `mentor/parser.py`
- `tests/test_parser.py`

---

## Задача 02: code-retrieval 📋

### Цель

Получить код студента в `workspace/code/`: клонировать публичный GitHub-репо или скопировать локальную директорию; построить `workspace/code-index.md` с деревом файлов.

> 💡 **Скиллы:** `sharp-edges/SKILL.md` — `git clone` без исполнения кода; timeout; обработка сетевых ошибок.

### Состав работ

- [x] Реализовать `mentor/retrieval.py`: функция `retrieve_code(submission: Submission, workspace: Path) -> Path`
- [x] Ветка GitHub: `subprocess.run(["git", "clone", "--depth=1", url, target], timeout=60)` — код не исполняется, только клонирование
- [x] Ветка локального пути: рекурсивное копирование через `shutil.copytree` в `workspace/code/`
- [x] Фильтрация: пропускать `.git/`, `node_modules/`, `__pycache__/`, бинарные файлы
- [x] Построить `workspace/code-index.md`: дерево файлов + количество строк + общий размер
- [x] Обработка ошибок: репо не найден, нет прав доступа, timeout → понятное сообщение
- [x] Самопроверка: `make lint && make typecheck`

### Критерии готовности (DoD)

**Агент проверяет:**

| # | Критерий | Способ проверки |
|---|----------|-----------------|
| 1 | Локальная директория копируется в `workspace/code/` | запустить с тестовой директорией |
| 2 | `workspace/code-index.md` создаётся с деревом файлов | проверить файл после запуска |
| 3 | Бинарные файлы и `.git/` отфильтрованы | проверить содержимое `workspace/code/` |
| 4 | Линтер и типы чистые | `make ci` |

**Пользователь проверяет:**

- `code-index.md` читается и даёт понятное представление о структуре проекта

### Артефакты

- `mentor/retrieval.py`
- `workspace/code/` (артефакт выполнения)
- `workspace/code-index.md` (артефакт выполнения)

---

## Задача 03: orchestrator-e2e 📋

### Цель

Реализовать полный Orchestrator-агент на `deepagents`: план (todo) → чтение рубрики → последовательная проверка по аспектам → синтез `feedback.md` + `fix_plan.md` → compact-вывод через Rich CLI.

> 💡 **Скиллы:** `deep-agents-core/SKILL.md`, `deep-agents-orchestration/SKILL.md` — `create_deep_agent`, `write_todos`, filesystem backend, tool-calling loop.

### Состав работ

- [x] Реализовать `mentor/agent.py`: функция `run_orchestrator(submission, workspace, config) -> Path`
- [x] Создать агента через `create_deep_agent(model=..., tools=[...], system_prompt=...)`
- [x] System prompt загружается из `config/prompts/orchestrator-system.yaml`
- [x] Заполнить `config/prompts/orchestrator-system.yaml` — инструкция: разобрать submission, построить план через `write_todos`, читать рубрику, проверять аспекты последовательно, писать ноты в `workspace/notes/`, синтезировать `feedback.md` и `fix_plan.md`
- [x] Заполнить `config/rubrics/default.yaml` — универсальная рубрика: структура проекта, качество кода, обработка ошибок, документация
- [x] Настроить filesystem backend deepagents на `workspace/`
- [x] Реализовать compact-рендеринг в `mentor/cli.py`: стримить события deepagents, показывать статус шагов плана, в конце — Rich-панель с Feedback + Fix Plan
- [x] Обработка ошибок: timeout LLM, пустой ответ, файловые ошибки → понятные сообщения
- [x] Самопроверка: `make lint && make typecheck`

### Критерии готовности (DoD)

**Агент проверяет:**

| # | Критерий | Способ проверки |
|---|----------|-----------------|
| 1 | `mentor check ./dir/ "тема"` завершается без ошибок | запустить на локальной директории |
| 2 | `workspace/plan.md` создан с todo-списком | проверить файл |
| 3 | `workspace/notes/` содержит ноты по аспектам рубрики | проверить файлы |
| 4 | `workspace/feedback.md` и `workspace/fix_plan.md` созданы | проверить файлы |
| 5 | Compact-вывод содержит секции «Хорошо», «Исправить», Fix Plan | прочитать терминал |
| 6 | Линтер и типы чистые | `make ci` |

**Пользователь проверяет:**

- Feedback содержит конкретные, адресные замечания (не generic)
- Fix Plan приоритизирован (Высокий / Средний / Низкий)
- Вывод в терминале читается без дополнительных инструкций

### Артефакты

- `mentor/agent.py` (реализован)
- `mentor/cli.py` (compact-рендеринг добавлен)
- `mentor/config/prompts/orchestrator-system.yaml` (заполнен)
- `mentor/config/rubrics/default.yaml` (заполнен)
- `workspace/plan.md`, `workspace/notes/`, `workspace/feedback.md`, `workspace/fix_plan.md` (артефакты выполнения)

### Демонстрация через Rich CLI (compact-режим)

По завершении Sprint 02 пользователь видит:

```
$ mentor check ./student-project/ "Задание: REST API на FastAPI"

╭─ AI Homework Mentor v0.1.0 ───────────────────────────────────────────╮
│  Модель: google/gemini-2.5-flash  │  Режим: compact                   │
╰───────────────────────────────────────────────────────────────────────╯

✓ OpenRouter: соединение установлено
📋 Тема:    REST API (FastAPI)
📁 Код:     ./student-project/ (14 файлов, ~2 400 строк)

  ✓ [1/4] Читаю структуру кода
  ✓ [2/4] Структура проекта
  ✓ [3/4] Качество кода
  ✓ [4/4] Синтез результатов

╭─ Feedback ────────────────────────────────────────────────────────────╮
│                                                                        │
│  ✅  Хорошо                                                            │
│  • Чёткая структура роутеров, Pydantic-модели для валидации           │
│                                                                        │
│  ⚠️   Обязательно исправить                                            │
│  1.  Нет обработки ошибок в роутерах                                  │
│  2.  Секреты захардкожены в main.py                                    │
│  3.  Нет тестов                                                        │
│                                                                        │
│  📋  Fix Plan                                                          │
│  [Высокий]  Добавить глобальный exception handler                     │
│  [Высокий]  Вынести DATABASE_URL и ключи в .env                       │
│  [Средний]  Написать smoke-тесты для роутеров                         │
│                                                                        │
╰───────────────────────────────────────────────────────────────────────╯
```

---

## Итог (заполняется после закрытия)

E2E-сценарий v0.1 работает: парсинг входа, получение кода, orchestrator с `write_todos`, артефакты в workspace, Feedback в compact/verbose. Все 7 критериев DoD пройдены.

**Summary:** [summary.md](./summary.md)
