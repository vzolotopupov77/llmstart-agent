# Summary: Sprint 06 — telegram-funnel

> **План:** [README.md](./README.md)  
> **Roadmap:** [../../roadmap.md](../../roadmap.md)  
> **Дата закрытия:** 2026-06-06

---

## Что реализовано

### Пакет `bot/` (aiogram 3)

- **Entry point:** `bot/main.py` — long polling, graceful shutdown
- **Config:** `bot/config.py` — `Settings` из `.env`, fail-fast на `TELEGRAM_BOT_TOKEN`
- **Core client:** `bot/api/core_client.py` — `POST /api/v1/chat` (JSON, `channel: telegram`), timeout 120 с, маппинг 400/503/сеть
- **Handlers:** `/start` (handoff `s_<uuid>`), текстовые сообщения → Core
- **Session store:** in-memory `chat_id → session_id`
- **Messaging:** `message_html` (parse_mode HTML), fallback plain text, `payment_link` follow-up, разбиение длинных сообщений, блок «Курсы»
- **Тесты:** 19 pytest (start payload, core client, session store, messaging, smoke main)

### Backend (доработки под Telegram-приёмку)

- **`channel_formatter.py`:** конвертация ответа в Telegram-совместимый HTML (`<b>`, `<a>`, списки без `<ol>/<li>`)
- **`price_formatter.py` + MCP `price_display`:** цены в рублях, не в копейках
- **Langfuse:** `init_langfuse` в lifespan, metadata `session_id`/`channel`, flush после turn (трейсы в UI — v0.2, см. roadmap)

### Инфра / документация

- `Makefile`: `dev-bot`, `lint-bot`, `typecheck-bot`, `test-bot`; `make dev` = backend + frontend + bot (`-j3`)
- CI: job `bot` в `.github/workflows/ci.yml`
- `bot/README.md` — env, запуск, 3 ручных сценария
- Корневой `README.md`, `.env.example` — `TELEGRAM_*`, `BACKEND_BASE_URL`

---

## Отклонения от плана

| План | Факт | Причина |
|------|------|---------|
| DoD #10 — trace в Langfuse UI | Отложено в **v0.2** | Server v2.95.11 не принимает OTLP; SDK готов |
| 16 тестов (оценка в чате) | 19 pytest | Добавлены `test_messaging`, `test_price` |
| Только `bot/` | Правки backend под HTML/цены | Баги ручной приёмки |

---

## Принятые решения

| Решение | Причина |
|---------|---------|
| In-memory `session_store`, без FSM | YAGNI для одного инстанса polling |
| `/start` без вызова Core | Сессия на первом текстовом сообщении |
| Fallback `_plain_without_markdown()` | Telegram отклонял невалидный HTML |
| Цены через `price_display` в каталоге | Единообразие с виджетом (₽, не копейки) |
| Langfuse upgrade → v0.2 | Несовместимость server v2 ↔ SDK v3+ |

---

## Проблемы и решения

| Проблема | Как решили |
|----------|-----------|
| Сырой markdown (`**`, `[text](url)`) в Telegram | HTML-форматтер в Core + plain fallback в боте |
| Цены в копейках | Нормализация в backend/MCP + `bot/utils/price.py` |
| `No Langfuse client...` в логах | `init_langfuse()` в lifespan backend |
| Трейсы не в UI | Зафиксировано: апгрейд Langfuse server → v0.2 |

---

## Итог DoD спринта

| # | Критерий | Результат |
|---|----------|-----------|
| 1 | `make dev` / `make dev-bot` → polling | ✅ |
| 2 | Текст → Core → `message_html` | ✅ |
| 3 | `/start` без payload — приветствие | ✅ |
| 4 | `/start s_<uuid>` — handoff web | ✅ |
| 5 | Невалидный session_id — сообщение, не падение | ✅ |
| 6 | B2C подбор + `payment_link` | ✅ |
| 7 | Воронка до лида в `leads.txt` (6 полей) | ✅ |
| 8 | 503 / сеть — сообщение на русском | ✅ |
| 9 | Два turn — контекст сохраняется | ✅ |
| 10 | Langfuse trace за turn | ⏭ v0.2 (UI traces) |
| 11 | `make ci` зелёный | ✅ |
| 12 | `bot/README.md` | ✅ |
| 13 | Корневой README + `.env.example` | ✅ |

---

## Что дальше

- **v0.1 MVP закрыт** — оба канала (web + Telegram), E2E-воронка
- **v0.2:** Langfuse v3 self-hosted, guardrails, rate limits
- **v1.0:** Postgres, реальные платежи/CRM, production deploy

---

## Ссылки

- [Roadmap v0.1](../../roadmap.md)
- [bot/README.md](../../../bot/README.md)
- [Sprint 05 handoff](../sprint-05-web-widget/README.md)
- [api-contracts.md](../../concept/api-contracts.md)
