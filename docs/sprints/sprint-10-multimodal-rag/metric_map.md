# Metric map — Sprint 10 Multimodal RAG

> **Датасет:** `evals/datasets/multimodal/multimodal-rag/v002_2026-07-05.json` (38 items)  
> **Baseline config:** `evals/configs/multimodal-baseline.yaml`  
> **Методология:** [.methodology/eval/metrics-guide.md](../../../.methodology/eval/metrics-guide.md)

Три **независимые** группы метрик. Не смешивать в одном скоре.

---

## 1. Retrieval по сегментам (primary для сравнения методов A–D)

Измеряем только ранжирование слайдов в top-k. Эталон — `required_slides` из датасета (сверены с PNG).

| Сегмент | Метрики | Формула / правило |
|---------|---------|-------------------|
| **S1_text**, **S2_chart**, **S3_layout** | Recall@k, nDCG@5, MRR | **Recall@k** = 1, если любой `required_slides` ∈ top-k, иначе 0. **MRR** = 1/rank первого релевантного слайда (0 если нет). **nDCG@5** = DCG@5 / IDCG@5; релевантность бинарная по `required_slides`. |
| **S4_multi** | Set-Recall@k | \|`required_slides` ∩ top-k\| / \|`required_slides`\|. Для однослайдовых S4 (43, 41, 51) = Recall@k. |
| **S5_unanswerable** | ⚠️ **не nDCG** | Retrieval-диагностика: `trap_slide_in_topk` по полю **`trap_slides`** (v002; v001 — legacy `required_slides`). **Primary S5 — группа 3.** |

**Параметры baseline:** k=5, эмбеддер `intfloat/multilingual-e5-base` (768d), префиксы E5: `query: …` / `passage: …`.

**Агрегация:** среднее **по сегменту**, не по корпусу. Общий macro-average — только вспомогательный, не для decision log.

**Ожидания baseline (пустой PDF text layer):** S1 ≈ 0; S2/S3/S4 ≈ 0; S5 trap_slide_in_topk ≈ random (~k/66).

---

## 2. Ingestion-quality (диагностика, не входит в retrieval-скор)

| Метрика | Метод | Когда | Формула |
|---------|-------|-------|---------|
| **CER** | A (OCR) | Task 04 | Levenshtein(ref, hyp) / len(ref); ref — ручная транскрипция ~10 слайдов (mix S1/S2) |
| **TEDS** | D (multivector) | Task 07 | Tree Edit Distance based Similarity для табличных слайдов **10, 11**; эталон — ручная HTML/JSON-разметка структуры |

Эти метрики **не суммируются** с Recall/nDCG и не участвуют в матрице «конфигурация × сегмент» Task 08 как retrieval-скор.

---

## 3. Generation (опционально) + время/стоимость

### Generation (опц.)

| Метрика | Сегменты | Слой | Описание |
|---------|----------|------|----------|
| `answer_correctness` | S1–S4 | generation | GEval по `reference_answer` / `required_facts` |
| **`correct_refusal_rate`** | **S5** | **behavior** | Доля ответов, где модель **отказалась выдумывать** (явный отказ + нет `must_not_invent` в тексте). **Не nDCG, не Recall.** |
| `faithfulness` | S1–S4 | guard | RAGAS Faithfulness к retrieved-контексту |

**S5 — поведение:** успех = «в корпусе нет данных» / «не указано», без подстановки числа/названия. Провал = выдуманный ROI, цена Cursor, названия пилотов и т.п.

Task 02 baseline — **retrieval-only**; generation-группа подключается с Task 03+ (общий eval-контур).

### Время и стоимость (на конфигурацию)

| Поле | Описание |
|------|----------|
| `build_time_s` | Время `Indexer.build_index(corpus)` |
| `index_size_mb` | Фактический объём коллекции Qdrant |
| `est_cost_usd` | API-вызовы индексации (OCR/VLM/embed); baseline local e5 = **0** |

---

## Эмбеддер (pinned, общий baseline / A / B)

| Параметр | Значение |
|----------|----------|
| Model | `intfloat/multilingual-e5-base` |
| Revision | HuggingFace default snapshot (2026-07-05) |
| Dim | 768 |
| Query prefix | `query: ` |
| Passage prefix | `passage: ` |
| Runtime | `sentence-transformers` (CPU), Task 02 eval script |

Task 03 переносит выбор в `Indexer` / env; здесь зафиксирован для baseline-прогона.

---

## Связь с `docs/eval/metrics-map.md`

Секция `multimodal-rag/*` добавляется в глобальную карту после закрытия Task 02. До Task 08 north-star для multimodal — **Recall@5 / Set-Recall@5 по сегменту**, не macro-average.
