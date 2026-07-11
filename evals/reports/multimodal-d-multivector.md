# Multimodal RAG — method D Multivector (Task 07)

> **Дата:** 2026-07-11
> **Спринт:** [sprint-10-multimodal-rag](../../docs/sprints/sprint-10-multimodal-rag/README.md)
> **Metric map:** [metric_map.md](../../docs/sprints/sprint-10-multimodal-rag/metric_map.md)

---

## Конфигурация

| Параметр | Значение |
|---|---|
| model_id | `jina-embeddings-v4` |
| token_dim | 128 |
| smoke vectors (slide-01) | 751 |
| d_max_side | 1024 |
| collection | `multimodal_multivector_jina_v002` |
| corpus_dir | `data\multimodal-rag` |

Index: PNG → Jina v4 multivector (`return_multivector=true`) → Qdrant MAX_SIM.
Query: Jina v4 text multivector (`task=retrieval.query`).

## Retrieval D по сегментам

| Сегмент | n | Recall@k | nDCG@5 | MRR | Set-Recall@k | trap_in_topk |
|---|---:|---:|---:|---:|---:|---:|
| S1_text | 7 | 1.000 | 1.000 | 1.000 | — | — |
| S2_chart | 9 | 1.000 | 1.000 | 1.000 | — | — |
| S3_layout | 10 | 0.900 | 0.900 | 0.900 | — | — |
| S4_multi | 6 | 1.000 | 0.831 | 0.875 | 0.850 | — |
| S5_unanswerable | 6 | 0.000 | 0.000 | 0.000 | — | 0.833 |

## D vs C по сегментам

C reference: [multimodal-c-unified.md](multimodal-c-unified.md) (Task 06, 2026-07-11).

| Сегмент | D Recall@5 | D nDCG@5 | C R/nDCG | Δ Recall (D−C) |
|---|---:|---:|---|---:|
| S1_text | 1.000 | 1.000 | 1.000/1.000 | +0.000 |
| S2_chart | 1.000 | 1.000 | 1.000/1.000 | +0.000 |
| S3_layout | 0.900 | 0.900 | 0.900/0.826 | +0.000 |
| S4_multi | 1.000 | 0.831 | 0.833/0.681 | +0.167 |
| S5_unanswerable | 0.000 | 0.000 | — | — |

## D vs best B по сегментам

B reference: [multimodal-b-caption.md](multimodal-b-caption.md) (Task 05, 2026-07-10).

| Сегмент | D Recall@5 | D nDCG@5 | best B R/nDCG | Δ Recall (D−best B) |
|---|---:|---:|---|---:|
| S1_text | 1.000 | 1.000 | 0.857/0.776 | +0.143 |
| S2_chart | 1.000 | 1.000 | 1.000/1.000 | +0.000 |
| S3_layout | 0.900 | 0.900 | 0.800/0.800 | +0.100 |
| S4_multi | 1.000 | 0.831 | 1.000/0.876 | +0.000 |
| S5_unanswerable | 0.000 | 0.000 | — | — |

## Время и стоимость

| Метод | build_time_s | embed_time_s | upsert_time_s | index_size_mb | total_tokens | api_calls | est_cost_usd |
|---|---:|---:|---:|---:|---:|---:|---:|
| D (multivector) | 631.11 | 487.14 | 143.96 | 24.202 | 49566 | 66 | 0.025641 |
| C (unified) | 207.37 | — | — | 0.516 | — | 66 | 0.000000 |
| B gemini | 398.53 | — | — | 0.193 | — | 66 | 0.021415 |
| A tesseract | 73.05 | — | — | — | — | 66 | 0.000000 |

### Мультипликаторы D относительно других методов

| Метрика | vs C | vs B gemini | vs A tesseract |
|---|---:|---:|---:|
| build_time_s | 3.04× | 1.58× | 8.64× |
| index_size_mb | 46.90× | 125.40× | — |
| est_cost_usd | — | 1.20× | — |

## TEDS (ingestion-quality, slides 10/11)

**Формула:** TEDS = 1 − TED(tree_ref, tree_hyp) / max(|tree_ref|, |tree_hyp|).
**Reference:** `evals/datasets/multimodal/teds-golden/v001_2026-07-11.json` (ручная HTML).
**Hypothesis:** VLM structure → `evals\artifacts\multivector\teds-hyp/slide-NN.html`.

| slide | segment | TEDS |
|---:|---|---:|
| 10 | S2_chart | 0.000 |
| 11 | S2_chart | 0.000 |
| **mean** | S2_chart | **0.000** |

## Гипотеза multivector на S2/S3

Гипотеза: late-interaction multivector (Jina v4) даёт прирост на chart/layout (S2/S3) относительно C и B, но цена index_size_mb / build_time_s / $ — максимальная.

**Вердикт: S2 без прироста, S3 без прироста.**

- D S2_chart: Recall@5=1.000 (C=1.000, best B=1.000)
- D S3_layout: Recall@5=0.900 (C=0.900, best B=0.800)
- D index_size_mb=24.202 vs C=0.516
- D build_time_s=631.11 vs C=207.37
- D est_cost_usd=0.025641

## Вывод

Multivector **не обогнал** C/B на S2/S3 при существенно большем `index_size_mb` — для этого корпуса цена multivector не оправдана retrieval-метриками.

Решение по сегментам, не macro-average. Сравнение с C: [multimodal-c-unified.md](multimodal-c-unified.md).
