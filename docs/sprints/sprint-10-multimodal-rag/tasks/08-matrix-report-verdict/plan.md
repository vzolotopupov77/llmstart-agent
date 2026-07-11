# Task 08: matrix-report-verdict

> **Sprint:** [../../README.md](../../README.md)
> **Тип:** docs (eval / synthesis)
> **Spec:** [analysis.md](../../analysis.md), [metric_map.md](../../metric_map.md)
> **Предшественники:** Task 04–07 summaries

---

## Цель

Собрать сводную матрицу «конфигурация × сегмент» со столбцами цены, зафиксировать decision log и вердикт — какая точка спектра методов оправдана для визуально-плотного B2B-корпуса (66 слайдов) и какой ценой — и закрыть sprint-10.

---

## Состав работ

1. Сводная таблица: 7 конфигураций (baseline, A_tesseract, A_rapidocr, B_nemotron, B_gemini, C, D) × 5 сегментов + `index_size_mb`, `build_time_s`, `est_cost_usd`.
2. Decision log: минимум по одной числовой записи на метод A/B/C/D.
3. Вердикт: рекомендуемая точка спектра (возможна комбинация по сегментам) с обоснованием числами.
4. Антипаттерны: явный список (ColPali ради ColPali, среднее по больнице, CER на глаз, молчаливая правка чисел у B, TEDS без контекста).
5. Обновить `docs/roadmap.md`: sprint-10 → Done.
6. Обновить sprint `README.md`: статус Task 08, дата закрытия, раздел «Итог».

---

## Источники данных

| Конфигурация | Отчёт |
|---|---|
| baseline | [multimodal-baseline.md](../../../../evals/reports/multimodal-baseline.md) |
| A_tesseract, A_rapidocr | [multimodal-a-ocr.md](../../../../evals/reports/multimodal-a-ocr.md) |
| B_nemotron, B_gemini | [multimodal-b-caption.md](../../../../evals/reports/multimodal-b-caption.md) |
| C | [multimodal-c-unified.md](../../../../evals/reports/multimodal-c-unified.md) |
| D | [multimodal-d-multivector.md](../../../../evals/reports/multimodal-d-multivector.md) |

Датасет: `evals/datasets/multimodal/multimodal-rag/v002_2026-07-05.json` (38 items).

---

## Метрики по сегментам (primary)

| Сегмент | Primary retrieval | В матрице |
|---|---|---|
| S1_text, S2_chart, S3_layout | nDCG@5, Recall@5 | оба |
| S4_multi | Set-Recall@5 | Set-Recall@5 (+ Recall@5 вспомогательно) |
| S5_unanswerable | `correct_refusal_rate` (generation) | trap_in_topk (retrieval-диагностика) |

Ingestion (CER, TEDS) — отдельная диагностика, не в retrieval-матрице.

---

## DoD

### Агент проверяет

- [x] `evals/reports/multimodal-final.md` содержит все 7 конфигураций и 5 сегментов + 3 столбца цены.
- [x] Decision log содержит минимум одну числовую запись на каждый из методов A/B/C/D.
- [x] `docs/roadmap.md` обновлён: sprint-10 → Done, ссылка на final report.
- [x] Sprint `README.md` обновлён: Task 08 ✅, дата закрытия, итог Task 07–08.

### Пользователь проверяет

- [x] Вердикт даёт конкретную рекомендацию с числами (не «все методы по-своему хороши») — 2026-07-11.
- [x] Антипаттерны перечислены явно — 2026-07-11.

---

## Артефакты

| Путь | Описание |
|---|---|
| `evals/reports/multimodal-final.md` | Сводная матрица + decision log + вердикт + антипаттерны |
| `docs/roadmap.md` | sprint-10 → Done |
| `docs/sprints/sprint-10-multimodal-rag/README.md` | Статус, итог спринта |
| `docs/sprints/sprint-10-multimodal-rag/tasks/08-matrix-report-verdict/plan.md` | Этот план |
| `docs/sprints/sprint-10-multimodal-rag/tasks/08-matrix-report-verdict/summary.md` | Итог задачи (2026-07-11) |

---

## Scope

**В scope:** документация, синтез готовых отчётов Task 02–07.

**Вне scope:** новый код, повторные eval-прогоны, ADR (опционально, не в DoD).
