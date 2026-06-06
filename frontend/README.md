# Frontend — LLMStart Web Widget

Next.js 16 виджет «ИИ-Консультант»: витрина B2C-каталога и чат со SSE-стримингом от Agent Core.

## Запуск

Из корня репозитория:

```bash
make dev-frontend
# или полный стек
make dev
```

Откройте [http://localhost:3002](http://localhost:3002). Backend — `:8003` (см. `Makefile` / `.env`).

## Переменные окружения

Задаются в корневом `.env` (см. `.env.example`):

| Переменная | Default | Назначение |
|------------|---------|------------|
| `NEXT_PUBLIC_BACKEND_BASE_URL` | `http://localhost:8003` | Base URL Agent Core |
| `NEXT_PUBLIC_TELEGRAM_BOT_USERNAME` | — | Username бота для deep link handoff |

## Структура

```
frontend/
├── app/                    # App Router: page, layout, globals
├── components/
│   ├── catalog/            # ProductGrid, ProductCard, CatalogTabs
│   ├── layouts/            # SplitScreenLayout, FloatingWidgetLayout
│   ├── ui/                 # Button, Card, Dialog, …
│   └── widget/             # ChatPanel, ThinkingBlock, ToolStepper, …
├── hooks/
│   └── use-chat-stream.ts  # SSE state machine
└── lib/
    ├── api.ts              # GET /products
    ├── sse-client.ts       # POST /chat SSE parser
    ├── session.ts          # localStorage session_id
    ├── format.ts           # formatPrice
    └── prompts.ts          # Quick actions
```

## Ручные сценарии

### 1. Консультация

1. `make dev` → открыть `:3002`
2. Написать: «Какой курс выбрать новичку?»
3. Проверить блок «Думает вслух», шаги tools, ответ ассистента

### 2. Оплата (мок)

1. Написать или нажать quick action «Оформить покупку»
2. Дождаться события `payment_link` → кнопка «Перейти к оплате»
3. Ссылка открывается в новой вкладке

### 3. Telegram handoff

1. После первого turn проверить кнопку «Продолжить в Telegram»
2. URL: `https://t.me/<username>?start=s_<session_id>`
3. F5 → следующий вопрос использует тот же `session_id` из localStorage

## Качество

```bash
pnpm lint
pnpm typecheck
pnpm test
pnpm build
```

Или из корня: `make lint`, `make typecheck`, `make test-frontend`, `make ci`.
