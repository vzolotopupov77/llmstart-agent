# Multimodal RAG — финальный отчёт (Task 08)

> **Дата:** 2026-07-11
> **Спринт:** [sprint-10-multimodal-rag](../../docs/sprints/sprint-10-multimodal-rag/README.md)
> **Датасет:** `evals/datasets/multimodal/multimodal-rag/v002_2026-07-05.json` (38 items)
> **Metric map:** [metric_map.md](../../docs/sprints/sprint-10-multimodal-rag/metric_map.md)

---

## 1. Сводная матрица: конфигурация × сегмент

> Решения принимаются **по строкам сегментов**, не по macro-average по корпусу.

### 1.0 Полная таблица: качество × сегмент + ось цены

Primary retrieval-метрика на сегмент: **Recall@5** (S1–S3), **Set-Recall@5** (S4), **trap_in_topk** (S5, ↓ лучше). Справа — ось цены индексации.

| Конфигурация | S1_text R@5 | S2_chart R@5 | S3_layout R@5 | S4 Set-R@5 | S5 trap↓ | build_time_s | index_size_mb | est_cost_usd |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **baseline** | 0.143 | 0.000 | 0.000 | 0.067 | 0.167 | 21.5 | — | 0.000 |
| **A_tesseract** | 0.857 | 0.889 | 0.900 | 0.800 | 1.000 | 73.1 | — | 0.000 |
| **A_rapidocr** | 0.429 | 0.889 | 0.400 | 0.533 | 0.333 | 294.6 | — | 0.000 |
| **B_nemotron** | 0.857 | **1.000** | 0.700 | 0.883 | 0.833 | 606.3 | 0.193 | 0.006 |
| **B_gemini** | 0.714 | **1.000** | 0.800 | **0.967** | 1.000 | 398.5 | 0.193 | 0.021 |
| **C** | **1.000** | **1.000** | 0.900 | 0.650 | 0.833 | 207.4 | 0.516 | 0.000 |
| **D** | **1.000** | **1.000** | 0.900 | 0.850 | 0.833 | 631.1 | 24.202 | 0.026 |

**Лучший по сегменту (primary):** S1 — C/D (1.000); S2 — B/C/D (1.000); S3 — A_tesseract/C/D (0.900); S4 — B_gemini (0.967 Set-Recall); S5 — baseline (0.167 trap, generation не прогонялась).

**Ось цены (от дешёвого к дорогому по $):** baseline = A_tesseract (0.000) < B_nemotron (0.006) < B_gemini (0.021) < D (0.026). По `index_size_mb`: B ≈ 0.19 < C = 0.52 ≪ D = 24.2. По `build_time_s`: baseline (22s) < A_tesseract (73s) < C (207s) < B_gemini (399s) < B_nemotron (606s) < D (631s).

**Качество/цена (default C):** S1/S2 Recall@5=1.000 при $0 и 207s — лучший free-tier вариант. D даёт +0.167 Recall@5 на S4 vs C (1.000 vs 0.833), но цена ×46.9 по storage и ×3.0 по времени.

### 1.1 Retrieval по сегментам (детально)

> Формат ячейки: **nDCG@5 / Recall@5** (S1–S3), **Set-Recall@5** (S4), **trap_in_topk** (S5, retrieval-диагностика).

| Конфигурация | S1_text (n=7) | S2_chart (n=9) | S3_layout (n=10) | S4_multi (n=6) | S5 trap (n=6) |
|---|---|---|---|---|---|
| **baseline** (PDF text layer) | 0.143 / 0.143 | 0.000 / 0.000 | 0.000 / 0.000 | 0.067 | 0.167 |
| **A_tesseract** | 0.688 / 0.857 | 0.889 / 0.889 | 0.693 / 0.900 | 0.800 | 1.000 |
| **A_rapidocr** | 0.288 / 0.429 | 0.848 / 0.889 | 0.265 / 0.400 | 0.533 | 0.333 |
| **B_nemotron** | 0.776 / 0.857 | 1.000 / 1.000 | 0.663 / 0.700 | 0.883 | 0.833 |
| **B_gemini** | 0.714 / 0.714 | 1.000 / 1.000 | 0.800 / 0.800 | 0.967 | 1.000 |
| **C** (unified VL embed) | 1.000 / 1.000 | 1.000 / 1.000 | 0.826 / 0.900 | 0.650 | 0.833 |
| **D** (Jina multivector) | 1.000 / 1.000 | 1.000 / 1.000 | 0.900 / 0.900 | 0.850 | 0.833 |

S4: primary = Set-Recall@5. Recall@5 для справки: baseline 0.167, A_tesseract 0.833, A_rapidocr 0.667, B_nemotron 1.000, B_gemini 1.000, C 0.833, D 1.000.

S5: primary = `correct_refusal_rate` (generation) — **не прогонялась** в sprint-10 (retrieval-only). `trap_in_topk` — только диагностика: чем выше, тем чаще trap-слайд попадает в top-k (плохо для refusal).

### 1.2 Цена индексации

