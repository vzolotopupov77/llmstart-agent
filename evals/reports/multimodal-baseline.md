# Multimodal RAG — naive text baseline (Task 03)

> **Дата:** 2026-07-05 · **config:** `multimodal-baseline`
> **Спринт:** [sprint-10-multimodal-rag](../../docs/sprints/sprint-10-multimodal-rag/README.md)
> **Metric map:** [metric_map.md](../../docs/sprints/sprint-10-multimodal-rag/metric_map.md)

---

## Конфигурация

| Параметр | Значение |
|---|---|
| collection | `multimodal_text_naive_v002` |
| embedding | `intfloat/multilingual-e5-base` (dim=768) |
| top_k | 5 |
| corpus_dir (input) | `data\multimodal-rag` |
| artifact_dir (output) | `evals\artifacts\corpus\text_naive` |
| PDF text pages non-empty | 0/66 |
| indexed slides | 66 |
| build_time_s | 21.50 |
| est_cost_usd | 0.00 |

## Ingestion failure examples (chart slides)

Гипотеза: naive PDF text layer не извлекает числа с chart-слайдов → retrieval слеп.

| Слайд | Число на PNG | PDF chars | Item | Recall@5 |
|---:|---|---:|---|---:|
| 10 | 72% (Zapier) | 0 | S2-9 | 0.000 |
| 11 | 70% документооборот, 39% заголовок | 0 | S2-1 | шум (Recall=1.0 случайно, rank 3) |
| 9 | ~45% Epoch AI 2026 | 0 | S2-3 | 0.000 |

S2_chart aggregate Recall@5 = 0.000 — **шум** пустого индекса, не сигнал качества.

## Retrieval по сегментам (primary)

> ⚠️ Не использовать macro-average по корпусу для решений — только строки таблицы.

| Сегмент | n | Recall@k | nDCG@5 | MRR | Set-Recall@k | trap_in_topk (S5 diag) |
|---|---:|---:|---:|---:|---:|---:|
| S1_text | 7 | 0.143 | 0.143 | 0.143 | — | — |
| S2_chart | 9 | 0.000 | 0.000 | 0.000 | — | — |
| S3_layout | 10 | 0.000 | 0.000 | 0.000 | — | — |
| S4_multi | 6 | 0.167 | 0.058 | 0.083 | 0.067 | — |
| S5_unanswerable | 6 | 0.000 | 0.000 | 0.000 | — | 0.167 |

## Интерпретация

- PDF text layer: **0** из 66 страниц с текстом — naive baseline индексирует пустые passage; метрики отражают «слепоту» без OCR/caption.
- **S5:** primary metric = `correct_refusal_rate` (generation); `trap_slide_in_topk` — только retrieval-диагностика.

## Ingestion / Generation

- **CER / TEDS** — не применимы к baseline (Task 04 / Task 07).
- **Generation** — не прогонялся (retrieval-only).

---

Детали: `evals/reports/runs/multimodal-baseline-20260705T161917Z.json`
