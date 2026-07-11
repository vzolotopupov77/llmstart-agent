# Eval — LLMStart Agent

> **Roadmap eval-трека:** [roadmap-eval.md](../roadmap-eval.md)  
> **Карта датасетов:** [dataset-map.md](dataset-map.md)  
> **Карта метрик:** [metrics-map.md](metrics-map.md)

---

## Sprint-10 Multimodal RAG ✅ (2026-07-11)

**Спринт:** [sprint-10-multimodal-rag](../sprints/sprint-10-multimodal-rag/README.md) · **Финальный отчёт:** [multimodal-final.md](../../evals/reports/multimodal-final.md)

**Вердикт:** метод **C** (unified VL embed) — default; **D** — S4-upgrade; **B_gemini** / **A_tesseract** — fallback.

| Артефакт | Описание |
|----------|----------|
| [multimodal-final.md](../../evals/reports/multimodal-final.md) | Матрица 7×5 + ось цены, decision log, вердикт, антипаттерны |
| [multimodal-baseline.md](../../evals/reports/multimodal-baseline.md) | Naive text baseline (PDF layer → e5 → Qdrant) |
| [multimodal-a-ocr.md](../../evals/reports/multimodal-a-ocr.md) | Method A: Tesseract vs RapidOCR + CER |
| [multimodal-b-caption.md](../../evals/reports/multimodal-b-caption.md) | Method B: Nemotron vs Gemini + hallucination-check |
| [multimodal-c-unified.md](../../evals/reports/multimodal-c-unified.md) | Method C: unified VL embed vs B |
| [multimodal-d-multivector.md](../../evals/reports/multimodal-d-multivector.md) | Method D: Jina multivector + TEDS |
| [metric_map.md (sprint-10)](../sprints/sprint-10-multimodal-rag/metric_map.md) | Три группы метрик: retrieval / ingestion-quality / generation |
| [v002 dataset](../../evals/datasets/multimodal/multimodal-rag/v002_2026-07-05.json) | 38 вопросов; S1–S4: `required_slides`, S5: `trap_slides` |

**Запуск:**

```bash
make eval-multimodal-baseline
make eval-multimodal-a-ocr
make eval-multimodal-b-caption
make eval-multimodal-c-unified
make eval-multimodal-d-multivector
# generic runner:
make eval-multimodal CONFIG=configs/multimodal-baseline.yaml
```

Конфиги: `evals/configs/multimodal-*.yaml` · артефакты ingestion: `evals/artifacts/{corpus,ocr,captions,multivector}/`
