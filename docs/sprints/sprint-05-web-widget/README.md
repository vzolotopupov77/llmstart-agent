# Sprint 05: web-widget

> **Версия roadmap:** v0.1  
> **Roadmap:** [../../roadmap.md](../../roadmap.md)  
> **Зависит от:** [sprint-04-api-stream-catalog](../sprint-04-api-stream-catalog/README.md)  
> **Статус:** ✅ Done  
> **Открыт:** 2026-06-05  
> **Закрыт:** 2026-06-05

---

## Цель спринта

Реализовать **веб-виджет** в `frontend/` (Next.js 16, App Router): полноценный UI «ИИ-Консультант» с потреблением **`POST /api/v1/chat` (SSE)** и витриной **`GET /api/v1/products`**. Пользователь видит в реальном времени блок «Думает вслух» (reasoning + шаги tools), карточки продуктов, кнопку мок-оплаты и CTA «Продолжить в Telegram» с handoff `session_id`. После спринта web-канал закрывает критерии v0.1 roadmap (#4) и готов к E2E-воронке вместе с sprint-06.

**Дизайн-референсы** (визуальная цель, не pixel-perfect):

| Макет | Содержание |
|-------|------------|
| `design-reference.png` | Desktop: split-screen — витрина курсов на фоне + центральное окно чата; блок «Думает вслух» (stepper); quick actions; тёмная тема, cyan glow, glass-панели |
| `tech-preset-screens-mockup.png` | Три сценария в чате: подбор курсов (карточки), сравнение (таблица в ответе агента), checkout (кнопка оплаты по `payment_link`) |

---

## DoD спринта

Sprint считается завершённым, когда:

| # | Критерий | Способ проверки |
|---|----------|-----------------|
| 1 | `make dev` → `http://localhost:3000` открывает виджет (не заглушку) | Браузер |
| 2 | Витрина: `GET /api/v1/products` → сетка карточек (6 продуктов B2C), цена в ₽, загрузка/ошибка обработаны | DevTools Network + UI |
| 3 | Отправка сообщения → SSE-поток: парсятся события `reasoning`, `tool`, `message`, `products`, `payment_link`, `done`, `error` | DevTools + ручной сценарий |
| 4 | Блок «Думает вслух»: reasoning-текст + stepper tools (`started` ⟳ / `done` ✓ / `error` ✗) обновляется по ходу стрима | Сценарий «Какой курс для новичка?» |
| 5 | Карточки продуктов из события `products` рендерятся в ленте чата (title, price, code) | Сценарий подбора курса |
| 6 | Событие `payment_link` → кнопка «Купить» / «Перейти к оплате» (внешняя ссылка, `target="_blank"`) | Сценарий «хочу купить …» |
| 7 | `message` delta накапливается в bubble ассистента; после `done` — полный текст + сохранённый `session_id` | Два turn подряд с тем же `session_id` |
| 8 | Quick actions («Подобрать курс», «Сравнить тарифы», «Оформить покупку») подставляют готовый prompt в input и отправляют turn | Клик по каждой кнопке |
| 9 | CTA Telegram: ссылка `https://t.me/<TELEGRAM_BOT_USERNAME>?start=s_<session_id>`; `session_id` из последнего `done`; если сессии нет — кнопка disabled + подсказка | Проверка href после первого сообщения |
| 10 | Два режима layout: **split-screen** (витрина + чат) и **floating pop-up** (кнопка-триггер, модальное окно чата) — переключатель на странице | Переключение без перезагрузки |
| 11 | Ошибки: JSON до стрима (`400`/`503`) и SSE `event: error` — понятное сообщение в UI, разблокировка input | Мок: backend down / невалидный session |
| 12 | `session_id` в `localStorage` (или аналог) — перезагрузка страницы продолжает диалог | F5 после turn → следующий вопрос в той же сессии |
| 13 | `make lint` / `make typecheck` / `make test-frontend` / `make ci` зелёные | CI |
| 14 | `frontend/README.md` обновлён: env, запуск, структура компонентов, ручные сценарии | Ручной просмотр |

---

## Scope

### В scope

| Область | Содержание |
|---------|------------|
| **Инициализация UI-стека** | shadcn/ui, базовые компоненты (Button, Card, Input, ScrollArea, Badge, Dialog/Sheet) |
| **Дизайн-система** | Тёмная тема по макетам: `zinc`/`slate` фон, cyan accent, glass (`backdrop-blur`, полупрозрачные панели), glow на active-элементах |
| **`lib/api.ts`** | Base URL из `NEXT_PUBLIC_BACKEND_URL`; `fetchProducts()`, типы `Product`, `ProductListResponse` |
| **`lib/sse-client.ts`** | `postChatStream(message, sessionId?)` → async iterator / callback по событиям SSE; парсинг `event:` / `data:` |
| **`lib/session.ts`** | Хранение `session_id` (localStorage), clear/restore |
| **`lib/format.ts`** | `formatPrice(kopecks, currency)` → «29 900 ₽» |
| **Витрина** | `ProductGrid` / `ProductCard` — данные с `GET /products`; skeleton + error state |
| **Чат** | `ChatPanel`, `MessageList`, `MessageBubble`, `ChatInput` (textarea + send, disabled во время стрима) |
| **Reasoning / tools** | `ThinkingBlock` («Думает вслух»): reasoning-текст + `ToolStepper` (вертикальный список шагов по SSE `tool`) |
| **Rich blocks в чате** | `ProductCardsInline` (из SSE `products`), `PaymentLinkCard` (из `payment_link`) |
| **Quick actions** | Три кнопки-подсказки над input (тексты промптов — константы в `lib/prompts.ts`) |
| **Telegram CTA** | `TelegramHandoffButton` — deep link по [integrations.md § Handoff](../../concept/integrations.md#handoff-web--telegram) |
| **Layouts** | `SplitScreenLayout` (витрина слева/фон + чат справа/центр), `FloatingWidgetLayout` (FAB + Dialog) |
| **`app/page.tsx`** | Главная демо-страница с переключателем режимов |
| **Env** | `NEXT_PUBLIC_BACKEND_URL` (default `http://localhost:8000`), `NEXT_PUBLIC_TELEGRAM_BOT_USERNAME` |
| **Тесты** | Vitest: парсер SSE (unit), `formatPrice`, session helpers; smoke `ProductCard` render |
| **Документация** | `frontend/README.md`, `.env.example` (корень) — новые `NEXT_PUBLIC_*` |

### Вне scope

| Область | Спринт / версия |
|---------|-----------------|
| Изменения backend API, SSE-контракта | sprint-04 (стабильно) |
| Telegram-бот (polling, handlers) | sprint-06 |
| Embed-скрипт на llmstart.ru, iframe SDK | v1.0 |
| Полноценная форма checkout (промокод, СБП, карта) из макета screen 3 | Post-MVP; достаточно кнопки `payment_link` |
| Вложения в чат (paperclip) | Post-MVP |
| Token-level typing effect (посимвольно) | YAGNI; достаточно delta-чанков из SSE |
| i18n / локализация | Русский only |
| Auth, rate limits | v0.2 |
| Production CORS / CDN deploy | v1.0 |
| Отдельный mobile-first breakpoint polish | Базовая адаптивность (stack на узком экране) — в scope; pixel-perfect mobile — post-MVP |

---

## UI / UX (по макетам)

### Общая эстетика

- Фон: глубокий тёмный (`#0a0f1a` / `zinc-950`), сетка или subtle gradient.
- Акцент: cyan / electric blue (`cyan-400`, `sky-500`) — borders, glow, active quick action.
- Панели: `bg-white/5`, `border border-white/10`, `backdrop-blur-md`.
- Шрифт: Geist (уже в scaffold) или системный sans; заголовок виджета — «ИИ-Консультант», статус «В сети» (green dot).

### Split-screen (основной режим, `design-reference.png`)

```
┌─────────────────────────────────────────────────────────────┐
│  [Популярные] [Новые] [Для начинающих]     🔍  🔔  👤      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                     │
│  │ LLM      │ │ ML       │ │ AI       │  ... ProductGrid    │
│  │ 9 990 ₽  │ │ 4.8 ★    │ │ ...      │                     │
│  └──────────┘ └──────────┘ └──────────┘                     │
│                    ┌─────────────────────┐                  │
│                    │ ИИ-Консультант  🟢  │                  │
│                    │ ─ chat messages ─   │                  │
│                    │ Думает вслух ▼      │                  │
│                    │ [Подобрать][Сравн.] │                  │
│                    │ [____________][➤]    │                  │
│                    └─────────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

- Витрина — `GET /products` (табы «Популярные» и др. — UI-фильтр client-side или статичные заголовки без backend-фильтра на MVP).
- Чат — overlay / правая колонка поверх витрины (как на макете).

### Floating pop-up

- FAB (иконка чата) в правом нижнем углу.
- По клику — Dialog/Sheet с тем же `ChatPanel` (без витрины или с компактным превью каталога).
- Закрытие не сбрасывает `session_id`.

### Блок «Думает вслух» (`tech-preset-screens-mockup.png`)

Маппинг SSE → UI:

| SSE | UI-элемент |
|-----|------------|
| `reasoning` | Текстовый блок / первый шаг «Анализ запроса» |
| `tool` `started` | Шаг со спиннером ⟳ |
| `tool` `done` | Шаг с ✓ (зелёный) |
| `tool` `error` | Шаг с ✗ (красный) |
| Конец стрима (`done`) | Сворачивание блока (опционально) или статус «Готово» |

Заголовки шагов — из поля `title` события `tool` (backend уже отдаёт человекочитаемые названия).

### Quick actions (промпты по умолчанию)

| Кнопка | Prompt (пример) |
|--------|-----------------|
| Подобрать курс | «Подбери курс по LLM для начинающего» |
| Сравнить тарифы | «Сравни курсы agents и deep-agents по цене и программе» |
| Оформить покупку | «Хочу оформить покупку курса agents» |

### Сравнение и checkout (макет screens 2–3)

- **Сравнение:** агент отвечает текстом/markdown в `message`; виджет рендерит plain text (или простой markdown — `react-markdown`, если добавление зависимости оправдано). Отдельный UI-компонент `ComparisonTable` — только если агент стабильно возвращает структуру; на MVP достаточно форматированного текста в bubble.
- **Checkout:** кнопка по `payment_link.url`; без встроенной формы оплаты.

---

## Контракты (потребление)

Источник истины: [api-contracts.md](../../concept/api-contracts.md). Виджет использует:

### `POST /api/v1/chat` (SSE)

```http
POST /api/v1/chat
Content-Type: application/json
Accept: text/event-stream

{"message": "...", "session_id": "<optional>", "channel": "web"}
```

Обработка событий — строго по таблице sprint-04. Порядок в UI:

1. Показать `ThinkingBlock`, очистить предыдущие шаги turn'а.
2. На каждое событие — обновить state (React).
3. `message` delta — append к текущему bubble ассистента.
4. `products` — вставить block карточек после текущего bubble.
5. `payment_link` — card с CTA под сообщением.
6. `done` — зафиксировать `session_id`, разблокировать input.
7. `error` — toast/alert, разблокировать input.

### `GET /api/v1/products`

```http
GET /api/v1/products?limit=20&offset=0
```

Для витрины; те же поля `Product`, что в SSE.

### Telegram handoff

```text
https://t.me/${NEXT_PUBLIC_TELEGRAM_BOT_USERNAME}?start=s_${sessionId}
```

Бот и парсинг `s_<uuid>` — sprint-06; виджет только формирует ссылку.

---

## Шаги реализации

### 1. Bootstrap UI-стека

- `pnpm add` зависимости: shadcn init (`components.json`), базовые UI-компоненты.
- Настроить Tailwind 4 + CSS variables для темы (accent, glass, glow).
- Обновить `app/layout.tsx`: `lang="ru"`, metadata «LLMStart — ИИ-Консультант».
- Добавить в корневой `.env.example`: `NEXT_PUBLIC_BACKEND_URL`, `NEXT_PUBLIC_TELEGRAM_BOT_USERNAME`.

### 2. API-слой и типы

- `lib/types.ts` — `Product`, `ChatStreamEvent` (discriminated union по `event`).
- `lib/api.ts` — `getProducts(limit?, offset?)` с обработкой HTTP-ошибок.
- `lib/format.ts` — форматирование цены (копейки → рубли с разделителем).

### 3. SSE-клиент

- `lib/sse-client.ts`:
  - `fetch` + `ReadableStream` / `getReader()`; декодер UTF-8.
  - Буферизация неполных строк; парсинг `event:` и `data:`.
  - Yield typed events; abort через `AbortController` при unmount / новом сообщении.
- Unit-тесты: фикстура raw SSE → массив событий.

### 4. Session state

- `lib/session.ts` — `getSessionId()`, `setSessionId()`, `clearSessionId()` через `localStorage`.
- Хук `useChatSession()` — синхронизация с `done.session_id`.

### 5. Хук чата

- `hooks/use-chat-stream.ts`:
  - State: `messages[]`, `thinking` (reasoning + tools), `isStreaming`, `error`, `products`, `paymentLink`.
  - `sendMessage(text)` — вызов SSE-клиента, редьюсер по событиям.
  - Отмена предыдущего стрима при новом сообщении.

### 6. Компоненты витрины

- `components/catalog/ProductCard.tsx` — title, price, code (опционально badge).
- `components/catalog/ProductGrid.tsx` — grid responsive, loading skeleton, error retry.
- `components/catalog/CatalogTabs.tsx` — декоративные табы (MVP: без фильтрации или фильтр по `code` client-side).

### 7. Компоненты чата

- `components/widget/ChatPanel.tsx` — композиция: header, messages, thinking, actions, input, telegram CTA.
- `components/widget/MessageList.tsx` / `MessageBubble.tsx` — user справа (blue), assistant слева (dark glass).
- `components/widget/ChatInput.tsx` — textarea, send button, disabled при `isStreaming`.
- `components/widget/ThinkingBlock.tsx` + `ToolStepper.tsx` — stepper по макету.
- `components/widget/ProductCardsInline.tsx` — горизонтальный/вертикальный список карточек в ленте.
- `components/widget/PaymentLinkCard.tsx` — цена + кнопка «Перейти к оплате».
- `components/widget/QuickActions.tsx` — три кнопки → `sendMessage(prompt)`.
- `components/widget/TelegramHandoffButton.tsx` — внешняя ссылка, disabled без session.

### 8. Layouts и страница

- `components/layouts/SplitScreenLayout.tsx` — витрина + чат-панель (центр/справа).
- `components/layouts/FloatingWidgetLayout.tsx` — FAB + Dialog с `ChatPanel`.
- `app/page.tsx` — toggle режимов, общий header «Курсы по ИИ».

### 9. Обработка ошибок и edge cases

- Backend недоступен при загрузке каталога — empty state + retry.
- `400` / `503` JSON на `POST /chat` — alert в чате.
- SSE `error` mid-stream — показать `detail`, сохранить частичный ответ.
- Пустой `TELEGRAM_BOT_USERNAME` — скрыть или disable CTA с tooltip «Бот не настроен».

### 10. Тесты и качество

- Vitest + Testing Library: `sse-client` parser, `formatPrice`, render `ProductCard`, `ToolStepper` states.
- `make test-frontend` в корневом Makefile (если ещё не wired — добавить `vitest run`).
- Цикл Edit → Sanitize → Verify: `pnpm lint`, `pnpm typecheck`, vitest на изменённые файлы.
- `make ci` зелёный перед закрытием.

### 11. Документация

- `frontend/README.md`: структура `components/widget/`, env, 3 ручных сценария (консультация, оплата, Telegram link).
- Ссылка на макеты в README спринта (этот файл).

---

## Зависимости и env

| Переменная | Компонент | Назначение |
|------------|-----------|------------|
| `NEXT_PUBLIC_BACKEND_URL` | frontend | Default `http://localhost:8000` |
| `NEXT_PUBLIC_TELEGRAM_BOT_USERNAME` | frontend | Username бота без `@` для deep link |
| `TELEGRAM_BOT_USERNAME` | `.env` (корень) | Уже может быть для bot; продублировать в `NEXT_PUBLIC_*` для виджета |

Backend env без изменений (sprint-04). CORS `http://localhost:3000` уже настроен.

---

## Риски и допущения

| Риск | Митигация |
|------|-----------|
| Буферизация SSE в dev-proxy | Прямой запрос на backend URL; Next.js rewrites только если проверено без буфера |
| Сложность shadcn + Tailwind 4 | Инициализировать shadcn рано; зафиксировать версии в `pnpm-lock.yaml` |
| Длинный стрим блокирует UI | React state batching; спиннер на send; abort предыдущего fetch |
| `localStorage` недоступен (SSR) | Читать/писать только в `useEffect` (client components) |
| Макет checkout ≠ API | MVP — только `payment_link`; форма из макета — визуальный ориентир на v1.0 |

**Допущения:**

- Все интерактивные части виджета — Client Components (`"use client"`).
- Один экземпляр чата на страницу; без роутинга `/chat/[id]`.
- Сравнение тарифов — через текст агента, не отдельный structured response.
- Табы витрины на MVP декоративные или с client-side filter (без нового API).
- Бот из sprint-06 может не существовать при приёмке 05 — проверяем только корректность URL.

---

## Skills

Перед реализацией прочитать:

- `nextjs-app-router-patterns` — Client Components, data fetching, layout
- `shadcn` — инициализация, Card, Dialog, Button
- `frontend-design` — тёмная tech-эстетика по макетам
- `vercel-react-best-practices` — state, streaming UI, bundle size
- `api-design-principles` — потребление контрактов, error handling

---

## Итог

Next.js виджет с SSE-чатом, витриной каталога, блоком «Думает вслух» (пошаговая анимация), quick actions и Telegram handoff. Dev: `:3002` / `:8003`.

Подробности: [summary.md](./summary.md).
