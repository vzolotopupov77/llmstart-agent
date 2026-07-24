# Sprint 01: foundation

> **Версия roadmap:** v0.1
> **Roadmap:** [../../roadmap.md](../../roadmap.md)
> **Статус:** ✅ Done
> **Открыт:** 2026-07-12
> **Закрыт:** 2026-07-12

---

## Цель спринта

Поднять скелет проекта: Python-пакет `mentor` с `typer`-CLI, конфиг-системой и проверкой подключения к OpenRouter — чтобы следующий спринт мог сразу писать агентную логику.

**Боль, которую закрывает:** нет вообще ничего — пустой репозиторий. Этот спринт создаёт фундамент, без которого Sprint 02 невозможен.

**Deep-agent механизм не вводится** — это инфраструктурный спринт. Агентная логика начинается с Sprint 02.

---

## Навыки

Перед началом прочитать:
- `.agents/skills/modern-python/SKILL.md` — настройка Python-проекта (uv, ruff, mypy)
- `.agents/skills/uv-package-manager/SKILL.md` — управление пакетами и зависимостями

---

## DoD спринта

Sprint считается завершённым, когда:

| # | Критерий | Способ проверки |
|---|----------|-----------------|
| 1 | Проект инициализирован через `uv` | `uv sync` завершается без ошибок |
| 2 | Линтер и форматтер проходят | `make lint` → exit 0 |
| 3 | Типы проверяются | `make typecheck` → exit 0 |
| 4 | `mentor check --help` выводит справку | запустить и увидеть описание команды |
| 5 | `mentor check . --verbose` выводит стартовую панель с версией и конфигом | запустить и проверить вывод |
| 6 | При отсутствии `OPENROUTER_API_KEY` — ошибка на старте с понятным сообщением | убрать ключ из `.env`, запустить |
| 7 | Health-check до OpenRouter — успешный запрос | `mentor check . --verbose` показывает `✓ OpenRouter: соединение установлено` |
| 8 | `make ci` проходит | `make ci` → exit 0 |

---

## Задачи

| # | Задача | Статус | Plan | Summary |
|---|--------|--------|------|---------|
| 01 | `project-setup` — инициализация uv-проекта, ruff, mypy, Makefile | ✅ | — | [summary](./summary.md) |
| 02 | `config-system` — Config класс, config.yaml, .env.example, fail-fast валидация | ✅ | — | [summary](./summary.md) |
| 03 | `cli-skeleton` — typer-команда `mentor check`, Rich-панели, health-check OpenRouter | ✅ | — | [summary](./summary.md) |

---

## Задача 01: project-setup ✅

### Цель

Создать Python-пакет `mentor` с корректной структурой проекта: `uv`, `ruff`, `mypy` strict, `Makefile` со стандартными целями.

> 💡 **Скиллы:** прочитать `modern-python/SKILL.md` и `uv-package-manager/SKILL.md` перед началом.

### Состав работ

- [x] `uv init` в директории `ai-homework-mentor/`; настроить `pyproject.toml` (name=`mentor`, python=`>=3.12`)
- [x] Добавить зависимости: `deepagents`, `typer`, `rich`, `pydantic-settings`, `pyyaml`
- [x] Добавить dev-зависимости: `ruff`, `mypy`, `pytest`, `pytest-asyncio`
- [x] Настроить `ruff` (`select = ["ALL"]`, минимальный `ignore`) в `pyproject.toml`
- [x] Настроить `mypy` (strict) в `pyproject.toml`
- [x] Создать структуру пакета: `mentor/__init__.py`, `mentor/cli.py`, `mentor/agent.py`, `mentor/reviewer.py`, `mentor/config/` (пакет)
- [x] Создать `mentor/config/` с заглушками: `config.yaml`, `prompts/`, `rubrics/`
- [x] Написать `Makefile` с целями: `dev`, `lint`, `format`, `typecheck`, `test`, `ci`
- [x] Создать `.env.example` с комментариями
- [x] Самопроверка: `make lint && make typecheck`

### Критерии готовности (DoD)

**Агент проверяет:**

| # | Критерий | Способ проверки |
|---|----------|-----------------|
| 1 | `uv sync` без ошибок | `uv sync` → exit 0 |
| 2 | Линтер чистый | `make lint` → exit 0 |
| 3 | Типы чистые | `make typecheck` → exit 0 |
| 4 | Структура пакета на месте | `ls mentor/` показывает все модули |

**Пользователь проверяет:**

- `pyproject.toml` содержит все нужные зависимости
- `Makefile` содержит все обязательные цели
- `.env.example` содержит все переменные с пояснениями

### Артефакты

- `pyproject.toml`
- `Makefile`
- `.env.example`
- `mentor/__init__.py`, `mentor/cli.py`, `mentor/agent.py`, `mentor/reviewer.py`, `mentor/config.py` (заглушки)
- `mentor/config/config.yaml`, `mentor/config/prompts/`, `mentor/config/rubrics/` (заглушки)

---

## Задача 02: config-system ✅

### Цель

