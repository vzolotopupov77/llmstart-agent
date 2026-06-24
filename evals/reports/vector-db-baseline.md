# Baseline eval: Qdrant (sprint-08 vector-db, Task 05)

> **Дата:** 2026-06-24 · **Статус:** ✅ завершён (canonical re-run зафиксирован)  
> **Спринт:** [sprint-08-vector-db Task 05](../../docs/sprints/sprint-08-vector-db/README.md)  
> **Журнал:** [`experiments-log.md`](experiments-log.md) (E-26)

---

## Гипотеза / вопрос

Зафиксировать e2e-baseline агента на **QdrantRetriever** (`RETRIEVER_BACKEND=qdrant`) на датасете `e2e/e2e-qa/v002` — та же методология, промпт и judge, что у chroma-baseline (exp-005), чтобы изолировать переменную retrieval backend.

## Конфигурация

| Параметр | Значение |
|---|---|
| Ран (canonical) | `vector-db-baseline--e2e-qa--884a6423--20260624T070642Z` |
| config_id | `vector-db-baseline` |
| Retrieval | `qdrant` v1.18.2, `text-embedding-3-small`, chunk_size=800, top_k=4 |
| Промпт | `agent-system-prompt-v2` |
| Датасет | `e2e/e2e-qa` **v002** (Langfuse: `e2e/e2e-qa/v002`, 26 items) |
| git_sha | `884a6423` |
| Judge | `google/gemini-2.5-flash-lite` |
| Agent model | `openai/gpt-4o-mini` |
| Judge timeouts | `DEEPEVAL_PER_ATTEMPT_TIMEOUT_SECONDS=120`, `RETRY_MAX_ATTEMPTS=3` |

Ссылки: [analyze re-run](vector-db-baseline--e2e-qa--884a6423--20260624T070642Z.md) · [JSON](runs/vector-db-baseline--e2e-qa--884a6423--20260624T070642Z.json) · [Langfuse run](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/datasets/cmqfb07co0001nm07e59lzf0n/runs/66c1317b-78ad-4d52-9b92-a8762871eb86)

Конфиг: [`evals/configs/vector-db-baseline.yaml`](../../configs/vector-db-baseline.yaml)

### История прогонов

| Run | Длительность | error_rate | avg_answer_correctness | Статус |
|---|---:|---:|---:|---|
| `…20260623T143257Z` | 2609 s | 0.038 | 0.465 | historical — 8 judge errors (peak hours) |
| `…20260624T053801Z` | 67 s | 1.000 | 0.000 | invalid — backend не отвечал |
| `…20260624T062728Z` | 66 s | 1.000 | 0.000 | invalid — backend не отвечал |
| **`…20260624T070642Z`** | **1122 s** | **0.000** | **0.588** | **canonical re-run** |

---

## Результаты (canonical re-run)

| Метрика | Роль | Порог | Value | Статус |
|---|---|---|---|:---:|
| avg_answer_correctness | **главная** | ≥ 0.75 | **0.588** | 🔴 |
| avg_faithfulness | guard | ≥ 0.85 | 0.873 | 🟢 |
| avg_task_completion | guard | ≥ 0.80 | 0.585 | 🔴 |
| error_rate | infra | ≤ 0.05 | 0.000 | 🟢 |
| segment_match_rate | guard | 100% | 0.846 | 🔴 |

Таксономия провалов (re-run): retrieval 4 · generation 13 · behavior 2 · unknown 7.

Длительность: ~19 min (1122 s), **26/26** items linked в Langfuse.

---

## Метрики по типам датасета (canonical re-run, v002)

> Стратификация по manifest metadata (match по input).

### По segment

| Segment | n | avg_answer_correctness | avg_faithfulness | avg_task_completion |
|---|---:|---:|---:|---:|
| b2c | 25 | 0.580 | 0.868 | 0.580 |
| b2b | 1 | 0.800 | 1.000 | 0.700 |

### По source

| Source | n | avg_answer_correctness |
|---|---:|---:|
| real_dialog | 18 | 0.478 |
| synthetic | 8 | 0.838 |

### По turn_mode

| Turn mode | n | avg_answer_correctness |
|---|---:|---:|
| single | 20 | 0.665 |
| multi | 6 | 0.333 |

---

## Сравнение с предыдущим baseline (chroma-embedded)

> ⚠️ **E-16:** не факторный анализ — разные прогоны, один git_sha. Chroma baseline: [exp-005](exp-005-candidate-rag-first-prompt-v002.md) (`candidate-rag-first-prompt-e2e-qa-v002`, v002, chroma-embedded).

| Метрика | Chroma v002 (`…151141Z`) | Qdrant canonical (`…070642Z`) | Δ (Qdrant−Chroma) |
|---|---:|---:|---:|
| avg_answer_correctness | 0.662 | **0.588** | −0.074 |
| avg_faithfulness | 0.830 | 0.873 | +0.043 |
| avg_task_completion | 0.608 | 0.585 | −0.023 |
| error_rate | 0.000 | 0.000 | — |
| segment_match_rate | 0.846 | 0.846 | — |

| Метрика | Qdrant 1st run (`…143257Z`) | Qdrant canonical (`…070642Z`) | Δ |
|---|---:|---:|---:|
| avg_answer_correctness | 0.465 | 0.588 | +0.123 |
| avg_faithfulness | 0.780 | 0.873 | +0.093 |
| avg_task_completion | 0.512 | 0.585 | +0.073 |

