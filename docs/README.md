# Документация LLMStart Agent

Навигатор по проектной документации (AI-driven / Spec-driven). Черновик продукта до онбординга: [`../project-draft.md`](../project-draft.md).

---

## С чего начать

| Задача | Документ |
|--------|----------|
| Быстрый старт, make-команды | [../README.md](../README.md) |
| Понять продукт и MVP | [concept/idea.md](concept/idea.md) |
| Техническое видение, компоненты, роли | [concept/vision.md](concept/vision.md) |
| План реализации по спринтам | [roadmap.md](roadmap.md) |
| Текущий этап | [roadmap.md](roadmap.md) — **v0.2 Развитие RAG-ассистента** (GraphRAG ✅, Multimodal RAG ✅; v0.1 MVP ✅) |

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
| [roadmap.md](roadmap.md) | v0.1 MVP ✅ → v0.2 RAG-ассистент → v0.3 hardening → v1.0 production |

### Спринты (`sprints/`)

| Sprint | Статус | Ссылка |
|--------|--------|--------|
| 01 infra-bootstrap | ✅ Done | [sprint-01-infra-bootstrap](sprints/sprint-01-infra-bootstrap/README.md) |
| 02 mcp-tools-rag | ✅ Done | [sprint-02-mcp-tools-rag](sprints/sprint-02-mcp-tools-rag/README.md) |
| 03 agent-core | ✅ Done | [sprint-03-agent-core](sprints/sprint-03-agent-core/README.md) |
| 04 api-stream-catalog | ✅ Done | [sprint-04-api-stream-catalog](sprints/sprint-04-api-stream-catalog/README.md) |
| 05 web-widget | ✅ Done | [sprint-05-web-widget](sprints/sprint-05-web-widget/README.md) |
| 06 telegram-funnel | ✅ Done | [sprint-06-telegram-funnel](sprints/sprint-06-telegram-funnel/README.md) |
| 07 langfuse-v3 | ✅ Done | [sprint-07-langfuse-v3](sprints/sprint-07-langfuse-v3/README.md) |
| 08 vector-db | ✅ Done | [sprint-08-vector-db](sprints/sprint-08-vector-db/README.md) |
| 09 graphrag | ✅ Done | [sprint-09-graphrag](sprints/sprint-09-graphrag/README.md) |
| 10 multimodal-rag | ✅ Done | [sprint-10-multimodal-rag](sprints/sprint-10-multimodal-rag/README.md) · [final report](../evals/reports/multimodal-final.md) |

В каждом спринте: `README.md`, `tasks/<NN-task>/plan.md`, `summary.md`.

### Eval (sprint-10 multimodal-rag)

| Артефакт | Описание |
|----------|----------|
| [multimodal-final.md](../evals/reports/multimodal-final.md) | Финальный отчёт: матрица 7×5 + цена, decision log, вердикт |
| [eval/README.md](eval/README.md) | Eval-контур, все multimodal-отчёты |

---

## Решения (`adrs/`)

Архитектурные записи (ADR). Файлы в `docs/adrs/`.

| ADR | Тема | Файл |
|-----|------|------|
| 0001 | Единое Agent Core, тонкие каналы | [ADR-0001](adrs/ADR-0001-agent-core-channels.md) |
| 0002 | Инструменты — отдельный MCP-сервер | [ADR-0002](adrs/ADR-0002-mcp-server.md) |
| 0003 | LLM — OpenRouter (`OPENAI_*` env) | [ADR-0003](adrs/ADR-0003-openrouter-llm.md) |
| 0004 | Платежи и CRM — моки | [ADR-0004](adrs/ADR-0004-payment-crm-mocks.md) |
| 0005 | In-memory сессии | [ADR-0005](adrs/ADR-0005-in-memory-sessions.md) |
| 0006 | Один `/chat`, JSON vs SSE через `Accept` | [ADR-0006](adrs/ADR-0006-chat-json-sse.md) |
| 0007 | Форматирование в Core по `channel` | [ADR-0007](adrs/ADR-0007-channel-formatting.md) |
| 0008 | HTTP 200 на `/chat` | [ADR-0008](adrs/ADR-0008-http-200-chat.md) |
| 0009 | Vector DB для RAG-слоя — Qdrant | [ADR-0009](adrs/ADR-0009-vector-db.md) |
| 0010 | Graph DB для GraphRAG — Neo4j | [ADR-0010](adrs/ADR-0010-graphrag.md) |

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
├── adrs/                  # ADR (архитектурные решения)
├── specs/                 # фичи (по необходимости)
└── sprints/
    └── sprint-NN-<name>/
        ├── README.md
        └── tasks/
```

---

*Последнее обновление навигатора: 2026-07-11 (sprint-10 multimodal-rag закрыт)*