Реализовать `Config`-класс на `pydantic-settings`: загружает `config.yaml` и `.env`, падает с понятной ошибкой на старте при отсутствии обязательных переменных.

> 💡 **Скиллы:** `modern-python/SKILL.md` — паттерн конфига с pydantic-settings.

### Состав работ

- [x] Реализовать `mentor/config/__init__.py`: `AppConfig(BaseSettings)` с полями `openrouter_api_key`, `model`, `log_level`, `output_mode`, `context_limit`, `summarization_threshold`
- [x] Настроить загрузку из `.env` (через `model_config = SettingsConfigDict(env_file=".env")`)
- [x] Реализовать загрузку `config/config.yaml` (через `pyyaml`); значения из `.env` перекрывают YAML
- [x] Fail-fast: при отсутствии `OPENROUTER_API_KEY` — `SystemExit` с сообщением `"OPENROUTER_API_KEY is required. See .env.example"` на старте
- [x] Заполнить `mentor/config/config.yaml` реальными дефолтами (модель, лимиты, режим вывода)
- [x] Заполнить `.env.example` всеми переменными с пояснениями
- [x] Настроить логирование: stdout, уровень из `LOG_LEVEL`, формат human-readable в dev
- [x] Самопроверка: `make lint && make typecheck`

### Критерии готовности (DoD)

**Агент проверяет:**

| # | Критерий | Способ проверки |
|---|----------|-----------------|
| 1 | `AppConfig()` загружается без ошибок при наличии `.env` | `python -c "from mentor.config import AppConfig; AppConfig()"` → exit 0 |
| 2 | Без `OPENROUTER_API_KEY` — `SystemExit` с читаемым сообщением | убрать ключ, запустить выше → сообщение об ошибке |
| 3 | Линтер и типы чистые | `make lint && make typecheck` → exit 0 |

**Пользователь проверяет:**

- Сообщение об ошибке при отсутствии ключа — понятно без документации
- `config.yaml` содержит все параметры с разумными дефолтами

### Артефакты

- `mentor/config.py` (реализован)
- `mentor/config/config.yaml` (заполнен)
- `.env.example` (заполнен)

---

## Задача 03: cli-skeleton ✅

### Цель

Реализовать `typer`-команду `mentor check` с Rich-выводом стартовой панели (версия, модель, режим) и health-check подключения к OpenRouter.

> 💡 **Скиллы:** `sharp-edges/SKILL.md` — проверить обработку ошибок при HTTP-запросах к внешнему API.

### Состав работ

- [x] Реализовать `mentor/cli.py`: `app = typer.Typer()`, команда `check(input: str, verbose: bool, compact: bool)`
- [x] Прописать точку входа `mentor` в `pyproject.toml` (`[project.scripts]`)
- [x] Реализовать стартовую Rich-панель: версия, модель, режим вывода, статус конфига
- [x] Реализовать health-check: один тестовый запрос к OpenRouter (минимальный prompt); вывести `✓ OpenRouter: соединение установлено` или `✗ OpenRouter: [сообщение ошибки]`
- [x] Реализовать заглушку основного потока: после health-check вывести `⚠ Проверка не реализовано — Sprint 02`
- [x] Обработка ошибок: timeout, сетевые ошибки — сообщение без traceback
- [x] Самопроверка: `make lint && make typecheck`

### Критерии готовности (DoD)

**Агент проверяет:**

| # | Критерий | Способ проверки |
|---|----------|-----------------|
| 1 | `mentor check --help` выводит справку | `mentor check --help` → описание аргументов |
| 2 | `mentor check . --verbose` запускается и выводит стартовую панель | запустить с валидным `.env` |
| 3 | Health-check проходит при валидном ключе | видеть `✓ OpenRouter` в выводе |
| 4 | Без ключа — ошибка на старте, до health-check | убрать ключ, запустить |
| 5 | `make ci` → exit 0 | `make ci` |

**Пользователь проверяет:**

- Стартовая панель выглядит чисто и информативно
- Флаги `--verbose` и `--compact` принимаются без ошибок (поведение идентично — реализуется в Sprint 02)

### Артефакты

- `mentor/cli.py` (реализован)
- `pyproject.toml` (с точкой входа `mentor`)

### Демонстрация через Rich CLI

По завершении Sprint 01 пользователь видит:

```
$ mentor check . --verbose

╭─ AI Homework Mentor v0.1.0 ──────────────────────────────────────────╮
│  Модель:    google/gemini-2.5-flash                                   │
│  Режим:     verbose                                                   │
│  Конфиг:    mentor/config/config.yaml                                 │
│  Workspace: /tmp/mentor-workspace-a1b2c3/                             │
╰──────────────────────────────────────────────────────────────────────╯

✓ OpenRouter: соединение установлено

⚠  Запуск проверки: не реализовано — реализуется в Sprint 02
```

---

## Итог (заполняется после закрытия)

Скелет проекта готов: `mentor check` с Rich-панелью, конфигом и health-check OpenRouter. Все 8 критериев DoD пройдены. Следующий шаг — [Sprint 02: e2e-flow](../sprint-02-e2e-flow/plan.md).

**Summary:** [summary.md](./summary.md)
