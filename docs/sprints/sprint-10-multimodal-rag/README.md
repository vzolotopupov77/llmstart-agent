# Sprint 10: multimodal-rag

> **Версия roadmap:** v0.2
> **Roadmap:** [../../roadmap.md](../../roadmap.md)
> **Статус:** ✅ Done
> **Открыт:** 2026-07-05
> **Закрыт:** 2026-07-11

---

## Цель спринта

Добавить мультимодальную ногу к Qdrant-RAG для визуально-плотного B2B-корпуса (66 слайдов презентации, русский язык, тёмная тема, текст вшит в картинку) и ответить не «какой метод лучше в среднем», а **на каком сегменте вопросов какой метод индексации даёт прирост и какой ценой** (время индексации, объём хранения, $ за прогон).

Корпус: `data/multimodal-rag/slide-01.png … slide-66.png` + `slide-01.pdf` (66 стр., **text layer пуст** — текст вшит в PNG). Эталоны eval — **только с видимого содержимого слайдов**; speaker notes в eval не участвуют.

---

## Ограничения

- Вектор остаётся в **Qdrant**; новую векторную БД не добавляем.
- Параметризован **только этап индексации** (`Indexer.build_index`); Qdrant-поиск, реранк и eval-контур — общий код, без ответвлений «if method == …» в downstream-слое.
- Без GPU и self-host моделей: метод D — **Jina v4 multivector через API**, не ColPali/self-hosted vision-модели.
- Качество измеряется и сравнивается **строго по сегментам** (S1–S5), общий средний по корпусу — не аргумент в decision log.
- Ingestion-метрики (**CER**, **TEDS**) — отдельная диагностическая группа, не подмешиваются в retrieval-скор.
- Для каждой конфигурации фиксируются `build_time_s` и `est_cost_usd` — это часть результата, а не побочный лог.
- Артефакты OCR и caption сохраняются в файлы (`evals/artifacts/`) для ручной проверки — «на глаз, без файла» не считается.
- Метод A обязателен в двух OCR-движках, метод B — минимум в двух VLM (дешёвая + более дорогая/фронтирная).
- Антихайп: метод D не берётся по умолчанию — сначала проверяются B/C и делается вывод, оправдывает ли multivector цену; визуальные методы (C, D) проверяются именно на русском тексте (гипотеза просадки MIRACL-Vision).
- Модели и версии SDK фиксируются явно (не `latest`); текстовый эмбеддер для baseline/A/B — `intfloat/multilingual-e5-base` (768d, pinned; контракт в `evals/indexers/`, Task 03 ✅).
- Темы будущих спринтов (context-engineering, hybrid search, структурный PDF-чанкинг) не затрагиваются.

---

## DoD спринта

| # | Критерий | Способ проверки |
|---|----------|-----------------|
| 1 | ✅ Таксономия 5 сегментов (S1_text/S2_chart/S3_layout/S4_multi/S5_unanswerable) подтверждена ≥3 реальными слайдами на сегмент | `analysis.md` |
| 2 | ✅ Датасет покрывает все 5 сегментов с эталонами (`required_slides` / golden-answer) | `evals/datasets/multimodal/multimodal-rag/v002_2026-07-05.json` |
| 3 | ✅ Naive text-baseline прогнан, боль по сегментам зафиксирована (не общий средний) | `evals/reports/multimodal-baseline.md` |
| 4 | ✅ Contract `Indexer.build_index(corpus) -> IndexCost` и `INDEXER_REGISTRY`/`make_indexer(cfg)` реализованы; downstream-код (поиск/eval) не тронут | `git diff` на `mcp_server/` = 0; `tests/test_indexer_registry.py` зелёный |
| 5 | ✅ Метод A: два OCR-движка сравнены по CER и по сегментам | `evals/reports/multimodal-a-ocr.md`, `evals/artifacts/ocr/**` |
| 6 | ✅ Метод B: ≥2 VLM сравнены; проведена ручная проверка галлюцинаций на числах | `evals/reports/multimodal-b-caption.md`, `evals/artifacts/captions/hallucination-check.md` |
| 7 | ✅ Метод C: сравнение с B, гипотеза просадки на русском (MIRACL-Vision) явно подтверждена/опровергнута числами | `evals/reports/multimodal-c-unified.md` |
| 8 | ✅ Метод D: MultiVectorConfig (MAX_SIM) работает, `index_size_mb` и TEDS (слайды 10/11) зафиксированы | `evals/reports/multimodal-d-multivector.md` |
| 9 | ✅ Для всех 7 конфигураций (baseline + 2×A + 2×B + C + D) есть `build_time_s` и `est_cost_usd` | сводная таблица Task 08 |
| 10 | ✅ Сводный отчёт: матрица «конфигурация × сегмент», decision log, вердикт с числами, явный список антипаттернов | `evals/reports/multimodal-final.md` |
| 11 | ✅ Roadmap и этот README обновлены по закрытии спринта | `git diff docs/roadmap.md` |

---

## Задачи