| Конфигурация | build_time_s | index_size_mb | est_cost_usd | Источник |
|---|---:|---:|---:|---|
| baseline | 21.50 | — | 0.000 | [baseline](multimodal-baseline.md) |
| A_tesseract | 73.05 | — | 0.000 | [a-ocr](multimodal-a-ocr.md) |
| A_rapidocr | 294.57 | — | 0.000 | [a-ocr](multimodal-a-ocr.md) |
| B_nemotron | 606.29 | 0.193 | 0.006 | [b-caption](multimodal-b-caption.md) |
| B_gemini | 398.53 | 0.193 | 0.021 | [b-caption](multimodal-b-caption.md) |
| C | 207.37 | 0.516 | 0.000 | [c-unified](multimodal-c-unified.md) |
| D | 631.11 | 24.202 | 0.026 | [d-multivector](multimodal-d-multivector.md) |

### 1.3 Ingestion-quality (диагностика, не retrieval-скор)

| Метрика | Значение | Конфигурация | Источник |
|---|---|---|---|
| CER mean | 0.600 | A_tesseract | [a-ocr](multimodal-a-ocr.md) |
| CER mean | 0.850 | A_rapidocr | [a-ocr](multimodal-a-ocr.md) |
| TEDS mean (slides 10/11) | 0.000 | D (hyp-pipeline) | [d-multivector](multimodal-d-multivector.md) |
| Hallucination-check slides 10/11 | совпадает (обе VLM) | B_nemotron, B_gemini | [hallucination-check](../artifacts/captions/hallucination-check.md) |

---

## 2. Decision log

### Метод A (OCR → e5)

**Что сравнивали:** Tesseract (docker, `rus+eng`, PSM 6) vs RapidOCR (local ONNX).

| Критерий | Tesseract | RapidOCR | Δ |
|---|---:|---:|---|
| CER mean (10 слайдов) | 0.600 | 0.850 | −0.250 (лучше Tesseract) |
| S1 Recall@5 | 0.857 | 0.429 | +0.428 |
| S3 Recall@5 | 0.900 | 0.400 | +0.500 |
| build_time_s | 73 | 295 | 4.0× быстрее Tesseract |

**Вердикт A:** Tesseract — победитель на этом корпусе. RapidOCR проигрывает на S1/S3 при сопоставимом S2 (0.889 vs 0.889). EasyOCR не использован (docker build blocked).

**Сегментный выигрыш:** S1 (+0.428 Recall), S3 (+0.500 Recall). S2 — паритет.

---

### Метод B (VLM caption → e5)

**Что сравнивали:** `nvidia/nemotron-nano-12b-v2-vl:free` vs `google/gemini-2.5-flash-lite`.

| Критерий | Nemotron | Gemini | Δ |
|---|---:|---:|---|
| S2 Recall@5 | 1.000 | 1.000 | 0.000 (паритет) |
| S3 Recall@5 | 0.700 | 0.800 | +0.100 (лучше Gemini) |
| S4 Set-Recall@5 | 0.883 | 0.967 | +0.084 (лучше Gemini) |
| build_time_s | 606 | 399 | Gemini 0.66× быстрее |
| est_cost_usd | 0.006 | 0.021 | Gemini 3.5× дороже |

**Вердикт B:** Gemini **оправдывает** прирост на S3 (Recall@5 0.800 vs 0.700) при паритете на S2 (1.000). Hallucination-check slides 10/11 — **совпадает** у обеих моделей. Nemotron slides 50–66 — fallback `qwen/qwen3-vl-8b-instruct` (rate limit free tier).

**Сегментный выигрыш Gemini:** S3 (+0.100 Recall), S4 Set-Recall (+0.084).

---

### Метод C (unified VL image-embed)

**Что сравнивали:** `nvidia/llama-nemotron-embed-vl-1b-v2:free` (2048d) vs лучший B (nemotron на S1, gemini на S3).

| Критерий | C | best B | Δ (C − best B) |
|---|---:|---:|---:|
| S1 Recall@5 | 1.000 | 0.857 (nemotron) | +0.143 |
| S2 Recall@5 | 1.000 | 1.000 | 0.000 |
| S3 Recall@5 | 0.900 | 0.800 (gemini) | +0.100 |
| S4 Recall@5 | 0.833 | 1.000 (nemotron/gemini) | −0.167 |
| build_time_s | 207 | 399 (gemini) | 0.52× быстрее |
| est_cost_usd | 0.000 | 0.021 (gemini) | бесплатно |

**Гипотеза MIRACL-Vision / русский S1:** опровергнута. C S1 Recall@5=1.000 vs best B=0.857.

**Вердикт C:** C обгоняет или равен best B на S1/S2/S3. Единственная просадка — S4 (−0.167 Recall vs B). Стоимость индексации $0 (free-tier OpenRouter).

**Сегментный выигрыш:** S1 (+0.143), S3 (+0.100). **Проигрыш:** S4 (−0.167).

---

### Метод D (Jina v4 multivector, MAX_SIM)

**Что сравнивали:** `jina-embeddings-v4` (token_dim 128) vs C и best B.

