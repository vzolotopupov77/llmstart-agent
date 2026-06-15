# Гайд по метрикам eval — справочник проекта
## Для человека и для coding-агента (`docs/eval/metrics-guide.md`)

> Назначение: единый справочник при заполнении `docs/eval/metrics-map.md` и написании evaluators. Правило проекта — **framework-first** (принцип E-17 методологии): сначала ищем метрику здесь, свою judge-метрику делаем только через ADR. Гайд сгруппирован по категориям; для каждой метрики — человеческое объяснение («на какой вопрос отвечает»), нужен ли эталон, и ссылка на документацию.
>
> **Обновлено:** 2026-06-10 (добавлены: item/run-level разделение, `task_error`/`error_rate`/`executed_tools_count`, главная метрика, заметка про OSS и tool calling)

---

## 0. Как выбирать метрику (порядок)

1. **Expected_output — структура или факт** (список инструментов, сегмент, запись в файле)? → детерминированная проверка кодом (категория A). LLM для проверки строки не нужен.
2. **Стандартная потребность RAG/агента/диалога?** → готовая метрика из RAGAS или DeepEval (категории B–D).
3. **Свой критерий, которого нет в готовых?** → `GEval(criteria=...)` из DeepEval — фреймворочный способ кастомного критерия (категория E).
4. **Не закрывается даже G-Eval?** → собственный судья в `evals/judges/` + ADR в `docs/decisions/`: какие готовые метрики рассматривали, почему не подошли, план калибровки против human review.

Два сквозных понятия:
- **Reference-based vs reference-free.** Reference-based метрики требуют эталона (`expected_output` / reference context) — годятся для оффлайн-датасетов. Reference-free работают без эталона — годятся и для оффлайна, и для онлайн-оценки прод-трафика.
- **Слой.** Каждая метрика отвечает за свой слой: retrieval / генерация / поведение агента / диалог целиком. Метрика «не того слоя» даёт неинтерпретируемый сигнал (см. component-level evaluation в теоретическом модуле).

Ещё два правила (из методологии, E-18/E-19):
- **Item-level vs run-level.** Item-level метрики пишутся score'ом на каждый трейс (значение метрики, `task_error`); run-level — агрегаты на Dataset Run (средние, `error_rate`, доли). Это разные evaluators (`evaluators=` и `run_evaluators=` в `run_experiment`), и нужны оба: упавший item — это метрика, а не исключение в логе.
- **Главная метрика.** У проекта одна north-star метрика сравнения конфигураций — `avg_answer_correctness` на `e2e-qa`; faithfulness, task_completion и `error_rate` — guard-метрики. «Конфиг лучше» = главная выросла при не-просевших guard.

---

## A. Детерминированные проверки (свой код, ADR не нужен)

Самая дешёвая, быстрая и честная категория. Используется всегда, когда ответ проверяется без суждения.

| Метрика | На какой вопрос отвечает | Эталон | Score | Где в проекте |
|---|---|---|---|---|
| `exact_match` | Совпал ли вывод с эталоном дословно/по нормализованной строке? | да | BOOLEAN | `segment-routing` (b2b/b2c) |
| `structured_match` | Совпали ли извлечённые поля (JSON) с ожидаемыми? | да | NUMERIC (доля полей) | проверка карточки продукта, суммы |
| `state_check` | Наступил ли проверяемый факт в системе? | да (критерий) | BOOLEAN | `funnel-to-lead`: лид в `data/leads.txt`, ссылка на оплату сгенерирована |
| `format_check` | Валиден ли формат (JSON-схема, наличие ссылки, длина)? | нет | BOOLEAN | любой датасет |
| `latency` / `cost` / `steps_count` | Сколько времени/денег/шагов стоил ответ? | нет | NUMERIC | из трейса Langfuse (usage, observations) |
| `executed_tools_count` | Сколько инструментов агент реально вызвал? (0 при ожидаемых ≥1 — признак сломанного tool calling) | нет | NUMERIC | из observations типа tool; диагностика OSS-моделей |
| `task_error` | Упал ли прогон item с ошибкой? | нет | BOOLEAN (item-level) | все датасеты, обязательная |
| `error_rate` | Доля упавших items в ране | нет | NUMERIC (run-level) | все датасеты, обязательная guard-метрика |

