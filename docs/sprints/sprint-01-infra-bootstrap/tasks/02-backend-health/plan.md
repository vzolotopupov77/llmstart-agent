# Task 02: backend-health

> **Sprint:** [../../README.md](../../README.md)  
> **Тип:** feat  
> **Ветка:** `feat/backend-1-health-endpoint`  
> **Spec:** без spec — см. [api-contracts.md](../../../../concept/api-contracts.md) (`GET /health`)

---

## Цель

Минимальный FastAPI-сервис Agent Core с рабочим `GET /health`, конфигурацией из env и smoke-тестом.

---

## Состав работ

- [ ] Инициализировать `backend/` через `uv init` / `pyproject.toml` (Python 3.12+, FastAPI, uvicorn, pydantic-settings)
- [ ] Структура: `app/main.py`, `app/core/config.py`, `app/api/routes/health.py`
- [ ] Эндпоинт `GET /health` → `200` `{"status": "ok", "service": "llmstart-agent-backend"}`
- [ ] Настроить ruff (`select = ["ALL"]`, минимальный ignore), mypy strict, pytest + httpx TestClient
- [ ] Тест `tests/test_health.py`: статус 200, тело JSON
- [ ] Самопроверка по критериям DoD
- [ ] (после «ок» пользователя) Создать `summary.md`, обновить sprint README.md

---

## Критерии готовности (DoD)

| # | Критерий | Способ проверки |
|---|----------|-----------------|
| 1 | `GET /health` → 200 JSON | `cd backend && uv run pytest tests/test_health.py` |
| 2 | ruff check без ошибок | `cd backend && uv run ruff check .` |
| 3 | mypy без ошибок | `cd backend && uv run mypy .` |
| 4 | Тесты проходят | `cd backend && uv run pytest` |

---

## Артефакты

- `backend/pyproject.toml` — зависимости и tool config (ruff, mypy, pytest)
- `backend/app/main.py` — FastAPI app, подключение роутера health
- `backend/app/core/config.py` — `Settings` из env (пока без обязательных LLM-ключей для health)
- `backend/app/api/routes/health.py` — роут `/health`
- `backend/tests/test_health.py` — smoke-тест

---

## Scope

**Трогаем:** только `backend/**`.

**НЕ трогаем:**
- `GET /ready`, `POST /chat`, MCP-клиент — sprint-03
- `Makefile` — задача 04
- Langfuse-интеграция — sprint-03

---

## Риски и допущения

- Допущение: для health-теста не нужны реальные `OPENAI_*` ключи.
- Риск: слишком строгий config на старте — в этой задаче валидируем только `LOG_LEVEL` (default INFO).

---

## Открытые вопросы

- [ ] Префикс API `/api/v1` для health: в api-contracts health на корне `/health` — следуем контракту.
