# Multimodal RAG — method B Caption (Task 05)

> **Дата:** 2026-07-10
> **Спринт:** [sprint-10-multimodal-rag](../../docs/sprints/sprint-10-multimodal-rag/README.md)
> **Metric map:** [metric_map.md](../../docs/sprints/sprint-10-multimodal-rag/metric_map.md)

---

## Конфигурация

| Модель | model_id | Pre-flight | Коллекция | artifact_dir |
|---|---|---|---|---|
| nemotron | `nvidia/nemotron-nano-12b-v2-vl:free` | FOUND | `multimodal_caption_nemotron_v002` | `evals\artifacts\captions\nemotron-nano-12b-v2-vl` |
| gemini | `google/gemini-2.5-flash-lite` | FOUND | `multimodal_caption_gemini_v002` | `evals\artifacts\captions\gemini-2.5-flash-lite` |

Промпт: русский, дословное извлечение чисел, temperature=0.
Embedding: `intfloat/multilingual-e5-base` (768d, local, $0).
- **Nemotron rate limit:** slides 50–66 через fallback `qwen/qwen3-vl-8b-instruct` (17 artifacts, причина: `rate_limit_429_free_tier`).

## Hallucination-check (S2 slides 10–11)

Детали: `evals/artifacts/captions/hallucination-check.md`

| Слайд | Модель | Вердикт |
|---:|---|---|
| 10 | nemotron | **совпадает** |
| 10 | gemini | **совпадает** |
| 11 | nemotron | **совпадает** |
| 11 | gemini | **совпадает** |

## Retrieval по сегментам

### nemotron

| Сегмент | n | Recall@k | nDCG@5 | MRR | Set-Recall@k | trap_in_topk |
|---|---:|---:|---:|---:|---:|---:|
| S1_text | 7 | 0.857 | 0.776 | 0.750 | — | — |
| S2_chart | 9 | 1.000 | 1.000 | 1.000 | — | — |
| S3_layout | 10 | 0.700 | 0.663 | 0.650 | — | — |
| S4_multi | 6 | 1.000 | 0.876 | 0.917 | 0.883 | — |
| S5_unanswerable | 6 | 0.000 | 0.000 | 0.000 | — | 0.833 |

### gemini

| Сегмент | n | Recall@k | nDCG@5 | MRR | Set-Recall@k | trap_in_topk |
|---|---:|---:|---:|---:|---:|---:|
| S1_text | 7 | 0.714 | 0.714 | 0.714 | — | — |
| S2_chart | 9 | 1.000 | 1.000 | 1.000 | — | — |
| S3_layout | 10 | 0.800 | 0.800 | 0.800 | — | — |
| S4_multi | 6 | 1.000 | 0.819 | 0.778 | 0.967 | — |
| S5_unanswerable | 6 | 0.000 | 0.000 | 0.000 | — | 1.000 |

## Время и стоимость

| Модель | build_time_s | caption_time_s | embed_time_s | index_size_mb | api_calls | est_cost_usd |
|---|---:|---:|---:|---:|---:|---:|
| nemotron | 606.29 | 509.07 | 97.22 | 0.193 | 66 | 0.006022 |
| gemini | 398.53 | 364.06 | 34.47 | 0.193 | 66 | 0.021415 |

Speed ratio (gemini/nemotron): **0.66×** (nemotron=606.3s, gemini=398.5s).

## Вывод

**Оправдывает ли мощная модель (gemini) прирост качества?** **Да** — по S2/S3:

- S2_chart: nemotron Recall@5=1.000 nDCG@5=1.000; gemini Recall@5=1.000 nDCG@5=1.000.
- S3_layout: nemotron Recall@5=0.700 nDCG@5=0.663; gemini Recall@5=0.800 nDCG@5=0.800.
- Стоимость индексации: nemotron=$0.006022, gemini=$0.021415.
- Скорость: gemini быстрее nemotron в 0.66× по build_time_s.
- Решение по сегментам, не macro-average по корпусу.

## Артефакты для ручной проверки

- Nemotron: `evals\artifacts\captions\nemotron-nano-12b-v2-vl`
- Gemini: `evals\artifacts\captions\gemini-2.5-flash-lite`
- Смотреть S2 (10–11) и S3 (15, 32) на адекватность подписей vs generic-описания.
