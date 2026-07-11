# Changelog: multimodal-rag v002 (2026-07-05)

> Post **dataset-reviewer** + user edits. Предыдущая версия: [v001_2026-07-05.json](./v001_2026-07-05.json)

## Сводка

| | v001 | v002 |
|---|-----:|-----:|
| Items | 37 | **38** |
| S1 | 7 | 7 (2 items заменены) |
| S2 | 8 | **9** (+S2-9) |
| S3 | 10 | 10 (S3-5 перефраз) |
| S4 | 6 | 6 (S4-1/2/3 правки) |
| S5 | 6 | 6 (`trap_slides`) |
| ID внутри сегмента | sequential (v001 patch) | без изменений |
| S5 slide field | `required_slides` | **`trap_slides`** |

## Схема (все items)

- **S5:** `trap_slides` вместо `required_slides`.
- **S4:** `metadata.multi_type`: `cross_slide` | `single_slide_dense`.
- **Персоны:** `metadata.persona` на перефразах (стиль, не смысл).

## Изменения по items (v001 → v002)

| id | Изменение |
|----|-----------|
| S1-2 | перефраз, persona `hr-evaluator` |
| S1-6 | slide 2 «20+ лет» → slide **27**, «Кандидат с ИИ» vs «без ИИ» → **10x** |
| S1-7 | slide 2 «Основатель» → slide **21**, **3 Skills** |
| S2-9 | **new:** 72% на slide **10** |
| S3-5 | перефраз, persona `developer` |
| S4-1 | `required_slides` **[15]** (убран декоративный slide 1) |
| S4-2 | см. ниже |
| S4-3 | перефраз, persona `case-analyst` |
| S4-4/5/6 | `multi_type: single_slide_dense` |
| S5-* | `trap_slides`; S5-2 — перефраз, persona `procurement` |

**Slide 2 (S1):** 5 → **3** gold items (S1-1, S1-2, S1-5).

### S4-2 (эволюция)

1. v001: 7 slides `[28,29,32,34,37,39,40]` — не влезает в set-Recall@5.
2. Reviewer: сокращено до 5 slides, составной вопрос.
3. User + упрощение формулировки:

**Финал v002:**

- **Вопрос:** «Как в блоке ступени 3 раскрыта модель Коттера — от формирования коалиции до закрепления культуры?»
- **Gold:** `[28, 29, 34, 37, 40]`
- **Ответ:** коалиция/Champions+весы (2) → 4 слоя коммуникации (4) → 6 препятствий (5) → культура/Governance (8); обзор 8 шагов — айсберг (28).

## Без изменений относительно v001

S1-1, S1-3, S1-4, S1-5 · S2-1…S2-8 · S3-1…S3-4, S3-6…S3-10 · S4-4…S4-6 (кроме multi_type) · S5-1,3,4,5,6 (кроме trap_slides).

## Validation sample

✅ **PNG-verified пользователем** (2026-07-05):

| Items | Slides |
|-------|--------|
| S5-1 … S5-6 | trap: 10, 23, 33, 53, 15+27, 61 |
| S2-9 | 10 (72%) |
| S1-6, S1-7 | 27 (10x), 21 (3 Skills) |
| S4-2 | 28, 29, 34, 37, 40 |

## Eval baseline (Task 02)

- Config: `evals/configs/multimodal-baseline.yaml` → dataset **v002**, collection `multimodal_text_naive_v002`
- Отчёт: [`evals/reports/multimodal-baseline.md`](../../../reports/multimodal-baseline.md) (re-run 2026-07-05)
- Run JSON: `evals/reports/runs/multimodal-baseline-20260705T154657Z.json`

## Связанные документы (не в JSON)

- [`evals/datasets/multimodal/multimodal-rag/README.md`](./README.md)
- [`docs/eval/dataset-map.md`](../../../../docs/eval/dataset-map.md) — секция `rag/multimodal-rag`
