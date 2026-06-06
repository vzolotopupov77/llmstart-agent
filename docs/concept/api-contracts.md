# API Contracts: LLMStart Agent

> **Базовый URL (локально):** `http://localhost:8000`  
> **Версия API:** `v1` — бизнес-логика по `/api/v1/...`  
> Интеграции и env — в [integrations.md](integrations.md).

---

## Общие конвенции

### Версионирование

- Бизнес-логика: `/api/v1/...`
- Служебные: `/health` — без версии

### Формат запросов и ответов

- Запросы: `Content-Type: application/json`, UTF-8
- JSON-ответы: `application/json`
- Стрим: `Accept: text/event-stream` → SSE (см. ниже)

### Формат ошибок

```json
{
  "detail": "Человекочитаемое описание ошибки"
}
```

Ошибка валидации (**422**):

```json
{
  "detail": [
    {
      "loc": ["body", "message"],
      "msg": "field required",
      "type": "missing"
    }
  ]
}
```

### HTTP-коды

| Код | Смысл |
|-----|-------|
| 200 | Успех (`GET`, `POST /chat` — без создания REST-ресурса в БД) |
| 400 | Бизнес-ошибка (неизвестная/истёкшая сессия, невалидный channel) |
| 404 | Не используется для пустых коллекций |
| 422 | Ошибка валидации схемы (Pydantic) |
| 503 | OpenRouter / MCP недоступны |

> **ADR (кандидат):** `POST /chat` возвращает **200**, не 201 — in-memory сессия, не персистентный ресурс.

### Пагинация

Для `GET /api/v1/products`:

```json
{
  "items": [],
  "total": 6,
  "limit": 20,
  "offset": 0
}
```

Пустая страница — `200` с `items: []`.

### Аутентификация (MVP)

Без auth для публичного демо-стенда. Опционально в compose: `X-Internal-Key` между `bot` и `backend` (не в публичном контракте виджета).

### CORS (MVP)

Разрешённые origins: `http://localhost:3000` (виджет). Production — post-MVP.

---

## Сводная таблица эндпоинтов

| Метод | Путь | Успех | Сценарий |
|-------|------|:-----:|----------|
| `POST` | `/api/v1/chat` | 200 | Сообщение в диалог (JSON или SSE) |
| `GET` | `/api/v1/products` | 200 | B2C-каталог для виджета |
| `GET` | `/health` | 200 | Liveness |

> **ADR (кандидаты):** один `/chat` + `Accept` (JSON \| SSE); форматирование по `channel` в Core.

---

## POST /api/v1/chat

**Сценарий:** один turn диалога — пользовательское сообщение → ответ агента. Сегмент B2B/B2C определяет **агент**, поле `segment` в API **нет**.

**Заголовки**

| Заголовок | Обязательный | Значение |
|-----------|:---:|----------|
| `Content-Type` | ✅ | `application/json` |
| `Accept` | ✅ | `application/json` или `text/event-stream` |

### Запрос

```json
{
  "message": "Какой курс выбрать новичку?",
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "channel": "web"
}
```

| Поле | Тип | Обязательное | Описание |
|------|-----|:---:|----------|
| `message` | string | ✅ | Текст пользователя, 1–4000 символов |
| `session_id` | string (UUID) | ❌ | Если нет — Core создаёт новую in-memory сессию |
| `channel` | string | ✅ | `web` \| `telegram` |

### Ответ при `Accept: application/json`

**Сценарий:** Telegram-бот, клиенты без стриминга.

**`200 OK`:**

```json
{
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "channel": "telegram",
  "message": "Вот подходящие курсы по промпт-инжинирингу: ...",
  "message_html": "<p>Вот подходящие курсы...</p>",
  "reasoning": "Пользователь ищет курс для новичка; подойдут agents и combo.",
  "tools": [
    {
      "name": "search_knowledge_base",
      "status": "done",
      "title": "Поиск в базе знаний"
    },
    {
      "name": "create_payment_link",
      "status": "done",
      "title": "Создание ссылки на оплату"
    }
  ],
  "products": [
    {
      "code": "agents",
      "title": "Промпт-инжиниринг: базовый курс",
      "price": 9900,
      "currency": "RUB"
    }
  ],
  "payment_link": "https://pay.llmstart.ru/invoice/agents-00123"
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `session_id` | string | ID сессии (новый или переданный) |
| `channel` | string | Эхо `channel` из запроса |
| `message` | string | Полный финальный текст (plain) |
| `message_html` | string | HTML для Telegram (`channel=telegram`); для `web` может совпадать с markdown-источником |
| `reasoning` | string | Краткое рассуждение агента |
| `tools` | array | Вызванные инструменты; `status`: `done` \| `error` |
| `products` | array \| null | Карточки продуктов turn'а; см. [Product](#product) |
| `payment_link` | string \| null | Мок-URL оплаты, если создан в turn |

**Элемент `tools[]`:**

| Поле | Тип | Описание |
|------|-----|----------|
| `name` | string | Имя tool (MCP) |
| `status` | string | `done` \| `error` |
| `title` | string | Человекочитаемый заголовок для UI |

### Ответ при `Accept: text/event-stream`

**Сценарий:** веб-виджет. Сервер шлёт **последовательность SSE-событий**, затем закрывает поток.

**`200 OK`**, заголовки: `Content-Type: text/event-stream`, `Cache-Control: no-cache`, `Connection: keep-alive`.

**Формат строк:**

```text
event: <type>
data: <json>