Примечание: `ToolCorrectnessMetric` из DeepEval (категория C) — тоже детерминированная, просто упакованная фреймворком.

---

## B. RAG-метрики (слои retrieval и generation)

Основной фреймворк — **RAGAS** (docs.ragas.io); у DeepEval есть аналоги. Четыре классические метрики образуют квадрат «2 слоя × 2 направления». Важно: в UI Langfuse есть managed-evaluators «RAGAS» — это **промпты RAGAS через LLM-судью Langfuse, а не вызов библиотеки** (подтверждено командой Langfuse, GitHub Discussion #7534); для точных формул используйте Python-библиотеку.

### Слой generation (оцениваем ответ)

| Метрика | На какой вопрос отвечает | Эталон | Ссылка |
|---|---|---|---|
| **Faithfulness** (RAGAS) | «Все ли утверждения ответа выводятся из извлечённого контекста?» — анти-галлюцинации. Считается как доля подтверждённых утверждений | **нет** (reference-free) | docs.ragas.io → Metrics → Faithfulness; аналог: deepeval.com/docs/metrics-faithfulness |
| **Answer/Response Relevancy** (RAGAS) | «Отвечает ли ответ на заданный вопрос?» (не уехал ли в сторону). Идея: из ответа генерируются вопросы и сравниваются с исходным | **нет** | docs.ragas.io → Response Relevancy; аналог: deepeval.com/docs/metrics-answer-relevancy |
| **Answer Correctness** (RAGAS) | «Совпадает ли ответ с эталонным по смыслу и фактам?» — главная end-to-end метрика для `e2e-qa` | **да** | docs.ragas.io → Answer Correctness |

### Слой retrieval (оцениваем найденный контекст)

| Метрика | На какой вопрос отвечает | Эталон | Ссылка |
|---|---|---|---|
| **Context Precision** (RAGAS) | «Релевантные чанки выше нерелевантных в выдаче?» — качество ранжирования | да (или LLM-вариант без) | docs.ragas.io → Context Precision |
| **Context Recall** (RAGAS) | «Всё ли нужное для ответа вообще извлечено?» — полнота retrieval. Единственная из четвёрки, жёстко требующая ground truth | **да** | docs.ragas.io → Context Recall |
| **Contextual Relevancy** (DeepEval) | «Какая доля извлечённого контекста вообще относится к запросу?» — шум в контексте | нет | deepeval.com/docs/metrics-contextual-relevancy |

**Куда вешать в Langfuse:** retrieval-метрики — score на span `retriever` (component-level), generation-метрики — score на trace (end-to-end). Это и есть практическое различие двух уровней оценки.

---

## C. Агентные / поведенческие метрики (слой «поведение»)

Основной фреймворк — **DeepEval** (deepeval.com/guides/guides-ai-agent-evaluation). Словарь строгости сравнения траекторий заимствуем из Google ADK (google.github.io/adk-docs/evaluate): **EXACT / IN_ORDER / ANY_ORDER**.

| Метрика | На какой вопрос отвечает | Тип | Эталон | Ссылка |
|---|---|---|---|---|
| **ToolCorrectnessMetric** | «Агент вызвал те инструменты, что ожидались?» Сравнивает `tools_called` с `expected_tools`. Режим проекта — семантика IN_ORDER: легитимный лишний вызов не фейлит; EXACT — только осознанным решением | детерминир. | да | deepeval.com/docs/metrics-tool-correctness |
| **ArgumentCorrectnessMetric** | «Аргументы вызовов корректны относительно запроса?» (инструмент правильный, а параметры — мусор) | LLM-judge | нет | deepeval.com/docs/metrics-argument-correctness |
| **TaskCompletionMetric** | «Задача пользователя в итоге решена?» Judge читает весь трейс; test case с эталоном не нужен | LLM-judge | **нет** | deepeval.com/docs/metrics-task-completion |
| **Step efficiency** (нет готовой — считается из трейса) | «Не сделал ли агент лишних/повторных шагов?» Агент с task_completion=1.0 и девятью вызовами вместо трёх — проблема, которую pass/fail не видит | детерминир. | порог | считать по observations трейса; концепция: confident-ai.com/blog/llm-agent-evaluation-complete-guide |
| **Trajectory quality** | «Разумен ли путь к ответу целиком (план, порядок, реакции на ошибки)?» | LLM-judge | нет/rubric | методология: langchain.com/articles/llm-evaluation-framework; ADK rubric_based_tool_use_quality |

**Принцип пары (из методологии Google, забираем дословно по смыслу):** rubric/judge-метрика сама по себе может пропустить галлюцинацию, которая «хорошо читается»; trajectory-метрика сама по себе не скажет, получил ли пользователь полезный ответ. На важных кейсах ставьте обе.

**⚠️ OSS-модели и tool calling (опыт реального бенчмарка).** Агент целиком построен на tool calling (MCP), а при модельных свипах через OpenRouter OSS reasoning-модели часто ломают именно его: добровольно не вызывают инструменты (завершают reasoning-текстом) либо провайдер возвращает 400 на `tool_choice="any"`. Диагностика — по `executed_tools_count` (категория A): near-zero при ожидаемых вызовах = несовместимость модели с tool-стратегией, а не «плохое качество». Поэтому новые модели заводятся как `benchmark_only`-конфиги и попадают в продукт только после прохождения бенчмарка (принцип E-8 методологии).

---

## D. Multi-turn / conversational метрики (слой «диалог целиком»)

Фреймворк — **DeepEval** (conversational metrics, вход — весь диалог). В Langfuse многоходовые диалоги группируются в sessions; в экспериментах — один сценарий = один трейс.

| Метрика | На какой вопрос отвечает | Ссылка |
|---|---|---|
| **KnowledgeRetentionMetric** | «Бот помнит, что пользователь сказал раньше?» (имя, сегмент, выбранный курс) — провалы памяти между ходами | deepeval.com/docs/metrics-knowledge-retention |
| **ConversationCompletenessMetric** | «Диалог в итоге закрыл потребности пользователя?» | deepeval.com/docs/metrics-conversation-completeness |
| **ConversationRelevancyMetric** | «Ответы оставались релевантными на протяжении всего диалога?» (диалог может быть completeness=high, но с уходами в сторону) | deepeval.com/docs/metrics-conversation-relevancy |
| **RoleAdherenceMetric** | «Бот держится заданной роли?» (консультант llmstart, а не универсальный ассистент) | deepeval.com/docs/metrics-role-adherence |

**Техника для multi-turn датасетов — user simulation:** LLM-симулятор играет пользователя по сценарию (`scenarios.yaml`: цель, профиль, лимит ходов) и ведёт агента через воронку; успех проверяется детерминированно (категория A: `state_check`) + TaskCompletion на весь диалог. Концепция — из ADK (`eval dataset synthesize`, google.github.io/adk-docs/evaluate), реализация в нашем стеке своя, внутри task-функции эксперимента. В проекте: датасет `funnel-to-lead`.

---

## E. Кастомные критерии

| Инструмент | Когда | Ссылка |
|---|---|---|
| **G-Eval** (DeepEval) | Нужен свой критерий («не выдумал несуществующий продукт каталога», «не дал юридических обещаний»). Пишете criteria на естественном языке, фреймворк сам строит шаги оценки (CoT) и нормализует score. Это всё ещё «фреймворочный» путь — ADR не нужен, но criteria фиксируются в metrics-map | deepeval.com/docs/metrics-llm-evals |
| **LLM-as-a-judge в UI Langfuse** | Онлайн-оценка прод-трафика по расписанию/сэмплированию (не для оффлайн-экспериментов — там evaluators в коде). Типы score: NUMERIC / CATEGORICAL / BOOLEAN; вешается на traces или observations | langfuse.com/docs/evaluation/evaluation-methods/llm-as-a-judge |
| **Собственный судья** | Только если не закрылось ничем выше → `evals/judges/` + **ADR** с мотивацией и планом калибровки против human review. Помнить: согласие хорошего LLM-судьи с человеком ~85%, судья без калибровки — не истина | шаблон ADR — в `docs/decisions/` |

---

## F. Сводная карта «датасет проекта → метрики» (стартовая, уточняется в metrics-map.md)

| Датасет | Метрики (категория) |
|---|---|
| `e2e-qa` | Answer Correctness (B, ref-based) + Faithfulness (B, ref-free) |
| `rag-retrieval` | Context Recall + Context Precision (B) — score на span retriever |
| `tool-trajectory` | ToolCorrectness IN_ORDER (C) + steps_count (A) |
| `segment-routing` | exact_match (A) |
| `funnel-to-lead` | state_check: лид + ссылка (A) + TaskCompletion (C); user simulation (D) |
| `edge-cases` | G-Eval «scope adherence» (E) + format_check (A) |

---

## G. Инструменты для работы с метриками (skills, MCP, CLI)

### Skills
- **`langfuse`** (github.com/langfuse/skills, `npx skills add langfuse/skills --skill "langfuse"`) — официальный skill: датасеты, прогоны, scores, трейсы через Langfuse CLI. Основной рабочий инструмент.
- **`llm-evaluation`** (skills.sh/wshobson/agents/llm-evaluation) — методология выбора типов оценок; использовать на этапе проектирования карт.
- Для RAGAS и DeepEval отдельных skills нет — их доки агент берёт через Context7 MCP (ниже).

### MCP-серверы
- **Langfuse MCP (нативный, аутентифицированный)** — встроен в Langfuse по адресу `{LANGFUSE_HOST}/api/public/mcp` (streamableHttp, BasicAuth по API-ключам проекта; работает и на self-hosted). Инструменты prompt management: `getPrompt`, `listPrompts`, `createTextPrompt`, `createChatPrompt`, `updatePromptLabels` — управление версиями и labels промптов прямо из coding-агента. Дока: langfuse.com/docs/api-and-data-platform/features/mcp-server.
- **Langfuse Docs MCP (публичный)** — `https://langfuse.com/api/mcp`: вся документация Langfuse как инструмент агента; полезен при написании evaluators и интеграций. Дока: langfuse.com/docs/docs-mcp.
- **Context7 MCP** — актуальные доки и примеры кода библиотек `ragas` и `deepeval` по запросу (страховка от устаревших сигнатур в знаниях модели).

### CLI
- **Langfuse CLI** (langfuse.com/docs/api-and-data-platform/features/cli) — то, что под капотом у skill: операции с датасетами, трейсами, scores из терминала; используется нашими make-целями и в разговорном анализе прогонов.

---

## H. Сводные ссылки на документацию

- RAGAS: docs.ragas.io (Metrics → Faithfulness / Response Relevancy / Answer Correctness / Context Precision / Context Recall); интеграция с Langfuse: langfuse.com/guides/cookbook/evaluation_of_rag_with_ragas
- DeepEval: deepeval.com/docs/metrics-introduction (обзор), metrics-tool-correctness, metrics-task-completion, metrics-llm-evals (G-Eval), конversational-метрики, deepeval.com/guides/guides-ai-agent-evaluation
- Langfuse Evaluation: langfuse.com/docs/evaluation/overview, scores data model (langfuse.com/docs/evaluation/scores/data-model), experiments via SDK (langfuse.com/docs/evaluation/experiments/experiments-via-sdk), LLM-as-a-judge
- Методология-источник (читать, не устанавливать): google.github.io/adk-docs/evaluate — match-типы, multi-turn метрики, user simulation; github.com/google/agents-cli → skill `google-agents-cli-eval` (metrics-guide.md, user-simulation.md)
