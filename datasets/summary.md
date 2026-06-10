# Summary — сборка датасетов llmstart Agent

**Дата:** 2026-06-09  
**Актуальная версия:** **v2** — см. [`v2-freeze.md`](v2-freeze.md)

## Что сделано

### v1 (frozen)

- **B2C** — 70 записей (28 extraction + 42 synthetic)
- **B2B** — 15 записей (7 extraction + 8 synthetic)

### v2 (reviewer patch)

- **B2C** — 72 записей (+G8.1, +G8.5; переразметка G4.2/G9.4; персоны; эталоны)
- **B2B** — 15 записей (reconstruction → synthetic; extraction 5 + synthetic 10)
- Сборка: `python datasets/scripts/build_v2_patch.py`
- Валидация: `python datasets/scripts/validate_dataset.py --version v2` → PASS

## Ключевые решения

- Таксономия G1–G9 из анализа реальных диалогов (`datasets/dialogs/`)
- Параллельные B2C и B2B датасеты; CHAT_0127 только в B2B
- G4: эталон «публичного демо нет»
- Гибрид turn_mode: ~77% single / ~23% multi (B2C)
- Chunk ids / Hit Rate@k отложены в v2

## DoD

| Критерий | Статус |
|----------|--------|
| Анализ + таксономия апрувнута | ✅ |
| План-документ апрувнут | ✅ |
| B2C/B2B извлечение + синтетика | ✅ |
| Структурная валидация PASS | ✅ |
| Validation sample 10% апрувнут | ✅ |
| Freeze v1 зафиксирован | ✅ |

## Артефакты

- План: `dataset-plan.md`
- Freeze v1: `v1-freeze.md` | **v2:** `v2-freeze.md`
- Датасеты v2: `b2c/v2/dataset.jsonl`, `b2b/v2/dataset.jsonl`
- Human review: `validation-sample-review.md` (шаблон)