**Интерпретация:** на canonical re-run Qdrant **ниже chroma** на главной метрике (−0.074), но разрыв **существенно меньше**, чем в первом прогоне (−0.197). Faithfulness на Qdrant **выше** chroma. Segment match совпадает (0.846). С учётом 2 judge artifacts adjusted correctness **≈ 0.64** — почти на уровне chroma 0.662.

---

## Конфаундеры и нюансы

### Judge artifacts (canonical re-run) — 2 items

| item_id | Причина | Влияние |
|---|---|---|
| e2e-qa-0025 | `Judge error: 'reason'` — GEval/deepeval не получил поле `reason` от gemini-2.5-flash-lite | correctness=0.00 (артефакт) |
| e2e-qa-0001 | `APIConnectionError` — сетевой сбой OpenRouter на последнем item | correctness=0.00 (артефакт) |

**Adjusted avg_answer_correctness** (24 items без judge error): **≈ 0.64** (raw 0.588 × 26 / 24).

Faithfulness и task_completion на этих items **не пострадали** — артефакты только на `answer_correctness`.

### Первый прогон (historical)

8/26 judge errors (peak hours, таймаут 30s) — см. `…143257Z`. Не использовать для сравнения с chroma.

### Invalid runs (infra)

`…053801Z` и `…062728Z` — backend на `:8003` не отвечал (67 s, error_rate=1.0, все `output=null`). Langfuse linked 25/26 на первом invalid run — один item без `dataset_run_item` при мгновенном task failure.

### Прочие наблюдения

- Multi-turn items слабее: correctness 0.333 vs single 0.665.
- Synthetic items выше real_dialog (0.838 vs 0.478) — возможный bias датасета, не эффект retrieval.
- Event loop warnings в логах deepeval/httpx — шум при cleanup async client, не влияет на scores.

---

## Решение

**🟡 Canonical Qdrant baseline зафиксирован; e2e-качество ниже порога 0.75, но близко к chroma с учётом judge artifacts.**

- **Canonical run:** `vector-db-baseline--e2e-qa--884a6423--20260624T070642Z` @ **0.588** (adjusted **≈ 0.64**).
- Qdrant vs Chroma: формально −0.074 на correctness; adjusted gap **≈ −0.02** — **не доказано**, что Qdrant хуже для e2e.
- Faithfulness **выше** chroma (+0.043) — retrieval context не деградирует.
- **Qdrant как production backend** по infra — ок; качество ответа требует eval-fix (generation 13, retrieval 4) **независимо от БД**.
- **Следующий шаг:** Task 06 — vector bench (latency, precision@k); eval-fix — отдельный спринт.

---

---

## Сравнение бэкендов (vector bench, Task 06)

> Прогон: `make bench` · dataset `data/` · top_k=4 · corpus 202 chunks · [отчёт](vector-bench-20260624T172450Z.md)  
> Метрика **precision@k / recall@k** — exact-match retrieval (bench-запросы = snippet из собственного корпуса).

| Backend | index_time_s | p50_latency_ms | p95_latency_ms | precision@k | recall@k |
|---------|-------------:|---------------:|---------------:|------------:|---------:|
| **Qdrant** 🏆 | **52.0** 🏆 | **3.33** 🏆 | **4.87** 🏆 | 0.2448 | 0.9792 |
| pgvector | 142.3 | 4.29 | 5.24 | 0.2448 | 0.9792 |
| Chroma | 162.6 | 4.89 | 9.19 | 0.2448 | 0.9792 |

**Победители по метрикам:**

| Метрика | Победитель | Комментарий |
|---------|-----------|-------------|
| `index_time_s` | **Qdrant** (52 s) | Qdrant в 2.7× быстрее pgvector, в 3.1× быстрее Chroma |
| `p50_latency_ms` | **Qdrant** (3.33 ms) | Qdrant → pgvector → Chroma; все < 5 ms |
| `p95_latency_ms` | **Qdrant** (4.87 ms) | Chroma показывает p95=9.19 ms — почти 2× хуже |
| `precision@k` | ничья | 0.2448 у всех трёх |
| `recall@k` | ничья | 0.9792 у всех трёх |

> **Примечание:** precision@k=0.2448, а не 1/top_k=0.25, потому что ~2% запросов не находят exact chunk в top-4 на расширенном корпусе (202 чанка, включая PDF). Все три бэкенда на одних и тех же данных и модели — качество retrieval идентично.

### Почему Qdrant остаётся основным бэкендом

По качеству retrieval (precision@k, recall@k) все три бэкенда эквивалентны на текущем корпусе, однако Qdrant стабильно быстрее на латентности поиска (p50 3.33 ms против 4.29–4.89 ms) и быстрее переиндексирует данные (52 s против 142–163 s). Кроме того, Qdrant — специализированная vector DB с Filterable HNSW, шардированием и квантованием, что даёт запас прочности при росте корпуса без смены стека. Выбор зафиксирован в [ADR-004](../../docs/adrs/ADR-004-vector-db.md); смена бэкенда через `RETRIEVER_BACKEND` в `.env` доступна без правки кода.

---

## Следующие шаги

- [x] Re-run e2e при стабильном judge — canonical `…070642Z`
- [x] Task 06: `PgvectorRetriever` + `make bench` — [vector-bench-20260624T172450Z.md](vector-bench-20260624T172450Z.md)
- [ ] Eval-fix: generation (13 items) и retrieval (4 items) из [analyze re-run](vector-db-baseline--e2e-qa--884a6423--20260624T070642Z.md)