| # | Задача | Статус | Plan | Summary |
|---|--------|--------|------|---------|
| 01 | [corpus-analysis](#task-01-corpus-analysis) | ✅ | [plan](tasks/01-corpus-analysis/plan.md) | [summary](tasks/01-corpus-analysis/summary.md) |
| 02 | [datasets-metrics-baseline](#task-02-datasets-metrics-baseline) | ✅ | [plan](tasks/02-datasets-metrics-baseline/plan.md) | [summary](tasks/02-datasets-metrics-baseline/summary.md) |
| 03 | [indexer-contract-configs](#task-03-indexer-contract-configs) | ✅ | [plan](tasks/03-indexer-contract-configs/plan.md) | [summary](tasks/03-indexer-contract-configs/summary.md) |
| 04 | [method-a-ocr](#task-04-method-a-ocr) | ✅ | [plan](tasks/04-method-a-ocr/plan.md) | [summary](tasks/04-method-a-ocr/summary.md) |
| 05 | [method-b-caption](#task-05-method-b-caption) | ✅ | [plan](tasks/05-method-b-caption/plan.md) | [summary](tasks/05-method-b-caption/summary.md) |
| 06 | [method-c-unified-embed](#task-06-method-c-unified-embed) | ✅ | [plan](tasks/06-method-c-unified-embed/plan.md) | [summary](tasks/06-method-c-unified-embed/summary.md) |
| 07 | [method-d-multivector](#task-07-method-d-multivector) | ✅ | [plan](tasks/07-method-d-multivector/plan.md) | [summary](tasks/07-method-d-multivector/summary.md) |
| 08 | [matrix-report-verdict](#task-08-matrix-report-verdict) | ✅ | [plan](tasks/08-matrix-report-verdict/plan.md) | [summary](tasks/08-matrix-report-verdict/summary.md) |

---

## Task 01: corpus-analysis

**Статус:** ✅ Done (2026-07-05)

**Цель:** прогнать агента-аналитика по всем 66 PNG корпуса и подтвердить (или опровергнуть) гипотезу, что слайды неоднородны в спектре текст/пиксели/расположение — и зафиксировать таксономию 5 сегментов вопросов с примерами на реальных слайдах.

> 📌 **Перед началом:** прочитать `schema-guided-reasoning` (структурированная классификация слайдов через Pydantic-схему вместо произвольного текста) и `dataset-builder` (принципы проектирования сегментного датасета — пригодится для черновика).

**Состав работ:**

- [x] Прогнать vision-агента по каждому из `data/multimodal-rag/slide-01.png … slide-66.png`; для каждого слайда зафиксировать структурированно: тип содержимого (текст/диаграмма-число/схема-раскладка/фото/мем), плотность текста, наличие ключевых чисел, зависит ли смысл от расположения элементов.
- [x] Явно проверить гипотезу неоднородности: показать минимум по 3 контрастных примера, где один и тот же класс метода (OCR / caption / image-embed) предположительно выиграет или проиграет — и почему усреднение по корпусу это скроет.
- [x] Зафиксировать таксономию 5 сегментов с определением и списком id слайдов-кандидатов на каждый (не менее 3 слайдов на сегмент):
  - **S1_text** — текст доминирует, OCR/caption не теряют смысл (плотные тезисы, цитаты, кейсы).
  - **S2_chart** — числовые/статистические слайды (например слайды 10–11: доли/проценты Zapier, СберАналитика).
  - **S3_layout** — смысл в расположении и структуре, не в тексте построчно (roadmap-диаграмма ступеней, схема «айсберг», схема платформы).
  - **S4_multi** — вопрос требует данных из 2+ слайдов (например все шаги модели Коттера, вся цепочка 5 ступеней, набор кейсов по вертикалям).
  - **S5_unanswerable** — вопрос вне корпуса (цены, юридические детали, вещи, которых на слайдах физически нет).
- [x] Черновик датасета: минимум 3 примера вопрос→эталон на каждый сегмент (финализация количества — Task 02).
- [x] Зафиксировать ожидания по методам (гипотезы, не выводы) и риски: малая выборка (66 слайдов), субъективность разметки, отсутствие golden-set для CER/TEDS.
- [x] Сохранить `docs/sprints/sprint-10-multimodal-rag/analysis.md`.

**Критерии готовности:**

*Агент проверяет:*

- [x] `analysis.md` содержит разделы: карта слайдов, подтверждение гипотезы неоднородности (с контрастными примерами), таксономия 5 сегментов, черновик датасета (≥3 примера/сегмент), ожидания по методам, риски.
- [x] Каждый сегмент подтверждён ≥3 конкретными номерами реальных слайдов (не абстрактно).

*Пользователь проверяет:*

- [x] Таксономия и примеры соответствуют реальному содержимому презентации.
- [x] Гипотеза неоднородности выглядит обоснованной, а не притянутой под желаемый результат.

**Артефакты:**

| Путь | Описание |
|------|----------|
| `docs/sprints/sprint-10-multimodal-rag/analysis.md` | §0 сводка, карта слайдов (§1), группы (§1b), таксономия, черновик датасета, ожидания и риски (§4) |
| `docs/sprints/sprint-10-multimodal-rag/tasks/01-corpus-analysis/plan.md` | План задачи |
| `docs/sprints/sprint-10-multimodal-rag/tasks/01-corpus-analysis/summary.md` | Итог задачи |

---

## Task 02: datasets-metrics-baseline

**Статус:** ✅ Done (2026-07-05)

**Цель:** собрать сегментный датасет вопрос→эталон, описать три группы метрик (retrieval / ingestion-quality / generation опц.) и прогнать наивный text baseline, зафиксировав боль по сегментам.

> 📌 **Перед началом:** прочитать `dataset-builder` (сборка датасета по сегментам) и `.methodology/eval/metrics-guide.md` + `.methodology/eval/eval-methodology.md` (выбор метрик по ступеням E-17); при готовом датасете — прогнать через `dataset-reviewer` перед фиксацией.

**Состав работ:**

- [x] Собрать датасет по 5 сегментам из `analysis.md`; эталоны — PNG-verified. **v002:** 38 items (`v002_2026-07-05.json`, post dataset-reviewer).
  - S1: 7 · S2: 9 · S3: 10 · S4: 6 · S5: 6 (`trap_slides` + `expected_behavior: refusal`).
- [x] Описать три группы метрик в `metric_map.md`:
  - **retrieval по сегментам:** Recall@k, nDCG@5, MRR — S1/S2/S3; S4 — set-recall; S5 — **не nDCG**, primary = `correct_refusal_rate` (generation).
  - **ingestion-quality (диагностика):** CER — Task 04; TEDS — Task 07.
  - **время и стоимость:** `build_time_s`, `est_cost_usd` — на конфигурацию.
- [x] Эмбеддер: `intfloat/multilingual-e5-base` (768d, CPU, префиксы query/passage).
- [x] Naive baseline (Task 02): PDF text layer, 0/66 non-empty → e5 → Qdrant `multimodal_text_naive_v002`. Путь corpus перенесён в Task 03 → `evals/artifacts/corpus/text_naive/`.
- [x] Eval по сегментам; отчёт `evals/reports/multimodal-baseline.md`.
- [x] Ссылка из `docs/eval.md`; секция в `docs/eval/metrics-map.md`.

**Критерии готовности:**

*Агент проверяет:*

- [x] Датасет валиден, 5 сегментов, `required_slides` заполнены.
- [x] `metric_map.md` — три группы метрик с формулами.
- [x] Baseline прогоняется (`make eval-multimodal-baseline`); метрики **по сегментам**.

*Пользователь проверяет:*

- [x] Вопросы требуют содержимого слайдов (validation sample v002: S5×6, S2-9, S1-6/7, S4-2 — PNG, 2026-07-05).
- [x] Просадка baseline по сегментам правдоподобна (v002 re-run; PDF layer пуст → ≈0 + шум).

**Артефакты:**

| Путь | Описание |
|------|----------|
| `evals/datasets/multimodal/multimodal-rag/v002_2026-07-05.json` | Eval-датасет v002 (38 items) |
| `evals/datasets/multimodal/multimodal-rag/v001_2026-07-05.json` | v001 (immutable) |
| `evals/datasets/multimodal/multimodal-rag/v002-changelog.md` | Changelog v001→v002 |
| `evals/datasets/multimodal/multimodal-rag/README.md` | Схема полей, версионирование |
| `docs/sprints/sprint-10-multimodal-rag/metric_map.md` | Три группы метрик |
| `docs/sprints/sprint-10-multimodal-rag/tasks/02-datasets-metrics-baseline/plan.md` | План задачи |
| `docs/sprints/sprint-10-multimodal-rag/tasks/02-datasets-metrics-baseline/summary.md` | Итог задачи |
| `evals/configs/multimodal-baseline.yaml` | Конфиг baseline v002 (схема обновлена в Task 03) |
| `evals/artifacts/corpus/text_naive/slide-*.txt` | Naive corpus (66 файлов; Task 03, было `corpus/text_naive/`) |
| `evals/scripts/run_multimodal_baseline.py` | Thin wrapper → `run_multimodal_eval` |
| `evals/scripts/multimodal_models.py` | Pydantic-модели датасета |
| `evals/scripts/multimodal_metrics.py` | Retrieval-метрики по сегментам |
| `evals/tests/test_multimodal_dataset.py` | Тесты датасета и метрик |
| `evals/reports/multimodal-baseline.md` | Baseline retrieval по сегментам |
| `evals/reports/runs/multimodal-baseline-20260705T154657Z.json` | Run JSON (v002, Task 02) |
| `docs/eval.md` | Точка входа eval |
| `docs/eval/metrics-map.md` | Секция `multimodal-rag` |
| `docs/eval/dataset-map.md` | Секция `rag/multimodal-rag` |
| `Makefile` | Цель `eval-multimodal-baseline` |

---

## Task 03: indexer-contract-configs

**Статус:** ✅ Done (2026-07-05)

**Цель:** зафиксировать контракт `Indexer`, реестр индексаторов и 5 eval-конфигов так, чтобы методы A–D подключались параметром, а Qdrant-поиск и eval-контур оставались общими.

**Состав работ:**

- [x] Контракт `IndexCost` + `Indexer.build_index(corpus_dir) -> IndexCost`
- [x] `INDEXER_REGISTRY` + `make_indexer(cfg)`
- [x] Граница: индексатор → Qdrant; search/eval — `multimodal_retrieval.py`
- [x] 5 конфигов в `evals/configs/` (baseline + A–D stubs)
- [x] Env: `OCR_ENGINE`, `CAPTION_MODEL`, `D_MAX_SIDE` в `.env.example`
- [x] `tests/test_indexer_registry.py`

**Критерии готовности:**

*Агент:* pytest ✅ · `mcp_server/` без изменений ✅

*Пользователь:* контракт config-driven ✅ (2026-07-05)

**Артефакты:**

| Путь | Описание |
|------|----------|
| `evals/indexers/base.py` | `IndexCost`, `Indexer`, `validate_corpus_dir()` |
| `evals/indexers/config.py` | `MultimodalEvalConfig`, `REPO_ROOT`, `EVALS_ROOT` |
| `evals/indexers/factory.py` | `load_multimodal_config()`, `make_indexer()` |
| `evals/indexers/registry.py` | `INDEXER_REGISTRY` (baseline + stub A–D) |
| `evals/indexers/baseline.py` | `BaselineIndexer` (PDF text layer, не OCR) |
| `evals/indexers/stubs.py` | Stub A/B/C/D (`NotImplementedError` до Task 04–07) |
| `evals/scripts/multimodal_retrieval.py` | Общий E5 search + eval |
| `evals/scripts/run_multimodal_eval.py` | Generic runner (config → index → eval → report) |
| `evals/scripts/run_multimodal_baseline.py` | Thin wrapper |
| `evals/configs/multimodal-baseline.yaml` | Baseline (обновлённая схема `indexer.*`) |
| `evals/configs/multimodal-a-ocr.yaml` | Stub метод A |
| `evals/configs/multimodal-b-caption.yaml` | Stub метод B |
| `evals/configs/multimodal-c-unified.yaml` | Stub метод C |
| `evals/configs/multimodal-d-multivector.yaml` | Stub метод D |
| `evals/tests/test_indexer_registry.py` | Тесты реестра (8 passed) |
| `evals/artifacts/corpus/text_naive/slide-*.txt` | Baseline corpus (66, PDF layer пуст) |
| `evals/reports/multimodal-baseline.md` | Re-run + ingestion failure (slides 10/11/9) |
| `evals/reports/runs/multimodal-baseline-20260705T161917Z.json` | Run JSON (Task 03) |
| `.env.example` | `OCR_ENGINE`, `CAPTION_MODEL`, `D_MAX_SIDE` |
| `Makefile` | `eval-multimodal-baseline`, `eval-multimodal` |
| `docs/sprints/sprint-10-multimodal-rag/tasks/03-indexer-contract-configs/plan.md` | План |
| `docs/sprints/sprint-10-multimodal-rag/tasks/03-indexer-contract-configs/summary.md` | Итог |

**Запуск:** `make eval-multimodal-baseline` · `make eval-multimodal CONFIG=configs/multimodal-a-ocr.yaml`

---

## Task 04: method-a-ocr

**Статус:** ✅ Done (2026-07-05)

**Цель:** реализовать метод A под контракт индексатора в двух OCR-движках (Tesseract и современный CPU-движок), посчитать CER на выборке и сравнить по сегментам.

**Итог:** Tesseract (docker) vs RapidOCR (local ONNX). EasyOCR не использован — docker build blocked. **Победитель на этом корпусе: Tesseract** (CER 0.600 vs 0.850; S1 Recall@5 0.857 vs 0.429).

**Состав работ:**

- [x] `A_ocr_tesseract`: Tesseract (`lang=rus+eng`, PSM 6) → `evals/artifacts/ocr/tesseract/slide-NN.txt`.
- [x] `A_ocr_modern`: RapidOCR ONNX (fallback вместо EasyOCR) → `evals/artifacts/ocr/rapidocr/slide-NN.txt`.
- [x] Оба текстовых корпуса → e5 → Qdrant, раздельные коллекции.
- [x] CER на 10 PNG-verified слайдах (golden manifest).
- [x] Eval по 5 сегментам + `build_time_s` (73s / 295s), `est_cost_usd=0`.
- [x] `evals/reports/multimodal-a-ocr.md`.

**Критерии готовности:**

*Агент проверяет:*

- [x] CER по явной формуле; формула и выборка в отчёте.
- [x] Обе коллекции проиндексированы; eval по сегментам для обеих.

*Пользователь проверяет:*

- [x] Тексты в `evals/artifacts/ocr/` читаемы и позволяют вручную оценить типичные ошибки (кириллица, разрывы строк, тёмная тема).

**Артефакты:**

- `evals/indexers/a_ocr.py`, `evals/indexers/ocr/`
- `evals/artifacts/ocr/tesseract/**`, `evals/artifacts/ocr/rapidocr/**`
- `evals/reports/multimodal-a-ocr.md`
- [summary](tasks/04-method-a-ocr/summary.md)

**Запуск:** `make eval-multimodal-a-ocr`

---

## Task 05: method-b-caption

**Статус:** ✅ Done (2026-07-10)

**Цель:** реализовать метод B (captioning через VLM, параметр `vlm_model`), прогнать минимум две модели и оценить, оправдывает ли более дорогая модель прирост качества и риск галлюцинаций на числах.

**Итог:** Nemotron free vs Gemini flash-lite. **Gemini оправдывает прирост на S3** (Recall@5 0.800 vs 0.700); S2 паритет (1.000). Быстрее в 0.66×, дороже ~3.5×. Hallucination-check slides 10/11 — совпадает у обеих. Slides 50–66 nemotron — fallback `qwen/qwen3-vl-8b-instruct` (rate limit free tier).

**Состав работ:**

- [x] `B_caption(vlm_model)`: подпись на слайд через OpenRouter; дефолт `nvidia/nemotron-nano-12b-v2-vl:free`.
- [x] Второй прогон: `google/gemini-2.5-flash-lite` (обе модели FOUND на OpenRouter 2026-07-10).
- [x] Сохранять подписи в `evals/artifacts/captions/{model_slug}/slide-NN.txt`.
- [x] Ручная сверка чисел на S2-слайдах (10–11) → `evals/artifacts/captions/hallucination-check.md`.
- [x] Подписи каждой модели → e5 → Qdrant, отдельные коллекции.
- [x] Eval по 5 сегментам + `build_time_s` + `est_cost_usd` для каждой модели.
- [x] `evals/reports/multimodal-b-caption.md`: ответ «да» на S3; S2 паритет.

**Критерии готовности:**

*Агент проверяет:*

- [x] Обе модели прогнаны отдельными коллекциями; cost/time зафиксированы по каждой.
- [x] `hallucination-check.md` существует и содержит по каждому проверенному S2-слайду явный вердикт.

*Пользователь проверяет:*

- [x] Подписи на S2/S3 слайдах адекватны по смыслу.
- [x] Отчёт даёт прямой ответ «да/нет» на вопрос об оправданности более дорогой модели, с цифрами.

**Артефакты:**

| Путь | Описание |
|------|----------|
| `evals/indexers/caption/` | OpenRouter VLM client, pricing, batch |
| `evals/indexers/b_caption.py` | `BCaptionIndexer` |
| `evals/configs/multimodal-b-caption-nemotron.yaml` | Конфиг nemotron |
| `evals/configs/multimodal-b-caption-gemini.yaml` | Конфиг gemini |
| `evals/scripts/caption_hallucination_check.py` | Hallucination-check |
| `evals/scripts/run_multimodal_b_caption.py` | Orchestrator |
| `evals/datasets/multimodal/caption-hallucination/v001_2026-07-10.json` | Manifest S2 чисел |
| `evals/tests/test_caption_client.py`, `evals/tests/test_b_caption_indexer.py` | Тесты |
| `evals/artifacts/captions/nemotron-nano-12b-v2-vl/slide-*.txt` | 66 caption (nemotron + fallback 50–66) |
| `evals/artifacts/captions/gemini-2.5-flash-lite/slide-*.txt` | 66 caption (gemini) |
| `evals/artifacts/captions/hallucination-check.md` | Вердикты slides 10/11 |
| `evals/reports/multimodal-b-caption.md` | Сводный отчёт |
| `evals/reports/runs/multimodal-b-caption-*.json` | Run JSON |
| `Makefile` | `eval-multimodal-b-caption` |
| [plan](tasks/05-method-b-caption/plan.md) · [summary](tasks/05-method-b-caption/summary.md) | Документация задачи |

**Запуск:** `make eval-multimodal-b-caption`

---

## Task 06: method-c-unified-embed

**Статус:** ✅ Done (2026-07-11)

**Цель:** реализовать метод C (один вектор на страницу через image-embedder), сравнить с методом B и подтвердить/опровергнуть гипотезу просадки визуального эмбеддера на русском тексте (MIRACL-Vision).

**Итог:** `nvidia/llama-nemotron-embed-vl-1b-v2:free` (dim 2048). Гипотеза просадки на S1 **опровергнута** (C Recall@5=1.000 vs best B=0.857). C выигрывает на S1/S3, проигрывает на S4. Быстрее B (~207s), `index_size_mb` выше (0.516).

**Состав работ:**

- [x] `C_unified`: PNG → VL embed → Qdrant `multimodal_unified_vl_v002` (без промежуточного текста).
- [x] Eval по 5 сегментам + `build_time_s` + `est_cost_usd`.
- [x] C vs B по сегментам; гипотеза S1 — **опровергнута** числами.
- [x] `evals/reports/multimodal-c-unified.md`.

**Критерии готовности:**

*Агент проверяет:*

- [x] Коллекция создана, eval прогнан по всем 5 сегментам.
- [x] Отчёт содержит прямое сравнение C vs B по каждому сегменту.

*Пользователь проверяет:*

- [x] Вывод про русский язык обоснован конкретными числами по сегментам.

**Артефакты:**

| Путь | Описание |
|------|----------|
| `evals/indexers/vl_embed/` | VL embed client (OpenRouter, batch, preflight) |
| `evals/indexers/openrouter_common.py` | Shared OpenRouter helpers |
| `evals/indexers/c_unified.py` | `CUnifiedIndexer` |
| `evals/indexers/registry.py` | Registry update |
| `evals/indexers/factory.py` | `EMBED_VL_MODEL` env override |
| `evals/scripts/multimodal_retrieval.py` | `QueryEmbedder` + `VLEmbedder` |
| `evals/scripts/run_multimodal_c_unified.py` | Orchestrator |
| `evals/configs/multimodal-c-unified.yaml` | Конфиг method C |
| `evals/tests/test_vl_embed_client.py` | Тесты VL client |
| `evals/tests/test_c_unified_indexer.py` | Тесты индексатора |
| `evals/reports/multimodal-c-unified.md` | Сводный отчёт C vs B |
| `evals/reports/runs/multimodal-c-unified-20260711T125339Z.json` | Run JSON |
| `Makefile` | `eval-multimodal-c-unified` |
| `.env.example` | `EMBED_VL_MODEL` |
| [plan](tasks/06-method-c-unified-embed/plan.md) · [summary](tasks/06-method-c-unified-embed/summary.md) | Документация задачи |

**Запуск:** `make eval-multimodal-c-unified`

---

## Task 07: method-d-multivector

**Статус:** ✅ Done (2026-07-11)

**Цель:** реализовать метод D (multivector через Jina v4) с Qdrant `MultiVectorConfig(MAX_SIM)`, зафиксировать цену хранения (`index_size_mb`) и TEDS на табличных слайдах.

**Итог:** `jina-embeddings-v4` (token_dim 128, MAX_SIM). Гипотеза прироста на S2/S3 **не подтверждена** (S2 паритет с C/B, S3 = C). Единственный явный выигрыш D над C — S4 Recall +0.167. Цена: `index_size_mb` **24.2** (46.9× vs C), `build_time_s` **631** (3.0× vs C), `est_cost_usd` **$0.026**. TEDS slides 10/11 = 0.000 (диагностика hyp-pipeline).

**Состав работ:**

- [x] `D_multivector`: `jina-embeddings-v4`, `return_multivector=true`; `D_MAX_SIDE` через env.
- [x] Qdrant `MultiVectorConfig(MAX_SIM)`; `index_size_mb` в `IndexCost`.
- [x] TEDS на слайдах 10/11 с ручной эталонной разметкой.
- [x] Eval по 5 сегментам + `build_time_s` + `est_cost_usd`.
- [x] `evals/reports/multimodal-d-multivector.md`: D vs C/B по сегментам + cost multipliers.

**Критерии готовности:**

*Агент проверяет:*

- [x] Поиск через `MultiVectorConfig` отрабатывает без ошибок и возвращает результаты.
- [x] TEDS посчитан на слайдах 10/11 с зафиксированной эталонной разметкой.
- [x] `index_size_mb` явно сопоставлен с другими методами в отчёте.

*Пользователь проверяет:*

- [x] Цена (mb / время / $) наглядно стоит рядом с приростом качества.

**Артефакты:**

| Путь | Описание |
|------|----------|
| `evals/indexers/jina_multivector/` | Jina multivector client (client, preprocess, factory) |
| `evals/indexers/d_multivector.py` | `DMultivectorIndexer` |
| `evals/indexers/registry.py` | Registry update |
| `evals/indexers/factory.py` | `require_jina_key`, `D_MAX_SIDE` |
| `evals/scripts/multimodal_retrieval.py` | `JinaMultivectorEmbedder` + MAX_SIM search |
| `evals/scripts/run_multimodal_d_multivector.py` | Orchestrator + report writer |
| `evals/scripts/teds_score.py` | TEDS scoring |
| `evals/scripts/teds_structure_extract.py` | VLM → HTML structure extract |
| `evals/configs/multimodal-d-multivector.yaml` | Конфиг method D (dim 128) |
| `evals/datasets/multimodal/teds-golden/v001_2026-07-11.json` | TEDS golden manifest |
| `evals/datasets/multimodal/teds-golden/refs/slide-10.html` | Эталон slide 10 |
| `evals/datasets/multimodal/teds-golden/refs/slide-11.html` | Эталон slide 11 |
| `evals/artifacts/multivector/teds-hyp/slide-10.html` | VLM hypothesis slide 10 |
| `evals/artifacts/multivector/teds-hyp/slide-11.html` | VLM hypothesis slide 11 |
| `evals/tests/test_jina_multivector_client.py` | Тесты Jina client |
| `evals/tests/test_d_multivector_indexer.py` | Тесты индексатора |
| `evals/tests/test_indexer_registry.py` | Registry update |
| `evals/reports/multimodal-d-multivector.md` | Сводный отчёт D vs C/B + TEDS |
| `evals/reports/runs/multimodal-d-multivector-20260711T155309Z.json` | Run JSON |
| `Makefile` | `eval-multimodal-d-multivector` |
| `.env.example` | `JINA_API_KEY`, `D_MAX_SIDE` |
| [plan](tasks/07-method-d-multivector/plan.md) · [summary](tasks/07-method-d-multivector/summary.md) | Документация задачи |

**Запуск:** `make eval-multimodal-d-multivector`

---

## Task 08: matrix-report-verdict

**Статус:** ✅ Done (2026-07-11)

**Цель:** собрать сводную матрицу «конфигурация × сегмент» со столбцами цены, зафиксировать decision log и вердикт — какая точка спектра методов оправдана для этого корпуса и какой ценой — и закрыть спринт.

**Итог:** 7 конфигураций × 5 сегментов в [multimodal-final.md](../../../evals/reports/multimodal-final.md). **Вердикт: метод C default** (S1/S2 Recall@5=1.000, S3=0.900, $0); D — S4-upgrade (+0.167 Recall, ×46.9 storage); B_gemini — degraded fallback; A_tesseract — offline.

**Состав работ:**

- [x] Сводная таблица: строки — все 7 конфигураций (baseline, A_tesseract, A_modern, B_model1, B_model2, C, D), столбцы — метрика по каждому сегменту (nDCG@5 / set-Recall@5 / доля корректных отказов — по типу сегмента) + `index_size_mb`, `build_time_s`, `~$/прогон`.
- [x] Decision log: минимум по одной записи на метод (A/B/C/D) — что дало прирост, на каком сегменте, какой ценой; что не помогло — с цифрами, не общими словами.
- [x] Вердикт: рекомендуемая точка спектра методов под этот корпус (возможна комбинация по сегментам) — с обоснованием числами из отчётов Task 04–07.
- [x] Явно перечислить антипаттерны и как их избежали/не избежали за спринт: ColPali ради ColPali (метод D не выбран по умолчанию без числового обоснования), среднее по больнице (решение не строится на общем среднем по корпусу), CER на глаз (формула и выборка зафиксированы в Task 04), молчаливая правка чисел у B (проверено в `hallucination-check.md`, Task 05).
- [x] Обновить `docs/roadmap.md`: sprint-10 → ✅ Done, ссылка на `multimodal-final.md`.
- [x] Обновить этот README: статус, дата закрытия, раздел «Итог».

**Критерии готовности:**

*Агент проверяет:*

- [x] Сводная таблица содержит все 7 конфигураций и 5 сегментов + 3 столбца цены.
- [x] Decision log содержит минимум одну числовую запись на каждый из методов A/B/C/D.

*Пользователь проверяет:*

- [x] Вердикт даёт конкретную рекомендацию с числами (не «все методы по-своему хороши»).
- [x] Антипаттерны перечислены явно, а не подразумеваются.

**Артефакты:**

| Путь | Описание |
|------|----------|
| `evals/reports/multimodal-final.md` | Финальный отчёт: §1.0 матрица качество×сегмент+цена, decision log, вердикт, антипаттерны |
| `docs/sprints/sprint-10-multimodal-rag/tasks/08-matrix-report-verdict/plan.md` | План задачи |
| `docs/sprints/sprint-10-multimodal-rag/tasks/08-matrix-report-verdict/summary.md` | Итог задачи |
| `docs/roadmap.md` | sprint-10 → Done, ссылка на final report |
| `docs/sprints/sprint-10-multimodal-rag/README.md` | Статус спринта, раздел «Итог» |
| `docs/README.md` | Навигатор: sprint-09/10 Done |
| `docs/eval/README.md` | Eval-контур: все multimodal-отчёты |

---

## Итог

> **Спринт закрыт 2026-07-11.** Финальный отчёт: [multimodal-final.md](../../../evals/reports/multimodal-final.md)

### Вердикт спринта

| Роль | Метод | Обоснование |
|---|---|---|
| **Default** | C (unified VL embed) | S1/S2 Recall@5=1.000, S3=0.900, build=207s, $0 |
| **S4 upgrade** | D (Jina multivector) | +0.167 Recall vs C на S4; цена ×46.9 storage, $0.026 |
| **Degraded fallback** | B_gemini | S2=1.000, S3=0.800; при недоступности VL embed API |
| **Offline fallback** | A_tesseract | S1=0.857, S2=0.889; без API, CER=0.600 |

### Task 01: corpus-analysis ✅ (2026-07-05)

Подтверждена неоднородность корпуса (66 PNG): 5 сегментов S1–S5. `analysis.md` дополнен §0 (сводка), §1b (группы слайдов), матрицей ожиданий в §4. Эталоны — только с PNG.

### Task 02: datasets-metrics-baseline ✅ (2026-07-05)

- Датасет **v002**: 38 items; S5 — `trap_slides`; validation sample PNG ✅
- Baseline re-run: [multimodal-baseline.md](../../../evals/reports/multimodal-baseline.md) · `make eval-multimodal-baseline`
- Итог: [summary.md](tasks/02-datasets-metrics-baseline/summary.md)

### Task 03: indexer-contract-configs ✅ (2026-07-05)

- Контракт `Indexer` + `INDEXER_REGISTRY` + 5 конфигов; метод переключается YAML/env
- Артефакты baseline: `evals/artifacts/corpus/text_naive/` (legacy `corpus/text_naive/` удалён)
- Ingestion failure: slides 10/11/9 — 0 PDF chars, chart-слайды слепы
- Итог: [summary.md](tasks/03-indexer-contract-configs/summary.md)

### Task 04: method-a-ocr ✅ (2026-07-05)

- Tesseract (docker) vs RapidOCR (local); победитель **Tesseract** (CER + S1 retrieval)
- Итог: [summary.md](tasks/04-method-a-ocr/summary.md) · `make eval-multimodal-a-ocr`

### Task 05: method-b-caption ✅ (2026-07-10)

- Nemotron free vs Gemini flash-lite; **gemini оправдан на S3** (Recall@5 0.800 vs 0.700)
- Hallucination-check slides 10/11 — совпадает; nemotron 50–66 — fallback qwen (rate limit)
- Итог: [summary.md](tasks/05-method-b-caption/summary.md) · `make eval-multimodal-b-caption`

### Task 06: method-c-unified-embed ✅ (2026-07-11)

- VL image embed `nvidia/llama-nemotron-embed-vl-1b-v2:free` (2048d); гипотеза просадки на S1 **опровергнута**
- C Recall@5: S1=1.000, S3=0.900 vs best B 0.857/0.800; S4 проигрыш (0.833 vs 1.000)
- Итог: [summary.md](tasks/06-method-c-unified-embed/summary.md) · `make eval-multimodal-c-unified`

### Task 07: method-d-multivector ✅ (2026-07-11)

- Jina v4 multivector (MAX_SIM); S4 +0.167 Recall vs C — единственный прирост
- Цена: index_size_mb=24.2 (46.9× vs C), build=631s, $0.026; TEDS slides 10/11=0.000
- Итог: [summary.md](tasks/07-method-d-multivector/summary.md) · `make eval-multimodal-d-multivector`

### Task 08: matrix-report-verdict ✅ (2026-07-11)

- Сводная матрица 7×5 + decision log + антипаттерны
- Вердикт: C default, D — S4-upgrade, B_gemini/A_tesseract — fallback
- Итог: [multimodal-final.md](../../../evals/reports/multimodal-final.md) · [plan](tasks/08-matrix-report-verdict/plan.md)

### Артефакты (Task 01–08)

| Путь | Описание |
|------|----------|
| `docs/sprints/sprint-10-multimodal-rag/analysis.md` | Анализ корпуса (§0–§4) |
| `docs/sprints/sprint-10-multimodal-rag/metric_map.md` | Три группы метрик |
| `evals/datasets/multimodal/multimodal-rag/v002_2026-07-05.json` | Eval-датасет v002 |
| `evals/datasets/multimodal/multimodal-rag/v002-changelog.md` | Changelog датасета |
| `evals/indexers/` | Контракт индексаторов, реестр, baseline, stubs |
| `evals/scripts/multimodal_retrieval.py` | Общий downstream (search + eval) |
| `evals/scripts/run_multimodal_eval.py` | Generic eval runner |
| `evals/configs/multimodal-*.yaml` | 5 конфигов (baseline + A–D) |
| `evals/artifacts/corpus/text_naive/` | Baseline corpus (66 `.txt`) |
| `evals/reports/multimodal-baseline.md` | Baseline по сегментам |
| `evals/reports/multimodal-a-ocr.md` | Method A OCR |
| `evals/reports/multimodal-b-caption.md` | Method B Caption |
| `evals/reports/multimodal-c-unified.md` | Method C Unified |
| `evals/reports/multimodal-d-multivector.md` | Method D Multivector |
| `evals/reports/multimodal-final.md` | Финальный отчёт Task 08 |
| `evals/reports/runs/multimodal-baseline-20260705T161917Z.json` | Последний run JSON |
| `docs/sprints/sprint-10-multimodal-rag/tasks/01-corpus-analysis/summary.md` | Итог Task 01 |
| `docs/sprints/sprint-10-multimodal-rag/tasks/02-datasets-metrics-baseline/summary.md` | Итог Task 02 |
| `docs/sprints/sprint-10-multimodal-rag/tasks/03-indexer-contract-configs/summary.md` | Итог Task 03 |
| `docs/eval.md` · `docs/eval/dataset-map.md` · `docs/eval/metrics-map.md` | Eval-контур |

**Входной корпус:** `data/multimodal-rag/slide-01.png … slide-66.png`, `slide-01.pdf` (только PDF+PNG; pre-flight в `validate_corpus_dir`).

**Дерево артефактов ingestion (Task 03+):**

```
evals/artifacts/
├── corpus/text_naive/     ← baseline (Task 03)
├── ocr/                   ← Task 04 (tesseract, rapidocr)
├── captions/              ← Task 05 (nemotron, gemini, hallucination-check.md)
└── multivector/teds-hyp/  ← Task 07 (TEDS hypothesis)
```
