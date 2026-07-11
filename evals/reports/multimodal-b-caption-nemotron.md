# Multimodal RAG — naive text baseline (Task 03)

> **Дата:** 2026-07-10 · **config:** `multimodal-b-caption-nemotron`
> **Спринт:** [sprint-10-multimodal-rag](../../docs/sprints/sprint-10-multimodal-rag/README.md)
> **Metric map:** [metric_map.md](../../docs/sprints/sprint-10-multimodal-rag/metric_map.md)

---

## Конфигурация

| Параметр | Значение |
|---|---|
| collection | `multimodal_caption_nemotron_v002` |
| embedding | `intfloat/multilingual-e5-base` (dim=768) |
| top_k | 5 |
| corpus_dir (input) | `data\multimodal-rag` |
| artifact_dir (output) | `evals\artifacts\captions\nemotron-nano-12b-v2-vl` |
| PDF text pages non-empty | 66/66 |
| indexed slides | 66 |
| build_time_s | 46.92 |
| est_cost_usd | 0.01 |

## Ingestion failure examples (chart slides)

Гипотеза: naive PDF text layer не извлекает числа с chart-слайдов → retrieval слеп.

| Слайд | Число на PNG | PDF chars | Item | Recall@5 |
|---:|---|---:|---|---:|
| 10 | 72% (Zapier) | 0 | S2-9 | 1.000 ⚠️ шум |
| 11 | 70% документооборот, 39% заголовок | 0 | S2-1 | шум (Recall=1.0 случайно, rank 3) |
| 9 | ~45% Epoch AI 2026 | 0 | S2-3 | 1.000 ⚠️ шум |

S2_chart aggregate Recall@5 = 1.000 — **шум** пустого индекса, не сигнал качества.

## Retrieval по сегментам (primary)

> ⚠️ Не использовать macro-average по корпусу для решений — только строки таблицы.

| Сегмент | n | Recall@k | nDCG@5 | MRR | Set-Recall@k | trap_in_topk (S5 diag) |
|---|---:|---:|---:|---:|---:|---:|
| S1_text | 7 | 0.857 | 0.776 | 0.750 | — | — |
| S2_chart | 9 | 1.000 | 1.000 | 1.000 | — | — |
| S3_layout | 10 | 0.700 | 0.663 | 0.650 | — | — |
| S4_multi | 6 | 1.000 | 0.876 | 0.917 | 0.883 | — |
| S5_unanswerable | 6 | 0.000 | 0.000 | 0.000 | — | 0.833 |

## Интерпретация

- PDF text layer: **66** из 66 страниц с текстом — naive baseline индексирует пустые passage; метрики отражают «слепоту» без OCR/caption.
- **S5:** primary metric = `correct_refusal_rate` (generation); `trap_slide_in_topk` — только retrieval-диагностика.

## Ingestion / Generation

- **CER / TEDS** — не применимы к baseline (Task 04 / Task 07).
- **Generation** — не прогонялся (retrieval-only).

---

Детали: `evals/reports/runs/multimodal-baseline-20260710T202454Z.json`
