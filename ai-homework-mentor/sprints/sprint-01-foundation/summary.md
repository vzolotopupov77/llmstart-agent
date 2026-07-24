# Summary: Sprint 01 — foundation

> **План:** [plan.md](./plan.md)
> **Дата закрытия:** 2026-07-12

---

## Что реализовано

- `pyproject.toml` — пакет `mentor`, Python 3.12+, hatchling, ruff/mypy/pytest, entry point `mentor`
- `Makefile` — `dev`, `lint`, `format`, `typecheck`, `test`, `ci`
- `.env.example`, `.gitignore`, `README.md`, `mentor.cmd` — онбординг и локальный запуск на Windows
- `mentor/` — пакет: `cli.py`, `agent.py`, `reviewer.py`, `openrouter.py`, `logging_setup.py`
- `mentor/config/` — `AppConfig` (pydantic-settings), `config.yaml`, заглушки `prompts/`, `rubrics/`
- `tests/` — smoke-тесты конфига (3) и health-check OpenRouter (3)

---

## Отклонения от плана

- `mentor/config.py` заменён на пакет `mentor/config/__init__.py` — в Python нельзя одновременно иметь модуль `config.py` и директорию `config/`; импорт `from mentor.config import AppConfig` сохранён.
- `make dev` дополнительно выполняет `uv tool install -e .` — чтобы команда `mentor` была в PATH без активации venv.
- Добавлена явная зависимость `httpx` (health-check) и `mentor.cmd` (fallback на Windows).

---

## Принятые решения

| Решение | Причина |
|---------|---------|
| Конфиг как пакет `mentor/config/` | Совместимость с YAML-артефактами в той же директории |
| `uv tool install` в `make dev` | Документированный UX: `mentor check` после `make dev` |
| UTF-8 reconfigure в CLI | Rich-символы `✓/✗/⚠` и кириллица на Windows cp1251 |
| Заглушки `agent.py` / `reviewer.py` | Агентная логика — Sprint 02 / 04 |

---

## Проблемы и решения

| Проблема | Как решили |
|----------|-----------|
| `mentor` не найден после `uv sync` | `uv tool install -e .` в `make dev` + `mentor.cmd` + `uv run mentor` в README |
| UnicodeEncodeError на Windows при выводе ✗ | `sys.stdout.reconfigure(encoding="utf-8")` в `_create_console()` |
| 403 от OpenRouter у части ключей | CLI корректно показывает `✗ OpenRouter: [сообщение]` без traceback; пользователь проверил с валидным ключом |

---

## Итог DoD

| # | Критерий | Результат |
|---|----------|-----------|
| 1 | `uv sync` без ошибок | ✅ |
| 2 | `make lint` → exit 0 | ✅ |
| 3 | `make typecheck` → exit 0 | ✅ |
| 4 | `mentor check --help` | ✅ (проверено пользователем) |
| 5 | `mentor check . --verbose` — стартовая панель | ✅ (проверено пользователем) |
| 6 | Без `OPENROUTER_API_KEY` — fail-fast | ✅ (проверено пользователем) |
| 7 | Health-check OpenRouter успешен | ✅ (проверено пользователем) |
| 8 | `make ci` → exit 0 | ✅ (6 тестов) |

---

## Что дальше

- **Sprint 02 (e2e-flow):** получение кода, план (todo), проверка по рубрике, вывод Feedback
- Заглушка в CLI: `⚠ Запуск проверки: не реализовано — Sprint 02`

---

## Ссылки

- [roadmap.md](../../roadmap.md) — слой v0.1
- [sprint-02-e2e-flow/plan.md](../sprint-02-e2e-flow/plan.md)