| Критерий | D | C | best B | Δ (D − C) | Δ (D − best B) |
|---|---:|---:|---:|---:|---:|
| S2 Recall@5 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 |
| S3 Recall@5 | 0.900 | 0.900 | 0.800 | 0.000 | +0.100 |
| S4 Recall@5 | 1.000 | 0.833 | 1.000 | +0.167 | 0.000 |
| index_size_mb | 24.202 | 0.516 | 0.193 | 46.9× | 125.4× |
| build_time_s | 631 | 207 | 399 | 3.0× | 1.6× |
| est_cost_usd | 0.026 | 0.000 | 0.021 | — | 1.2× |

**Гипотеза multivector на S2/S3:** не подтверждена — паритет с C на S2 (1.000) и S3 (0.900).

**TEDS slides 10/11:** 0.000 (диагностика hyp-pipeline, не retrieval).

**Вердикт D:** единственный явный retrieval-прирост над C — **S4 Recall@5 +0.167** (1.000 vs 0.833). Цена: index_size_mb ×46.9 vs C, build_time ×3.0, $0.026 vs $0. Multivector **не оправдан** для S2/S3 на этом корпусе.

**Сегментный выигрыш:** S4 (+0.167 vs C). S2/S3 — паритет с C.

---

## 3. Вердикт

### Рекомендуемая точка спектра для корпуса llmstart B2B-презентации (66 PNG, text-in-image)

| Сегмент | Лучший метод | Recall@5 / Set-Recall@5 | Цена (build / size / $) |
|---|---|---|---|
| S1_text | **C** | 1.000 | 207s / 0.516mb / $0 |
| S2_chart | **C** (= B, D) | 1.000 | 207s / 0.516mb / $0 |
| S3_layout | **C** (= D) | 0.900 | 207s / 0.516mb / $0 |
| S4_multi | **D** (= B) | 1.000 Recall / 0.850 Set-Recall | 631s / 24.2mb / $0.026 |
| S5 | — | generation не прогонялась | — |

### Итоговая рекомендация

**Default: метод C** (`nvidia/llama-nemotron-embed-vl-1b-v2:free`).

- Максимальный Recall@5 на S1 (1.000) и S2 (1.000), S3=0.900.
- Бесплатная индексация ($0), build=207s, index=0.516mb.
- Гипотеза просадки на русском тексте — **опровергнута** (+0.143 vs best B на S1).

**Upgrade на S4:** метод D — только если multi-hop вопросы (S4) критичны для продукта.

- Прирост над C: Recall@5 +0.167 (1.000 vs 0.833).
- Цена: index_size_mb ×46.9, build_time ×3.0, $0.026 за прогон.
- На S2/S3 прироста нет — multivector не оправдан «по умолчанию».

**Degraded fallback (нет VL image-embed API):** метод B, модель **gemini-2.5-flash-lite**.

- S2=1.000, S3=0.800 (лучше nemotron на +0.100), build=399s, $0.021.
- Hallucination-check на chart-слайдах 10/11 — числа совпадают.

**Offline fallback (нет API вообще):** метод A, движок **Tesseract**.

- S1=0.857, S2=0.889, build=73s, $0, CER=0.600.
- Без GPU, docker-ready.

**Baseline (PDF text layer):** неприменим — 0/66 страниц с текстом, S2/S3/S4 ≈ 0.

### Комбинация по сегментам (если routing доступен)

```
S1, S2, S3 → C (unified VL embed)
S4         → D (multivector) — только при бизнес-требовании multi-hop
fallback   → B_gemini → A_tesseract
```

---

## 4. Антипаттерны

| # | Антипаттерн | Статус в sprint-10 |
|---|---|---|
| 1 | **ColPali ради ColPali** — multivector по умолчанию без числового обоснования | Избежали: D прогнан последним; вердикт — не default, только S4-upgrade |
| 2 | **Среднее по больнице** — решение на macro-average по корпусу | Избежали: все decision log записи по строкам S1–S5 |
| 3 | **CER на глаз** — субъективная оценка OCR без формулы | Избежали: Levenshtein/ref_len, 10-slide golden, артефакты в `evals/artifacts/ocr/` |
| 4 | **Молчаливая правка чисел у B** — VLM подменяет цифры без проверки | Избежали: `hallucination-check.md` на slides 10/11, вердикт «совпадает» |
| 5 | **TEDS=0.000 без контекста** — нулевой TEDS трактуется как «плохой метод» | Зафиксирован как диагностика hyp-pipeline (VLM→HTML), не retrieval-метрика |
| 6 | **PDF text layer как ground truth** — naive baseline как «норма» | Избежали: 0/66 non-empty зафиксировано, baseline = контроль слепоты |

---

## 5. Ссылки на отчёты Task 02–07

| Task | Отчёт |
|---|---|
| 02 baseline | [multimodal-baseline.md](multimodal-baseline.md) |
| 04 method A | [multimodal-a-ocr.md](multimodal-a-ocr.md) |
| 05 method B | [multimodal-b-caption.md](multimodal-b-caption.md) |
| 06 method C | [multimodal-c-unified.md](multimodal-c-unified.md) |
| 07 method D | [multimodal-d-multivector.md](multimodal-d-multivector.md) |
