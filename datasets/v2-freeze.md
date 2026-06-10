# Freeze: llmstart Agent Datasets v2

**Дата freeze:** 2026-06-09  
**База:** v1 (immutable) + reviewer patch  
**Статус:** immutability — правки только через **v3**

---

## Что изменилось относительно v1

| Область | Изменение |
|---------|-----------|
| Покрытие | +G8.1 (`b2c-nurture-001`), +G8.5 (`b2c-objection-m08`) |
| Переразметка | `b2c-rag-010` → `b2c-objection` / G4.2 |
| G9 | tool payment-flow → категория **G9.4** (6 записей); G9.1 только price/rassрочка |
| B2B | `b2b-segment-001/002` → `source: reconstruction`, перенос в synthetic |
| Эталоны | `b2c-rag-008` — условный возврат; `b2b-rag-002` — `must_not` |
| Metadata | `assistant_context: paraphrased` на multi-turn; `dataset_version: 2` |
| Персоны | 39/72 B2C synthetic+extraction с `persona` (было ~10/42 synthetic) |
| Метрики | Tool Call: exact — name + product_code; query/contact — fuzzy |

---

## Артефакты

| Датасет | Файл | Записей | SHA256 (16) |
|---------|------|---------|-------------|
| **B2C** | [`b2c/v2/dataset.jsonl`](b2c/v2/dataset.jsonl) | 72 | `728ddc74c0f28627` |
| **B2B** | [`b2b/v2/dataset.jsonl`](b2b/v2/dataset.jsonl) | 15 | `faec4e93b585ffd3` |

### Компоненты

| Компонент | Файл | Записей | SHA256 (16) |
|-----------|------|---------|-------------|
| B2C extraction | `b2c/v2/extraction.jsonl` | 29 | `9582e9c5ea87cac6` |
| B2C synthetic | `b2c/v2/synthetic.jsonl` | 43 | `0f6fa3a82f7e210f` |
| B2B extraction | `b2b/v2/extraction.jsonl` | 5 | `5f721c144283c755` |
| B2B synthetic | `b2b/v2/synthetic.jsonl` | 10 | `db7c04316da55a7d` |

---

## Процесс

| Стадия | Артефакт |
|--------|----------|
| Сборка v2 | [`scripts/build_v2_patch.py`](scripts/build_v2_patch.py) |
| Валидация | [`validation-report-v2.md`](validation-report-v2.md), [`validation-sample-v2.md`](validation-sample-v2.md) |
| Human review (шаблон) | [`validation-sample-review.md`](validation-sample-review.md) |
| v1 (reference) | [`v1-freeze.md`](v1-freeze.md) |

---

## Known limitations v2

- Strong model pass (20%) — **не выполнен**, backlog v3
- Extraction — expert-curated + `build_v2_patch.py`; SGR-pipeline — v3
- B2B inbound — 2 reconstruction-записи, реальных входящих мало
- Chunk ids / Hit Rate@k — v3

---

## v3 backlog

- Strong model pass + протокол `validation-strong-model.md`
- SGR extraction pipeline (`extraction/scripts/extract_windows.py`)
- Стабильные chunk ids + retrieval-метрики
- Больше реальных B2B/B2C диалогов
