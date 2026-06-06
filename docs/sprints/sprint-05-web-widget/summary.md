# Summary: Sprint 05 — web-widget

> **План:** [README.md](./README.md)  
> **Roadmap:** [../../roadmap.md](../../roadmap.md)  
> **Дата закрытия:** 2026-06-05

---

## Что реализовано

### Frontend (Next.js 16)

- **Виджет «ИИ-Консультант»:** `ChatPanel`, `MessageList`, `MessageBubble`, `ChatInput`, quick actions, Telegram CTA
- **Витрина:** `ProductGrid` / `ProductCard` / `CatalogTabs` — `GET /api/v1/products`, skeleton + error/retry
- **Layouts:** `SplitScreenLayout` (витрина + чат), `FloatingWidgetLayout` (FAB + Dialog), переключатель на `app/page.tsx`
- **SSE-клиент:** `lib/sse-client.ts` — парсинг `event:` / `data:`, typed events, abort
- **Чат-хук:** `hooks/use-chat-stream.ts` — state machine по событиям, `session_id` в localStorage, retry без stale session
- **«Думает вслух»:** `ThinkingBlock` + `ToolStepper` — шаги привязаны к сообщению ассистента, остаются после turn; итоговый ответ под блоком
- **Пошаговая анимация:** `lib/stream-pacing.ts` (минимальные паузы UI) + CSS `step-enter` на шагах
- **Rich blocks:** `ProductCardsInline`, `PaymentLinkCard`
- **Дизайн:** тёмная тема, cyan accent, glass-панели по макетам
- **Тесты:** 13 Vitest (SSE parser, format, session, stream-pacing, ProductCard, ToolStepper)

### Backend (доработки под виджет)

- **Потоковый SSE во время turn:** агент в worker-thread, tool-события уходят в стрим по мере вызова; паузы на синтезированных шагах и message-чанках (`sse_pacing.py`)
- **Reasoning:** операционный trace, не дублирует финальный ответ (`react_runner.py`)
- **Каталог в чате:** фильтр до 3 продуктов по упоминанию в ответе (`product_filter.py`)
- **Tools:** схемы `create_payment_link`, graceful error вместо 503 на KeyError
- **CORS / порты:** `NoDecode` для `CORS_ORIGINS`; dev на `:8003` / `:3002` (Windows)

### Инфра / документация

- `frontend/README.md` — env, структура, ручные сценарии
- Корневой `.env.example` — `NEXT_PUBLIC_*`, `CORS_ORIGINS`
- `Makefile` — `BACKEND_PORT` / `FRONTEND_PORT`, `test-frontend` = vitest + build
- `@next/env` в devDependencies — typecheck `next.config.ts`

---

## Отклонения от плана

| План | Факт | Причина |
|------|------|---------|
| `:3000` / `:8000` | `:3002` / `:8003` | Зависшие слушатели на Windows |
| `NEXT_PUBLIC_BACKEND_URL` | `NEXT_PUBLIC_BACKEND_BASE_URL` | Явное имя в `lib/config.ts` |
| Reasoning-текст в блоке | Только stepper (синтетические шаги + tools) | Итоговый ответ не дублировался в «Думает вслух» |
| Сворачивание блока после `done` | Блок остаётся, ответ ниже | UX по запросу при приёмке |
| Real-time только из backend delta | Backend thread-stream + frontend pacing | Видимая пошаговая анимация при пакетной доставке |
| DoD #1 `:3000` | `:3002` | Актуальные dev-порты в Makefile |

---

## Принятые решения

| Решение | Причина |
|---------|---------|
| `thinking` в `ChatMessage`, не глобальный state | История turn'ов: шаги не исчезают между сообщениями |
| `ToolEventCollector(on_event=...)` + queue | SSE tool-события во время `invoke`, не post-hoc |
| Eager session validation до `StreamingResponse` | `400` JSON до стрима (контракт sprint-04) |
| Автоочистка stale `session_id` + retry | 400 после перезапуска backend |
| `useSyncExternalStore` для session | Без hydration mismatch |
| `uvicorn` без `--reload` | Стабильность dev на Windows |

---

## Проблемы и решения

| Проблема | Как решили |
|----------|-----------|
| Шаги не видны — блок скрывался на `done` | `thinking` на сообщении; `isStreaming: false` без скрытия |
| Все SSE-события приходили пакетом | Backend: thread + live callbacks; frontend: `stream-pacing` |
| «Думает вслух» показывал финальный ответ | `_build_reasoning` — только операционный trace |
| Весь каталог в чате | `filter_recommended_products` по тексту ответа |
| `create_payment_link` → 503 | Схемы tool + error dict из sync_tools |
| Hydration mismatch `session_id` | `useSyncExternalStore` |
| `typecheck` — `@next/env` | `pnpm add -D @next/env` |
| Langfuse warning в логах | Безвредно; tracing опционален |

---

## Итог DoD спринта

| # | Критерий | Результат |
|---|----------|-----------|
| 1 | `make dev` → виджет на localhost | ✅ `:3002` (порты в Makefile) |
| 2 | Витрина `GET /products` | ✅ 6 B2C, цена ₽, loading/error |
| 3 | SSE: все типы событий | ✅ reasoning, tool, message, products, payment_link, done, error |
| 4 | «Думает вслух» + stepper по ходу стрима | ✅ с пошаговой анимацией |
| 5 | Карточки из `products` в ленте | ✅ `ProductCardsInline` |
| 6 | `payment_link` → кнопка оплаты | ✅ `PaymentLinkCard`, `target="_blank"` |
| 7 | Delta + `done` + `session_id` | ✅ два turn в одной сессии |
| 8 | Quick actions | ✅ три промпта |
| 9 | Telegram CTA с `session_id` | ✅ disabled без сессии |
| 10 | Split-screen + floating | ✅ переключатель |
| 11 | Ошибки JSON / SSE | ✅ alert в UI |
| 12 | `session_id` в localStorage | ✅ F5 сохраняет диалог |
| 13 | lint / typecheck / test-frontend / ci | ✅ `make test-frontend` (vitest + build) |
| 14 | `frontend/README.md` | ✅ |

---

## Что дальше

- **Sprint 06:** Telegram-бот, handoff `s_<session_id>`, E2E воронка до лида
- Полная воронка v0.1 (мок-оплата → лид) — sprint-06
- Production embed / deploy — v1.0

---

## Ссылки

- [Sprint 06: telegram-funnel](../sprint-06-telegram-funnel/README.md)
- [frontend/README.md](../../../frontend/README.md)
- [api-contracts.md](../../concept/api-contracts.md)
- Макеты: `design-reference.png`, `tech-preset-screens-mockup.png` (в папке спринта)
