# Документация LLMStart Agent

Навигатор по проектной документации (AI-driven / Spec-driven). Черновик продукта до онбординга: [`../project-draft.md`](../project-draft.md).

---

## С чего начать

| Задача | Документ |
|--------|----------|
| Понять продукт и MVP | [concept/idea.md](concept/idea.md) |
| Техническое видение, компоненты, роли | [concept/vision.md](concept/vision.md) |
| План реализации по спринтам | [roadmap.md](roadmap.md) |
| Текущий спринт | [sprints/](sprints/) (создаётся по мере работы) |

---

## Концепт (`concept/`)

Продуктовый и архитектурный слой — заполнен на онбординге.

| Документ | Содержание |
|----------|------------|
| [idea.md](concept/idea.md) | Суть, аудитория, MVP, примеры запросов |
| [vision.md](concept/vision.md) | Компоненты, сценарии, стек, ADR-0001…0005 |
| [architecture.md](concept/architecture.md) | Контейнеры, MCP, SSE, деплой, внутренняя структура |
| [integrations.md](concept/integrations.md) | OpenRouter, Langfuse, Telegram, моки, env |
| [api-contracts.md](concept/api-contracts.md) | `POST /chat`, SSE, `GET /products`, `/health` |

**Не в scope MVP:** [data-model.md](concept/data-model.md) — появится с Postgres (v1.0).

---

## Дорожная карта

| Документ | Содержание |
|----------|------------|
| [roadmap.md](roadmap.md) | v0.1 MVP → v0.2 hardening → v1.0 production, спринты 01–06 |

### Спринты (`sprints/`)

| Sprint | Статус | Ссылка |
|--------|--------|--------|
| 01 infra-bootstrap | ✅ Done | [sprint-01-infra-bootstrap](sprints/sprint-01-infra-bootstrap/README.md) |
| 02 mcp-tools-rag | ✅ Done | [sprint-02-mcp-tools-rag](sprints/sprint-02-mcp-tools-rag/README.md) |
| 03 agent-core | 📋 Planned | [sprint-03-agent-core](sprints/sprint-03-agent-core/README.md) |
| 04 api-stream-catalog | 📋 Planned | [sprint-04-api-stream-catalog](sprints/sprint-04-api-stream-catalog/README.md) |
| 05 web-widget | 📋 Planned | [sprint-05-web-widget](sprints/sprint-05-web-widget/README.md) |
| 06 telegram-funnel | 📋 Planned | [sprint-06-telegram-funnel](sprints/sprint-06-telegram-funnel/README.md) |

В каждом спринте: `README.md`, `tasks/<NN-task>/plan.md`, `summary.md`.

---

## Решения (`decisions/`)

Архитектурные записи (ADR). Зафиксированы в vision, файлы — по мере реализации.

| ADR | Тема |
|-----|------|
| 0001 | Единое Agent Core, тонкие каналы |
| 0002 | Инструменты — отдельный MCP-сервер |
| 0003 | LLM — OpenRouter (`OPENAI_*` env) |
| 0004 | Платежи и CRM — моки |
| 0005 | In-memory сессии |
| 0006 | Один `/chat`, JSON vs SSE через `Accept` |
| 0007 | Форматирование в Core по `channel` |
| 0008 | HTTP 200 на `/chat` |

---

## Спецификации (`specs/`)

Функциональные требования по фичам (`requirements.md`, `design.md`, `tasks.md`) — появятся при детализации отдельных возможностей. Карта фич: `specs/README.md` (создать при первой spec).

---

## Вне репозитория

| Ресурс | Путь |
|--------|------|
| Методология | [`.methodology/`](../.methodology/README.md) |
| Правила Cursor | [`.cursor/rules/methodology/`](../.cursor/rules/methodology/) |
| MCP (Cursor) | [`.cursor/mcp.json`](../.cursor/mcp.json), [`.env.example`](../.env.example) |
| Шаблоны документов | [`.methodology/templates/`](../.methodology/templates/) |

---

## Структура `docs/`

```
docs/
├── README.md              ← вы здесь
├── roadmap.md
├── concept/
│   ├── idea.md
│   ├── vision.md
│   ├── architecture.md
│   ├── integrations.md
│   └── api-contracts.md
├── decisions/             # ADR (по мере создания)
├── specs/                 # фичи (по необходимости)
└── sprints/
    └── sprint-NN-<name>/
        ├── README.md
        └── tasks/
```

---

*Последнее обновление навигатора: 2026-06-05*
