# Multimodal RAG — method A OCR (Task 04)

> **Дата:** 2026-07-05
> **Спринт:** [sprint-10-multimodal-rag](../../docs/sprints/sprint-10-multimodal-rag/README.md)
> **Metric map:** [metric_map.md](../../docs/sprints/sprint-10-multimodal-rag/metric_map.md)

---

## Конфигурация

| Движок | OCR | Коллекция | artifact_dir |
|---|---|---|---|
| tesseract | tesseract | `multimodal_ocr_tesseract_v002` | `evals\artifacts\ocr\tesseract` |
| rapidocr | rapidocr | `multimodal_ocr_modern_v002` | `evals\artifacts\ocr\rapidocr` |

Pre-process: adaptive invert if mean luminance < 128, contrast ×1.5.
Tesseract: `lang=rus+eng`, `psm=6`. Modern: RapidOCR ONNX (`rapidocr-onnxruntime`).
Runtime: tesseract=`docker`, rapidocr=`local` (EasyOCR/RapidOCR docker blocked by PyPI in build).

## CER (ingestion-quality)

**Формула:** `CER = Levenshtein(ref, hyp) / len(ref)` после normalize (lowercase, collapse whitespace; punctuation и `%` сохраняются).
**Выборка (10 слайдов):** 2, 6, 37, 45, 9, 10, 11, 44, 49, 15.
CER > 1.0 возможен при галлюцинации символов — не clamp.

**tesseract:** mean=0.600, median=0.585
**rapidocr:** mean=0.850, median=0.878

| slide | segment | tesseract | rapidocr |
|---:|---|---:|---:|
| 2 | S1_text | 0.333 | 0.503 |
| 6 | S1_text | 1.084 | 0.993 |
| 37 | S1_text | 0.389 | 0.873 |
| 45 | S1_text | 0.603 | 0.925 |
| 9 | S2_chart | 0.414 | 0.878 |
| 10 | S2_chart | 0.651 | 0.884 |
| 11 | S2_chart | 0.566 | 0.823 |
| 44 | S2_chart | 0.705 | 0.879 |
| 49 | S2_chart | 0.695 | 0.883 |
| 15 | S3_layout | 0.559 | 0.861 |

## Retrieval по сегментам

### tesseract

| Сегмент | n | Recall@k | nDCG@5 | MRR | Set-Recall@k | trap_in_topk |
|---|---:|---:|---:|---:|---:|---:|
| S1_text | 7 | 0.857 | 0.688 | 0.636 | — | — |
| S2_chart | 9 | 0.889 | 0.889 | 0.889 | — | — |
| S3_layout | 10 | 0.900 | 0.693 | 0.625 | — | — |
| S4_multi | 6 | 0.833 | 0.714 | 0.722 | 0.800 | — |
| S5_unanswerable | 6 | 0.000 | 0.000 | 0.000 | — | 1.000 |

### rapidocr

| Сегмент | n | Recall@k | nDCG@5 | MRR | Set-Recall@k | trap_in_topk |
|---|---:|---:|---:|---:|---:|---:|
| S1_text | 7 | 0.429 | 0.288 | 0.243 | — | — |
| S2_chart | 9 | 0.889 | 0.848 | 0.833 | — | — |
| S3_layout | 10 | 0.400 | 0.265 | 0.220 | — | — |
| S4_multi | 6 | 0.667 | 0.474 | 0.500 | 0.533 | — |
| S5_unanswerable | 6 | 0.000 | 0.000 | 0.000 | — | 0.333 |

## Время и стоимость

| Движок | build_time_s | index_size_mb | est_cost_usd |
|---|---:|---:|---:|
| tesseract | 73.05 | — | 0.00 |
| rapidocr | 294.57 | — | 0.00 |

## Вывод

Modern engine: **RapidOCR (ONNX)** — EasyOCR docker build blocked by PyPI network errors in this environment; RapidOCR per plan fallback.

- **Ingestion (CER mean):** `tesseract` (tesseract=0.600, rapidocr=0.850).
- **Retrieval (S1+S2 Recall@5):** `tesseract` (tesseract S1=0.857 S2=0.889; rapidocr S1=0.429 S2=0.889).
- Решение по сегментам, не macro-average по корпусу.

## Типичные ошибки (ручная проверка)

- Tesseract: `evals\artifacts\ocr\tesseract`
- RapidOCR: `evals\artifacts\ocr\rapidocr`
- Смотреть кириллицу, разрывы строк, chart-слайды 9–11 на тёмном фоне.
