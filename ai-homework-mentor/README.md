# AI Homework Mentor

Агент-ревьюер домашних заданий на базе [deepagents](https://github.com/langchain-ai/deepagents): принимает код студента, выбирает тематическую рубрику, проверяет через изолированных Reviewer-субагентов и возвращает actionable фидбэк.

## Требования

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) — зависимости и CLI
- Git — для проверки GitHub-репозиториев (`git clone`)
- Ключ [OpenRouter](https://openrouter.ai/keys) — LLM-вызовы
- *(опционально)* экспертные навыки в `~/.agents/skills/` — `modern-python`, `fastapi-templates` (см. [Skills](#skills))

## Быстрый старт

```bash
git clone <repo-url>
cd ai-homework-mentor/
cp .env.example .env          # заполнить OPENROUTER_API_KEY
make dev                      # uv sync + установка CLI в PATH
mentor check . "CLI-утилита на Python" --compact
```

Проверка занимает 1–3 минуты (вызовы LLM через OpenRouter). При преждевременной остановке агента CLI автоматически повторяет попытку — в терминале появится `↻ Повтор N/M` (лимит задаётся `AGENT_MAX_ATTEMPTS` в `.env`).

Если `mentor` не найден после `make dev`:

- перезапустите терминал (нужен `~/.local/bin` в PATH), или
- `uv run mentor check . "тема" --compact`, или
- `.\mentor.cmd check . "тема" --compact` (Windows, без глобальной установки)

## CLI

```bash
# Локальная директория + явная тема
mentor check ./student-project/ "REST API на FastAPI"

# Компактный вывод: шаги плана + итоговый Feedback
mentor check ./student-project/ "CLI-утилита на Python" --compact

# Подробный вывод: план, субагенты, CE, навыки, контекст + путь к workspace
mentor check ./student-project/ "CLI-утилита на Python" --verbose

# GitHub-репозиторий
mentor check https://github.com/user/repo "тема задания" --compact

# Без темы — автоопределение или один уточняющий вопрос (HITL)
mentor check ./student-project/ --verbose

# Dogfooding — проверка самого продукта (auto: Python CLI)
mentor check . --verbose

# Справка
mentor check --help
```

### Режимы вывода

| Флаг | Что показывает |
|------|----------------|
| `--compact` | Прогресс todo + итоговая панель Feedback |
| `--verbose` | План, субагенты, рост контекста, CE-события, навыки, HITL, путь к workspace |

По умолчанию — значение `OUTPUT_MODE` из `.env` / `config.yaml`.

### Артефакты проверки

Пишутся во временный `workspace/` (путь в стартовой панели):

| Путь | Назначение |
|------|------------|
| `submission.md` | Источник и тема |
| `code/` | Код студента (read-only для агента) |
| `code-index.md` | Дерево файлов и статистика |
| `rubric.md` | Выбранная рубрика |
| `briefs/brief-<aspect>.md` | Брифы для Reviewer-субагентов |
| `plan.md` | План проверки |
| `notes/review-<aspect>.md` | ReviewNote по аспектам |
| `feedback.md` | Итоговый фидбэк |
| `fix_plan.md` | Приоритизированный план исправлений |

Примеры после dogfooding: [docs/example-feedback.md](docs/example-feedback.md), [docs/example-fix-plan.md](docs/example-fix-plan.md).

## Тема и рубрики

| Сценарий | Поведение |
|----------|-----------|
| Тема в CLI (`"REST API на FastAPI"`) | Рубрика по теме, HITL не вызывается |
| Тема не указана, сигналы в коде | Авто: FastAPI (импорты `fastapi`/`uvicorn`) или Python CLI (`typer`/`click`/`argparse`) |
| Тема не указана, сигналов нет | Старт с `default.yaml` → **один** вопрос пользователю → рубрика обновляется без перезапуска |

| Рубрика | Когда | Аспектов |
|---------|-------|----------|
| `fastapi-service.yaml` | FastAPI / REST API | 6 (api-design, code-quality, error-handling, testing, security, documentation) |
| `python-cli.yaml` | CLI-утилита | 5 (cli-design, code-quality, error-handling, testing, documentation) |
| `default.yaml` | Неизвестный тип / до ответа HITL | 4 (structure, code-quality, error-handling, documentation) |

Документация студента всегда ищется в `code/README.md`, не в корне workspace.

## Skills

К аспектам рубрики могут подключаться экспертные навыки — их содержимое попадает в бриф субагента (секция «Экспертный контекст»).

| Аспект | Навык |
|--------|-------|
| api-design (FastAPI) | `fastapi-templates` |
| code-quality | `modern-python` |

Поиск навыков (первый найденный):

1. `<repo>/.agents/skills/<name>/SKILL.md`
2. `~/.agents/skills/<name>/SKILL.md`
3. `~/.codex/skills/<name>/SKILL.md`

Если навык не найден — бриф строится по критериям рубрики без ошибки. В `--verbose` видно, что подключилось: `📚 Навык: modern-python → подключён к аспекту "code-quality"`.

## Что происходит под капотом

| Механизм | Что делает |
|----------|------------|
| **План (todo)** | Оркестратор: подготовка plan → один шаг на аспект → синтез feedback |
| **Субагенты** | `spawn_reviewer` — Reviewer с чистым контекстом; результат в `notes/review-*.md` |
| **Context Engineering** | Вынос объёмных данных в файлы; суммаризация и компактизация истории |
| **Skills** | Экспертный контекст из SKILL.md в брифах субагентов |
| **Human-in-the-loop** | `ask_user` + `interrupt_on`: один вопрос, если тема не определена |

Подробнее: [roadmap.md](roadmap.md), [concept/architecture.md](concept/architecture.md).

## Конфигурация

| Источник | Назначение |
|----------|------------|
| `.env` | Секреты и переопределения (`OPENROUTER_API_KEY`, `MODEL`, лимиты) |
| `mentor/config/config.yaml` | Дефолты: модель, `context_limit`, пороги CE |
| `mentor/config/rubrics/*.yaml` | Тематические рубрики |
| `mentor/config/prompts/*.yaml` | System prompts оркестратора и ревьюера |

Ключевые переменные `.env` (полный список — [.env.example](.env.example)):

| Переменная | Описание |
|------------|----------|
| `OPENROUTER_API_KEY` | API-ключ OpenRouter (**обязателен**) |
| `MODEL` | Модель LLM, напр. `google/gemini-2.5-flash` |
| `CONTEXT_LIMIT` | Лимит контекста в токенах |
| `SUMMARIZATION_THRESHOLD` | Порог суммаризации истории |
| `AGENT_RECURSION_LIMIT` | Лимит шагов LangGraph |
| `AGENT_MAX_ATTEMPTS` | Повторы при ранней остановке агента |
| `LLM_REQUEST_TIMEOUT` | Таймаут одного LLM-запроса, сек |
| `OUTPUT_MODE` | `verbose` или `compact` по умолчанию |

## Make

| Команда | Описание |
|---------|----------|
| `make dev` | `uv sync` + установка CLI |
| `make lint` | ruff check |
| `make format` | ruff format |
| `make typecheck` | mypy strict |
| `make test` | pytest |
| `make ci` | lint + typecheck + test |

## Структура пакета

| Модуль | Назначение |
|--------|------------|
| `mentor/cli.py` | Typer CLI, Rich-вывод, HITL callback |
| `mentor/parser.py` | Разбор входа (GitHub URL / локальный путь) |
| `mentor/retrieval.py` | Копирование или `git clone` кода в workspace |
| `mentor/rubric.py` | Автоопределение темы, выбор рубрики |
| `mentor/skills.py` | Резолвер экспертных навыков |
| `mentor/agent.py` | Orchestrator: `create_deep_agent`, `spawn_reviewer`, `ask_user` |
| `mentor/brief.py` | Брифы для Reviewer-субагентов |
| `mentor/reviewer.py` | Reviewer-субагент: изолированная проверка аспекта |
| `mentor/ce.py` | Context Engineering: middleware, write_to_workspace |
| `mentor/feedback_validator.py` | Фильтр ложных claims против code-index |
| `mentor/render.py` | Feedback, compact-прогресс, HITL prompt |
| `mentor/renderer.py` | Verbose: план, субагенты, контекст, навыки |
| `mentor/tracker.py` | Трекинг токенов, CE-событий, HITL interrupt |

## Статус

| Sprint | Статус | Результат |
|--------|--------|-----------|
| 01 foundation | ✅ | CLI-скелет, конфиг, health-check OpenRouter |
| 02 e2e-flow | ✅ | E2E: parser, retrieval, orchestrator, Feedback |
| 03 context-bloat | ✅ | verbose-мониторинг контекста |
| 04 subagents-isolation | ✅ | Reviewer-субагенты, изоляция контекста |
| 05 context-engineering | ✅ | CE-механики, валидация feedback |
| 06 rubrics-skills | ✅ | Тематические рубрики, skills, HITL |
| 07 dogfooding | ✅ | Самопроверка, README, smoke E2E, CLI-тесты |

Roadmap: [roadmap.md](roadmap.md)
