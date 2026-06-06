# Sprint 02: mcp-tools-rag

> **Версия roadmap:** v0.1  
> **Roadmap:** [../../roadmap.md](../../roadmap.md)  
> **Зависит от:** [sprint-01-infra-bootstrap](../sprint-01-infra-bootstrap/README.md)  
> **Статус:** ✅ Done  
> **Открыт:** 2026-06-05  
> **Закрыт:** 2026-06-05

---

## Цель спринта

Реализовать MCP-сервер инструментов (`mcp_server/`) со всеми пятью tools, RAG по B2B/B2C базам знаний, каталогом продуктов и моками лид/оплата; подготовить содержимое `data/` и возможность вызывать tools из CLI/тестов (без Agent Core — sprint-03).

---

## DoD спринта

Sprint считается завершённым, когда:

| # | Критерий | Способ проверки |
|---|----------|-----------------|
| 1 | MCP-сервер стартует по stdio, отдаёт список из 5 tools | `uv run python -m mcp_server` + MCP inspector / интеграционный тест |
| 2 | `search_knowledge_base(query, segment)` возвращает релевантные чанки из B2B или B2C | pytest с фиксированным запросом по seed-данным |
| 3 | `list_b2c_products()` → 6 продуктов из `data/b2c/catalog.json` | pytest / ручной вызов tool |
| 4 | `create_payment_link` → мок-URL; `confirm_payment` → ok; `save_lead` → append в `data/leads.txt` (6 полей) | pytest end-to-end воронки |
| 5 | Chroma persist в `data/.chroma/`; переиндексация при изменении файлов в `data/b2b`, `data/b2c` | Удалить `.chroma`, перезапустить indexer, поиск работает |
| 6 | `make test` / `make ci` включают тесты mcp_server | `make ci` |
| 7 | Seed-данные: минимум 2 MD-файла в `data/b2b/`, 2 в `data/b2c/`, `catalog.json` с 6 slug'ами | Ручной просмотр `data/` |

---

## Scope

### В scope

| Область | Содержание |
|---------|------------|
| `mcp_server/` | MCP SDK, stdio transport, регистрация tools |
| Tools | `search_knowledge_base`, `list_b2c_products`, `save_lead`, `create_payment_link`, `confirm_payment` |
| RAG | Индексация PDF/MD, Chroma в `data/.chroma/`, embeddings через OpenRouter |
| `data/` | Seed knowledge base, `catalog.json`, `leads.txt`, опционально `data/payments.json` для state мок-оплаты |
| Тесты | Unit + integration для каждого tool; мок OpenRouter embeddings в unit-тестах |
| Makefile | `make test-mcp`, включение в `make test` / `make ci` |

### Вне scope

- Agent Core, MCP-клиент в backend — sprint-03
- `POST /chat`, Langfuse traces — sprint-03
- Реальные платежи и CRM
- HTTP-транспорт MCP (только stdio)
- Парсинг PDF — опционально; MVP достаточно MD, PDF — если успеваем

---

## Контракт tools (MVP)

