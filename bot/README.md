# LLMStart Telegram Bot

Тонкий адаптер к Agent Core: long polling (aiogram 3), `POST /api/v1/chat` с `channel: telegram`. Без локальной логики агента и без прямых вызовов MCP.

## Prerequisites

- Python 3.12+, [uv](https://docs.astral.sh/uv/)
- Запущенный backend (`make dev-backend` или `make dev`)
- `TELEGRAM_BOT_TOKEN` от [@BotFather](https://t.me/BotFather)

## Environment

Переменные в корневом `.env` (см. `.env.example`):

| Переменная | Обязательная | Default | Описание |
|------------|:---:|---------|----------|
| `TELEGRAM_BOT_TOKEN` | ✅ | — | Токен бота |
| `TELEGRAM_BOT_USERNAME` | ❌ | — | Username без `@` (для документации / deep link) |
| `BACKEND_BASE_URL` | ❌ | `http://127.0.0.1:8003` | URL Agent Core |
| `BOT_CHAT_TIMEOUT_SECONDS` | ❌ | `120` | Timeout HTTP-запроса к Core |
| `LOG_LEVEL` | ❌ | `INFO` | Уровень логирования |

## Запуск

```bash
# из корня репозитория
make dev-bot

# или вместе со стеком
make dev
```

Только бот (backend уже запущен):

```bash
cd bot && uv sync --dev && uv run python -m bot.main
```

## Структура

```
bot/
├── bot/
│   ├── main.py              # long polling, startup
│   ├── config.py            # Settings из .env
│   ├── api/
│   │   └── core_client.py   # HTTP → POST /api/v1/chat
│   ├── handlers/
│   │   ├── start.py         # /start, handoff s_<uuid>
│   │   └── message.py       # текстовые сообщения → Core
│   ├── services/
│   │   ├── session_store.py # chat_id → session_id
│   │   └── start_payload.py
│   └── utils/
│       └── messaging.py     # HTML, payment_link, split long text
└── tests/
```

## Handoff web → Telegram

Виджет формирует ссылку:

```text
https://t.me/<TELEGRAM_BOT_USERNAME>?start=s_<session_id>
```

Бот парсит payload `s_<uuid>`, сохраняет `session_id` и продолжает in-memory сессию Core.

## Ручные сценарии

### 1. Новый диалог

1. `/start` — приветствие.
2. «Какой курс выбрать новичку?» — ответ в HTML.
3. Уточняющий вопрос — контекст сохраняется (тот же `session_id`).

### 2. Handoff с сайта

1. Открыть http://localhost:3002, отправить сообщение в виджет.
2. Нажать «Продолжить в Telegram».
3. В боте — «Продолжаем диалог с сайта».
4. Спросить про предыдущую тему — агент помнит контекст web-сессии.

### 3. Воронка до лида

1. «Подбери курс для новичка» → рекомендация.
2. «Хочу купить agents» → ссылка на оплату (кнопка «Перейти к оплате»).
3. «Оплатил, ivan@mail.ru, +79991234567, Иван» → подтверждение.
4. Проверить последнюю строку `data/leads.txt` — `channel: telegram`, 6 полей лида.

## Качество

```bash
make lint-bot
make typecheck-bot
make test-bot
```

## Связанные документы

- [api-contracts.md](../docs/concept/api-contracts.md) — контракт `/chat`
- [integrations.md § Telegram](../docs/concept/integrations.md#5-telegram-bot-api)
- [sprint-06 README](../docs/sprints/sprint-06-telegram-funnel/README.md)
