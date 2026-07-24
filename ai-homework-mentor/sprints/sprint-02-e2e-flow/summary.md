# Summary: Sprint 02 — e2e-flow

> **План:** [plan.md](./plan.md)
> **Дата закрытия:** 2026-07-17

---

## Что реализовано

- `mentor/parser.py` — `parse_input(source, topic)`, GitHub URL / локальный путь, `submission.md`
- `mentor/retrieval.py` — `git clone` / copy → `workspace/code/`, `code-index.md`, фильтрация `.git`, `.env`, бинарников
- `mentor/agent.py` — orchestrator на `create_deep_agent`, `FilesystemBackend`, `write_todos`, retry до 5 попыток, `GraphRecursionError` с понятным сообщением
- `mentor/render.py` — прогресс плана, панель Feedback + Fix Plan
- `mentor/cli.py` — полный E2E-поток: `mentor check <source> [topic] [--compact|--verbose]`
- `mentor/config/prompts/orchestrator-system.yaml`, `mentor/config/rubrics/default.yaml`
- Зависимость `langchain-openrouter`
- `tests/` — `test_parser.py`, `test_retrieval.py`, `test_agent.py` (19 тестов в `make ci`)
- `README.md` — актуальные примеры CLI, статус спринтов, пометка про `reviewer.py`

---

## Отклонения от плана

- CLI: два positional-аргумента (`source`, `topic`) вместо одного `parse_input(raw)`
- Retry-логика (fresh thread, до 5 попыток) — не была в plan.md; добавлена после нестабильности Gemini Flash (ранняя остановка без tool call)
- Обработка `GraphRecursionError` — не была в plan.md; добавлена после прогона на большом репо (~45k строк)
- Фильтрация `.env` при копировании локального кода — дополнение к sharp-edges

---

## Принятые решения

| Решение | Причина |
|---------|---------|
| `langchain-openrouter` + `openrouter:{model}` | Официальный путь deepagents для OpenRouter |
| `MemorySaver` + retry | Модель иногда завершает цикл текстом без tool call |
| Fresh thread при нулевом прогрессе | Короткий «continue» в том же thread не перезапускал агента |
| `recursion_limit: 100` | Баланс для homework-размера; большие репо → понятная ошибка |
| `reviewer.py` не удалять | Sprint 04 — subagents; пометка в README |

---

## Проблемы и решения

| Проблема | Как решили |
|----------|-----------|
| `feedback.md` не создаётся — агент останавливается рано | Retry + усиленный system prompt (tool call до конца) |
| `--compact` vs `--verbose` — разное поведение | Один код; различие — недетерминизм LLM, не режим вывода |
| `GraphRecursionError` на Ttlg_bot_learning (~45k строк) | Понятное сообщение + указание на v0.1 / Sprint 03–04 |
| Пустая панель Feedback при `#`/`##` секциях | Улучшен парсинг `_extract_section` в `render.py` |
| Долгая пауза без вывода на retry | Норма; в compact нет промежуточных HTTP-логов |
| Ложное «README отсутствует» при dogfooding (`mentor check .`) | README есть в `code/README.md` и `code-index.md`; агент ищет в корне workspace — carry-over в Sprint 04–05, DoD в Sprint 07 |

---

## Итог DoD

| # | Критерий | Результат |
|---|----------|-----------|
| 1 | Локальный E2E + план в CLI | ✅ (dogfooding на `ai-homework-mentor`) |
| 2 | GitHub E2E | ✅ (`zva-hh-agent`, ~108 файлов) |
| 3 | Артефакты в workspace | ✅ |
| 4 | Compact: «Хорошо», «Обязательно исправить», Fix Plan | ✅ |
| 5 | Без темы — понятная ошибка | ✅ |
| 6 | `make ci` → exit 0 | ✅ (19 тестов) |
| 7 | Smoke-тест парсера | ✅ |

**Примечание:** очень большие репо (>~300 файлов / >~40k строк) могут упираться в `recursion_limit` — ожидаемое ограничение v0.1, закрывается в Sprint 03–04.

---

## Что дальше

- **Sprint 03 (context-bloat):** verbose-мониторинг контекста, наглядное раздувание окна на объёмном репо
- **Sprint 04 (subagents-isolation):** Reviewer-субагенты, реализация `mentor/reviewer.py`; явные пути `code/` в промптах и брифах (fix false positive по README)
- **Sprint 05 (context-engineering):** валидация синтеза против `code-index.md` перед выводом Feedback
- **Sprint 07 (dogfooding):** не допускать ложных замечаний о README при наличии файла в индексе

---

## Ссылки

- [roadmap.md](../../roadmap.md) — слой v0.1 закрыт
- [sprint-03-context-bloat/plan.md](../sprint-03-context-bloat/plan.md)