Согласовано с [architecture.md § MCP](../../concept/architecture.md#mcp-core--mcp_server):

| Tool | Вход | Выход / поведение |
|------|------|-------------------|
| `search_knowledge_base` | `query: str`, `segment: "b2b" \| "b2c"` | Список чанков `{text, source, segment}` |
| `list_b2c_products` | — | `{items: [{code, title, price, currency, description}]}` из `catalog.json` |
| `create_payment_link` | `product_id`, `session_id` | `{url}` — мок `https://pay.mock.llmstart.ru/checkout?...` |
| `confirm_payment` | `session_id`, `product_id` | `{status: "confirmed"}` — без проверки реального платежа |
| `save_lead` | `email`, `phone`, `name`, `product_id`, `channel`, `segment` | `{ok: true}` + append JSON line в `leads.txt` |

Поля лида — [vision.md §7](../../concept/vision.md#7-доменные-сущности).

Каталог — 6 продуктов из [project-draft.md](../../../project-draft.md): `ai-agents-combo`, `vibe-coding-intensive`, `fullstack-aidd`, `agents`, `deep-agents`, `consultation`.

---

## Шаги реализации

### 1. Каркас mcp_server

- Инициализировать `mcp_server/` (uv, pyproject.toml, ruff, mypy, pytest).
- Структура по [architecture.md](../../concept/architecture.md):

```
mcp_server/
├── server.py              # точка входа MCP stdio
├── tools/
│   ├── search_knowledge_base.py
│   ├── list_b2c_products.py
│   ├── save_lead.py
│   └── payment.py         # create_payment_link + confirm_payment
├── rag/
│   ├── indexer.py
│   └── retriever.py
└── data_access/
    ├── catalog.py
    └── leads.py
```

- `server.py`: регистрация всех tools, запуск stdio-сервера.

### 2. Seed-данные data/

- `data/b2c/catalog.json` — 6 продуктов с ценами (RUB), slug, краткое описание.
- `data/b2c/*.md` — 2+ файла: описания курсов, FAQ B2C.
- `data/b2b/*.md` — 2+ файла: корп. обучение, заказ разработки, FAQ B2B.
- `data/leads.txt` — пустой или с комментарием-заголовком (не JSON до первого лида).
- Опционально `data/payments.json` — in-memory state подтверждений (или dict в процессе MCP).

### 3. RAG: indexer + retriever

- `rag/indexer.py`:
  - Сканирует `data/b2b/`, `data/b2c/` (MD; PDF — опционально).
  - Chunking (фиксированный размер / по заголовкам).
  - Embeddings через OpenAI-compatible API (`OPENAI_API_KEY`, `OPENAI_BASE_URL`).
  - Persist Chroma в `data/.chroma/`.
  - CLI/функция `reindex()` — вызывается при старте сервера, если индекс пуст или mtime файлов новее.
- `rag/retriever.py`:
  - Поиск с фильтром `segment` (metadata).
  - Top-k чанков (k=3–5, конфигурируемо).

### 4. Tool: search_knowledge_base

- Валидация `segment` ∈ {b2b, b2c}.
- Вызов retriever, форматирование ответа для LLM.
- Обработка пустого индекса → понятная ошибка tool.

### 5. Tool: list_b2c_products

- Чтение `data/b2c/catalog.json` через `data_access/catalog.py`.
- Валидация схемы (6 items, обязательные поля).
- Кэш in-process (invalidate по mtime файла).

### 6. Tools: payment (мок)

- `create_payment_link`: генерация URL по шаблону из [integrations.md §6](../../concept/integrations.md#6-платёжный-провайдер-мок-mvp); сохранение pending-state по `session_id`.
- `confirm_payment`: пометка confirmed (без верификации платежа); идемпотентность повторного confirm.

### 7. Tool: save_lead

- Валидация 6 обязательных полей.
- Append JSON Lines в `data/leads.txt` (формат из integrations §7).
- Не логировать PII в stdout.

### 8. Тесты и качество

- Unit: catalog, leads append, payment URL format, segment filter (mock retriever).
- Integration: subprocess MCP или прямой вызов handlers с тестовой `data/` (tmp dir).
- Integration RAG: с мок embeddings или skip-marker при отсутствии `OPENAI_API_KEY`.
- `make test-mcp`, обновить корневой `Makefile`.

### 9. Документация

- `mcp_server/README.md`: запуск, env, reindex, примеры вызова tools.
- Обновить корневой README: секция MCP (stdio, данные в `data/`).

---

## Зависимости и env

| Переменная | Компонент | Назначение |
|------------|-----------|------------|
| `OPENAI_API_KEY` | mcp_server | Embeddings (OpenRouter) |
| `OPENAI_BASE_URL` | mcp_server | `https://openrouter.ai/api/v1` |
| Embedding model | config mcp_server | напр. `openai/text-embedding-3-small` |

Полный список — [.env.example](../../../.env.example).

---

## Риски и допущения

| Риск | Митигация |
|------|-----------|
| OpenRouter недоступен при индексации | Отдельная команда `make reindex`; CI без реального API (мок) |
| Chroma растёт на диске | `.chroma/` в `.gitignore`; документировать `make reindex` |
| PDF-парсинг усложняет спринт | MVP на MD; PDF — stretch goal |
| stdio без backend-клиента | Тесты через прямой вызов + subprocess; клиент в sprint-03 |

**Допущение:** путь к `data/` резолвится от корня репо (env `DATA_DIR` или относительный путь при stdio subprocess).

---

## Skills

Перед реализацией прочитать:

- `modern-python`, `uv-package-manager` — структура пакета
- `python-testing-patterns` — фикстуры, tmp data dir
- `build-mcp-server` — паттерны MCP tools
- `langchain-fundamentals` — только для RAG/embeddings паттернов (не Agent Core)

---

## Итог (заполняется после закрытия)

Sprint закрыт 2026-06-05. MCP-сервер с 5 tools, RAG B2B/B2C (Chroma), seed `data/`, моки оплаты и лидов; 17 тестов, `make ci` зелёный.

Подробности: [summary.md](./summary.md).
