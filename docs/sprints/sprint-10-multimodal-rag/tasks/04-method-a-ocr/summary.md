# Summary: Task 04 — method-a-ocr

> **План:** [plan.md](./plan.md)
> **Дата закрытия:** 2026-07-05

---

## Что реализовано

- `AOcrIndexer` (OCR → `evals/artifacts/ocr/{engine}/` → e5 → Qdrant) через контракт Task 03
- Два движка: **Tesseract** (docker) и **RapidOCR ONNX** (local host)
- Golden CER set: 10 PNG-verified ref-текстов + manifest `ocr-cer-golden/v001_2026-07-05.json`
- `ocr_cer.py` — CER по формуле `Levenshtein/len(ref)`, без clamp при >100%
- Docker OCR: Tesseract image + compose; batch runner + `ocr_docker.py`
- Конфиги `multimodal-a-ocr-tesseract.yaml`, `multimodal-a-ocr-modern.yaml` с `ocr_runtime` per engine
- `run_multimodal_a_ocr.py` — index/eval обоих движков + сводный отчёт
- Артефакты: 66×2 `.txt`; Qdrant: `multimodal_ocr_tesseract_v002`, `multimodal_ocr_modern_v002`
- Отчёт: `evals/reports/multimodal-a-ocr.md`

---

## Принятые решения

| Решение | Причина |
|---------|---------|
| Tesseract PSM=6, `lang=rus+eng` | Лучше block-текст на слайдах vs auto (3) |
| Adaptive invert при mean luminance < 128 | Тёмная тема корпуса без invert-all |
| RapidOCR вместо EasyOCR | EasyOCR docker build падает на PyPI (torch/sympy/pillow); RapidOCR — ONNX CPU fallback из plan |
| `ocr_runtime` в YAML: tesseract=docker, rapidocr=local | RapidOCR docker тоже не собрался; local ONNX на host работает |
| CER refs — PNG-verified, не `notes.md` | Speaker notes не в eval scope |
| `dependency-groups.ocr-modern` в pyproject | RapidOCR deps не тянутся в baseline eval |

---

## Отклонения от плана

- **EasyOCR не прогнан:** docker build blocked (PyPI network/timeout). Modern engine = RapidOCR.
- **Артефакты в `evals/artifacts/ocr/rapidocr/`**, не `easyocr/` — соответствует фактическому движку.
- **Hybrid runtime** вместо единого `OCR_RUNTIME=docker`: зафиксировано в YAML + отчёте.

---

## Итог DoD

| # | Критерий | Результат |
|---|----------|-----------|
| 1 | CER по формуле на 10 слайдах; формула в отчёте | ✅ mean tesseract=0.600, rapidocr=0.850 |
| 2 | Оба движка: 66 artifacts + Qdrant + eval 5 сегментов | ✅ |
| 3 | `build_time_s`, `est_cost_usd` зафиксированы | ✅ 73.05s / 294.57s, cost=0 |
| 4 | Вывод «какой лучше на русском» с числами | ✅ **Tesseract** (CER + S1 retrieval; S2 паритет 0.889) |
| 5 | Артефакты читаемы для ручной проверки | ✅ `evals/artifacts/ocr/tesseract/`, `…/rapidocr/` |
| 6 | `mcp_server/` не менялся | ✅ `git diff --stat mcp_server/` пуст |
| 7 | Lint + тесты evals | ✅ 16 OCR-related tests passed |

---

## Ключевые метрики (из отчёта)

| | CER mean | S1 Recall@5 | S2 Recall@5 |
|---|---:|---:|---:|
| tesseract | 0.600 | 0.857 | 0.889 |
| rapidocr | 0.850 | 0.429 | 0.889 |

**Вывод:** Tesseract лучше читает пиксели (CER) и лучше ищет по текстовым вопросам (S1); на chart-слайдах (S2) retrieval одинаков.

---

## Запуск

```bash
make ocr-build                    # Tesseract image
make eval-multimodal-a-ocr        # uv sync --group ocr-modern + full pipeline
```

Per-engine (уже прогнано):

```bash
make eval-multimodal CONFIG=configs/multimodal-a-ocr-tesseract.yaml
make eval-multimodal CONFIG=configs/multimodal-a-ocr-modern.yaml
```

---

## Артефакты

| Путь | Описание |
|------|----------|
| `evals/reports/multimodal-a-ocr.md` | Сводный отчёт |
| `evals/datasets/multimodal/ocr-cer-golden/` | CER golden set |
| `evals/indexers/a_ocr.py`, `evals/indexers/ocr/` | Индексатор + OCR adapters |
| `devops/docker-compose.ocr.yml` | Docker OCR batch |
