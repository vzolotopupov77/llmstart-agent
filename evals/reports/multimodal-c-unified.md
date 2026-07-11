# Multimodal RAG — method C Unified Embed (Task 06)

> **Дата:** 2026-07-11
> **Спринт:** [sprint-10-multimodal-rag](../../docs/sprints/sprint-10-multimodal-rag/README.md)
> **Metric map:** [metric_map.md](../../docs/sprints/sprint-10-multimodal-rag/metric_map.md)

---

## Конфигурация

| Параметр | Значение |
|---|---|
| model_id | `nvidia/llama-nemotron-embed-vl-1b-v2:free` |
| Pre-flight | SMOKE_OK_NOT_IN_CATALOG |
| embedding_dim (smoke) | 2048 |
| collection | `multimodal_unified_vl_v002` |
| corpus_dir | `data\multimodal-rag` |

Index: PNG → VL image embed (без промежуточного текста).
Query: VL text embed (та же модель).

## Retrieval C по сегментам

| Сегмент | n | Recall@k | nDCG@5 | MRR | Set-Recall@k | trap_in_topk |
|---|---:|---:|---:|---:|---:|---:|
| S1_text | 7 | 1.000 | 1.000 | 1.000 | — | — |
| S2_chart | 9 | 1.000 | 1.000 | 1.000 | — | — |
| S3_layout | 10 | 0.900 | 0.826 | 0.800 | — | — |
| S4_multi | 6 | 0.833 | 0.681 | 0.833 | 0.650 | — |
| S5_unanswerable | 6 | 0.000 | 0.000 | 0.000 | — | 0.833 |

## C vs B по сегментам

B reference: [multimodal-b-caption.md](multimodal-b-caption.md) (Task 05, 2026-07-10).

| Сегмент | C Recall@5 | C nDCG@5 | B_nemotron R/nDCG | B_gemini R/nDCG | best B R/nDCG | Δ Recall (C−best B) |
|---|---:|---:|---|---|---:|---:|
| S1_text | 1.000 | 1.000 | 0.857/0.776 | 0.714/0.714 | 0.857/0.776 | +0.143 |
| S2_chart | 1.000 | 1.000 | 1.000/1.000 | 1.000/1.000 | 1.000/1.000 | +0.000 |
| S3_layout | 0.900 | 0.826 | 0.700/0.663 | 0.800/0.800 | 0.800/0.800 | +0.100 |
| S4_multi | 0.833 | 0.681 | 1.000/0.876 | 1.000/0.819 | 1.000/0.876 | -0.167 |
| S5_unanswerable | 0.000 | 0.000 | — | — | — | — |

## Время и стоимость

| Метод | build_time_s | embed_time_s | upsert_time_s | index_size_mb | api_calls | est_cost_usd |
|---|---:|---:|---:|---:|---:|---:|
| C (unified) | 207.37 | 200.77 | 6.59 | 0.516 | 66 | 0.000000 |
| B nemotron | 606.29 | — | — | 0.193 | 66 | 0.006022 |
| B gemini | 398.53 | — | — | 0.193 | 66 | 0.021415 |

## Гипотеза MIRACL-Vision / русский S1

Гипотеза: unified image-embedder проседает на плотном кириллическом S1 (слайды 2, 8, 13 — см. analysis.md) относительно B (caption + e5).

**Вердикт: опровергнута.**

- C S1_text: Recall@5=1.000, nDCG@5=1.000 (n=7)
- B nemotron S1: Recall@5=0.857, nDCG@5=0.776
- B gemini S1: Recall@5=0.714, nDCG@5=0.714
- best B S1: Recall@5=0.857, nDCG@5=0.776
- Δ Recall@5 (C − best B): +0.143
- Δ nDCG@5 (C − best B): +0.224

## Вывод

Метод C **обгоняет или равен** лучшему B на S1_text (C 1.000 vs best B 0.857 Recall@5). Гипотеза просадки на русском для этого корпуса не подтвердилась.

Решение по сегментам, не macro-average. Сравнение с B: [multimodal-b-caption.md](multimodal-b-caption.md).
