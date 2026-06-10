# Freeze: llmstart Agent Datasets v1

**Дата freeze:** 2026-06-09  
**Статус:** immutability — правки только через **v2** (новые файлы / новая папка)

---

## Артефакты

| Датасет | Файл | Записей | SHA256 (16) |
|---------|------|---------|-------------|
| **B2C** | [`b2c/v1/dataset.jsonl`](b2c/v1/dataset.jsonl) | 70 | `a7ada7f0f0da18cd` |
| **B2B** | [`b2b/v1/dataset.jsonl`](b2b/v1/dataset.jsonl) | 15 | `e83ae784f4bbc5b2` |

### Компоненты

| Компонент | Файл | Записей | SHA256 (16) |
|-----------|------|---------|-------------|
| B2C extraction | `b2c/v1/extraction.jsonl` | 28 | `3527bae17ca86556` |
| B2C synthetic | `b2c/v1/synthetic.jsonl` | 42 | `cef5c6d5af7b408a` |
| B2B extraction | `b2b/v1/extraction.jsonl` | 7 | `404bfd418b34476b` |
| B2B synthetic | `b2b/v1/synthetic.jsonl` | 8 | `57f25f664db6573a` |

---

## Процесс (выполнено)

| Стадия | Артефакт |
|--------|----------|
| Анализ | [`extraction/analysis-report.md`](extraction/analysis-report.md) |
| План | [`dataset-plan.md`](dataset-plan.md) |
| Валидация | [`validation-report.md`](validation-report.md), [`validation-sample.md`](validation-sample.md) |
| Скрипт валидации | [`scripts/validate_dataset.py`](scripts/validate_dataset.py) |

---

## Формат записи

ChatML: `id`, `input` (string | multi-turn array), `expected_output` (`segment`, `product_codes`, `answer_key_points`, `tools`, …), `metadata` (`dataset_type`, `group`, `category`, `source`, `turn_mode`).

---

## Метрики v1 (проектирование)

- Segment / Product Match — exact
- Answer Correctness — LLM-judge по `answer_key_points`
- Clarification Score — 0 / 0.5 / 1.0
- Tool Call Accuracy — name + args
- Hit Rate@k — **v2** (chunk ids не фиксировали)

---

## Known limitations v1

- G8.1, G8.5 — не покрыты → исправлено в [**v2**](v2-freeze.md)
- B2B `b2b-segment-001/002` — реконструкция из исходящего CHAT_0127 → v2: `source: reconstruction`
- Strong model pass — не выполнен
- Extraction v1 — expert-curated, без SGR-pipeline

---

## v2

См. [`v2-freeze.md`](v2-freeze.md) — актуальная версия для Evaluation.