```

(пустая строка после `data` завершает событие)

#### Типы SSE-событий

| event | data | Назначение |
|-------|------|------------|
| `reasoning` | `{ "text": string }` | Рассуждение (блок «Рассуждение») |
| `tool` | `{ "name", "status", "title" }` | Статус tool: `started` ⟳ / `done` ✓ / `error` |
| `products` | `{ "items": Product[] }` | Карточки продуктов |
| `message` | `{ "delta": string }` | Чанк финального текста |
| `payment_link` | `{ "url": string }` | Мок-ссылка («Купить») |
| `done` | `{ "session_id", "message" }` | Завершение turn |
| `error` | `{ "detail": string }` | Ошибка генерации |

**`tool.status` (SSE):** `started` | `done` | `error`

#### Пример потока

```text
event: reasoning
data: {"text": "Пользователь хочет найти курсы по промпт-инжинирингу и ссылку на оплату..."}

event: tool
data: {"name": "search_knowledge_base", "status": "started", "title": "Поиск в базе знаний"}

event: tool
data: {"name": "search_knowledge_base", "status": "done", "title": "Поиск в базе знаний"}

event: tool
data: {"name": "create_payment_link", "status": "done", "title": "Создание ссылки на оплату"}

event: products
data: {"items": [{"code": "agents", "title": "Промпт-инжиниринг: базовый курс", "price": 9900, "currency": "RUB"}]}

event: message
data: {"delta": "Вот подходящие курсы по промпт-инжинирингу:"}

event: payment_link
data: {"url": "https://pay.llmstart.ru/invoice/agents-00123"}

event: done
data: {"session_id": "a1b2c3", "message": "Вот подходящие курсы..."}

```

> События `products` и `payment_link` — только если релевантны turn'у.

### Ошибки `POST /chat`

| Код | Условие | Пример `detail` |
|-----|---------|-----------------|
| 422 | Нет `message` / неверный `channel` | Pydantic `detail` |
| 400 | Неизвестный `session_id` (нет в памяти) | `"Session not found or expired"` |
| 400 | `message` длиннее 4000 | `"Message too long"` |
| 503 | OpenRouter недоступен | `"LLM service unavailable"` |
| 503 | MCP subprocess недоступен | `"Tools service unavailable"` |

При ошибке до старта стрима — обычный JSON `detail`. При ошибке mid-stream (SSE) — событие `event: error` и закрытие потока.

### Примеры curl

**JSON (Telegram-подобный клиент):**

```bash
curl -s -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"message":"Привет","channel":"telegram"}'
```

**SSE (виджет):**

```bash
curl -N -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"message":"Привет","channel":"web"}'
```

---

## Product

Общая схема продукта B2C (JSON-ответ, SSE `products`, `GET /products`):

| Поле | Тип | Описание |
|------|-----|----------|
| `code` | string | Код продукта (`agents`, `deep-agents`, `ai-agents-combo`, …) |
| `title` | string | Название |
| `price` | integer | Цена в минимальных единицах валюты (копейки для RUB); мок на MVP |
| `currency` | string | `RUB` |

---

## GET /api/v1/products

**Сценарий:** получить B2C-каталог для прямого рендера в виджете (витрина, превью). В диалоге каталог доступен агенту через MCP `list_b2c_products`.

**Query-параметры:**

| Параметр | Тип | Обязательное | Описание |
|----------|-----|:---:|----------|
| `limit` | integer | ❌ | По умолчанию `20`, макс `100` |
| `offset` | integer | ❌ | По умолчанию `0` |

**Ответ `200 OK`:**

```json
{
  "items": [
    {
      "code": "ai-agents-combo",
      "title": "Комбо из 4 программ",
      "price": 0,
      "currency": "RUB"
    },
    {
      "code": "vibe-coding-intensive",
      "title": "Интенсив по Cursor",
      "price": 0,
      "currency": "RUB"
    }
  ],
  "total": 6,
  "limit": 20,
  "offset": 0
}
```

**Ошибки:** `422` — невалидный `limit`/`offset`.

**Пример:**

```bash
curl -s "http://localhost:8000/api/v1/products?limit=20&offset=0"
```

---

## GET /health

**Ответ `200 OK`:**

```json
{
  "status": "ok",
  "version": "0.1.0"
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `status` | string | `ok`, если процесс жив |
| `version` | string | Версия из конфига / package |

---

## OpenAPI

Интерактивная схема: `http://localhost:8000/docs` (генерация FastAPI из Pydantic-моделей).

---

## Связанные документы

- [architecture.md](architecture.md) — Accept, channel, ADR-0006…0008
- [integrations.md](integrations.md) — клиенты, base URL
- [vision.md](vision.md) — сценарии и воронка
