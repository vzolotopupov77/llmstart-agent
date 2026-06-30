# Corpus Analysis — GraphRAG Sprint 09

> Task 01 · Основные источники: `data/real_data/b2c/programs/`, `data/real_data/b2b/corporate-training.md`  
> Вспомогательные (синтетика): `data/b2c/catalog.json`, `data/b2c/courses-overview.md`, `data/b2c/faq-b2c.md`, `data/b2b/corporate-training.md`, `data/b2b/custom-development.md`  
> Исключено из индексирования: `data/leads.txt` (персональные данные), `data/payments.json` (транзакции), `data/real_data/b2b/*.pdf` (B2B-материалы вне скоупа графа каталога)

---

## 1. Инвентаризация сущностей

### Курсы (B2C)

| id (slug) | Название | Цена (₽) | Ступень комбо | Уровень | Формат | Файл |
|-----------|----------|----------|---------------|---------|--------|------|
| `vibe-coding` / `ai-coding-intensive-cursor` | Интенсив AI-кодинг ИИ-агентов в Cursor | 14 990 | 1 из 4 | интенсив | в записи | `real_data/b2c/programs/ai-coding-intensive-cursor.md` |
| `fullstack-aidd` / `ai-driven-fullstack` | AI-driven Fullstack разработка | 39 990 | 2 из 4 | средний | в записи + чат | `real_data/b2c/programs/ai-driven-fullstack.md` |
| `agents` / `ai-coding-agents-base` | AI-driven разработка ИИ-агентов | 39 990 | 3 из 4 | средний | гибрид (8 live + 3 запись) | `real_data/b2c/programs/ai-coding-agents-base.md` |
| `deep-agents` / `deep-agents-advanced` | Deep Agents: продвинутая разработка ИИ-агентов | 44 990 | 4 из 4 | продвинутый | online live | `real_data/b2c/programs/deep-agents-advanced.md` |

> **Дубль-кандидат:** `aidd-program.md` — ещё одно описание fullstack-направления без явной цены, с другим числом занятий (12 вместо 10). Подробнее — в секции 5.

### Комбо

| id | Название | Цена (₽) | Состав | Файл |
|----|----------|----------|--------|------|
| `ai-agents-combo` | Комбо «ИИ-агенты»: траектория от 0 до эксперта | 59 990 | vibe-coding + fullstack-aidd + agents + deep-agents | `real_data/b2c/programs/ai-agents-combo.md` |

### B2B направления

| Направление | Описание | Цена | Файл |
|-------------|----------|------|------|
| Корпоративное обучение | AI-driven разработка, агенты, RAG, production-практики для команд | по запросу | `real_data/b2b/corporate-training.md` |
| Разработка под заказ | Ассистенты, RAG-системы, MCP-интеграции | по запросу | `real_data/b2b/corporate-training.md` |
| Консультации и аудит | Зрелость команды, выбор стека, пилоты | по запросу | `real_data/b2b/corporate-training.md` |

### Модули (темы из программ)

| Тема | Курс-источник | Файл |
|------|---------------|------|
| AI-driven методология / Cursor | vibe-coding, fullstack-aidd, agents, deep-agents | все программы |
| LLM API / промпт-инжиниринг | vibe-coding, agents, fullstack-aidd | все программы |
| RAG (базовый pipeline) | agents | ai-coding-agents-base.md |
| Advanced RAG (Self-RAG, Agentic RAG, Hybrid Search) | agents | ai-coding-agents-base.md |
| Векторные БД (ChromaDB, Qdrant) | agents, deep-agents | ai-coding-agents-base.md, deep-agents-advanced.md |
| Графовые БД / GraphRAG | deep-agents | deep-agents-advanced.md |
| Мультимодальный RAG | deep-agents | deep-agents-advanced.md |
| LangChain / LangGraph | agents, deep-agents | ai-coding-agents-base.md, deep-agents-advanced.md |
| MCP | agents, fullstack-aidd, deep-agents | все три |
| ReAct | vibe-coding, agents | ai-coding-intensive-cursor.md, ai-coding-agents-base.md |
| Tool calling / инструменты агента | agents | ai-coding-agents-base.md |
| Память агента (краткосрочная/долгосрочная) | agents, deep-agents | ai-coding-agents-base.md, deep-agents-advanced.md |
| Human-in-the-loop (HITL) | agents, deep-agents | ai-coding-agents-base.md, deep-agents-advanced.md |
| Мультиагентные системы (Network, Supervisor, Hierarchical) | agents, deep-agents | оба |
| Deep Agents (planning, skills, subagents) | deep-agents | deep-agents-advanced.md |
| Context Engineering | deep-agents | deep-agents-advanced.md |
| A2A / A2UI протоколы | deep-agents | deep-agents-advanced.md |
| Evaluation / Evals (RAGAS, DeepEval, LLM-as-Judge) | agents, deep-agents | оба |
| Red teaming / безопасность | agents, deep-agents | оба |
| Prompt Management / версионирование | deep-agents | deep-agents-advanced.md |
| FastAPI / Backend API | fullstack-aidd | ai-driven-fullstack.md |
| PostgreSQL / ORM | fullstack-aidd | ai-driven-fullstack.md |
| Frontend (React/Next.js) | fullstack-aidd | ai-driven-fullstack.md |
| Docker / DevOps | fullstack-aidd | ai-driven-fullstack.md |
| CI/CD (GitHub Actions) | fullstack-aidd | ai-driven-fullstack.md |
| Observability (LangSmith/LangFuse, Prometheus, Grafana) | agents, fullstack-aidd | оба |
| Мультимодальность (голос, изображения) | vibe-coding, agents | оба |
| Датасет-менеджмент | deep-agents | deep-agents-advanced.md |

### Аудитории

| Аудитория | id | Курсы | Файл |
|-----------|----|-------|------|
| Продакты, дизайнеры, менеджеры (без кода) | `non-dev` | vibe-coding | ai-coding-intensive-cursor.md |
| Разработчики, архитекторы, Tech Lead | `dev` | все B2C курсы | все программы |
| C-level / фаундеры / стартаперы | `executive` | vibe-coding | ai-coding-intensive-cursor.md |
| Команды разработки (B2B, мин. группа) | `team` | корпоративное обучение | corporate-training.md |
| ML/AI инженеры | `ai-engineer` | agents, deep-agents | ai-coding-agents-base.md |

### Форматы обучения

| Формат | id | Длительность | Файл |
|--------|----|--------------|------|
| Видеокурс (запись) | `self-paced` | — | ai-coding-intensive-cursor.md, ai-driven-fullstack.md |
| Гибрид (live + запись) | `hybrid` | 1,5 мес. | ai-coding-agents-base.md |
| Online live | `live` | 2 мес. | deep-agents-advanced.md |
| Воркшоп / интенсив | `workshop` | 3–5 дней | ai-coding-agents-base.md (производный формат) |
| Корпоративная программа | `corporate` | по согласованию | real_data/b2b/corporate-training.md |
| Менторинг | `mentoring` | индивидуально | ai-coding-agents-base.md (производный формат) |

---

## 2. Связи явные и неявные

### Явные рёбра

| Источник | Тип | Цель | Источник данных |
|----------|-----|------|-----------------|
| (ai-agents-combo) | `INCLUDES` | (vibe-coding) | ai-agents-combo.md: «Ступень 1» |
| (ai-agents-combo) | `INCLUDES` | (fullstack-aidd) | ai-agents-combo.md: «Ступень 2» |
| (ai-agents-combo) | `INCLUDES` | (agents) | ai-agents-combo.md: «Ступень 3» |
| (ai-agents-combo) | `INCLUDES` | (deep-agents) | ai-agents-combo.md: «Ступень 4» |
| (vibe-coding) | `RECOMMENDED_BEFORE` | (fullstack-aidd) | ai-agents-combo.md: последовательность ступеней |
| (fullstack-aidd) | `RECOMMENDED_BEFORE` | (agents) | ai-agents-combo.md: последовательность ступеней |
| (agents) | `RECOMMENDED_BEFORE` | (deep-agents) | ai-agents-combo.md + faq-b2c.md: «кто уже прошёл базовый курс» |

### Неявные рёбра — покрытие тем (Course → Theme)

| Источник | Тип | Цель |
|----------|-----|------|
| (vibe-coding) | `COVERS` | (AI-driven методология) |
| (vibe-coding) | `COVERS` | (ReAct) |
| (vibe-coding) | `COVERS` | (Мультимодальность) |
| (fullstack-aidd) | `COVERS` | (AI-driven методология) |
| (fullstack-aidd) | `COVERS` | (FastAPI) |
| (fullstack-aidd) | `COVERS` | (PostgreSQL) |
| (fullstack-aidd) | `COVERS` | (Frontend React/Next.js) |
| (fullstack-aidd) | `COVERS` | (Docker/DevOps) |
| (fullstack-aidd) | `COVERS` | (CI/CD) |
| (fullstack-aidd) | `COVERS` | (Observability) |
| (fullstack-aidd) | `COVERS` | (MCP) |
| (agents) | `COVERS` | (LangChain/LangGraph) |
| (agents) | `COVERS` | (RAG базовый) |
| (agents) | `COVERS` | (Advanced RAG) |
| (agents) | `COVERS` | (Векторные БД) |
| (agents) | `COVERS` | (Tool calling) |
| (agents) | `COVERS` | (Память агента) |
| (agents) | `COVERS` | (HITL) |
| (agents) | `COVERS` | (Мультиагентные системы) |
| (agents) | `COVERS` | (Evaluation/Evals) |
| (agents) | `COVERS` | (Безопасность/guardrails) |
| (agents) | `COVERS` | (MCP) |
| (agents) | `COVERS` | (Observability) |
| (deep-agents) | `COVERS` | (GraphRAG) |
| (deep-agents) | `COVERS` | (Графовые БД) |
| (deep-agents) | `COVERS` | (Мультимодальный RAG) |
| (deep-agents) | `COVERS` | (Context Engineering) |
| (deep-agents) | `COVERS` | (Deep Agents: planning/skills/subagents) |
| (deep-agents) | `COVERS` | (Датасет-менеджмент) |
| (deep-agents) | `COVERS` | (Prompt Management) |
| (deep-agents) | `COVERS` | (A2A / A2UI) |
| (deep-agents) | `COVERS` | (Red teaming) |

### Неявные рёбра — концептуальные зависимости (Theme → Theme)

| Источник | Тип | Цель | Обоснование |
|----------|-----|------|-------------|
| (GraphRAG) | `REQUIRES` | (RAG базовый) | GraphRAG — расширение RAG-паттерна |
| (GraphRAG) | `REQUIRES` | (Векторные БД) | GraphRAG использует векторный поиск как одну из ног |
| (GraphRAG) | `REQUIRES` | (Графовые БД) | Вторая нога GraphRAG — обход графа |
| (Advanced RAG) | `REQUIRES` | (RAG базовый) | Advanced RAG строится на базовом pipeline |
| (Мультиагентные системы) | `REQUIRES` | (LangChain/LangGraph) | Реализация через LangGraph |
| (Мультиагентные системы) | `REQUIRES` | (Tool calling) | Агенты взаимодействуют через инструменты |
| (Deep Agents) | `REQUIRES` | (Мультиагентные системы) | Deep Agents — продвинутые паттерны над мультиагентами |
| (HITL) | `REQUIRES` | (ReAct) | HITL — прерывание ReAct-цикла |
| (Agentic RAG) | `REQUIRES` | (RAG базовый) | Агентный RAG = RAG + planning |
| (Agentic RAG) | `REQUIRES` | (Tool calling) | Агентный RAG использует tools для итеративного поиска |
| (Context Engineering) | `REQUIRES` | (MCP) | Контекст через внешние источники via MCP |
| (Evaluation) | `REQUIRES` | (Observability) | Метрики строятся поверх трейсов |

### Неявные рёбра — аудитории

| Источник | Тип | Цель |
|----------|-----|------|
| (vibe-coding) | `TARGETS` | (non-dev) |
| (vibe-coding) | `TARGETS` | (executive) |
| (vibe-coding) | `TARGETS` | (dev) |
| (fullstack-aidd) | `TARGETS` | (dev) |
| (agents) | `TARGETS` | (dev) |
| (agents) | `TARGETS` | (ai-engineer) |
| (deep-agents) | `TARGETS` | (ai-engineer) |
| (корпоративное обучение) | `TARGETS` | (team) |

---

## 3. Вопросы, плохо покрываемые flat RAG

### Multi-hop (≥ 6)

| # | Вопрос | Почему Qdrant-hybrid промахнётся |
|---|--------|----------------------------------|
| MH-1 | «Что нужно пройти перед deep-agents?» | Требует обхода цепочки RECOMMENDED_BEFORE (3 прыжка от vibe-coding до deep-agents); flat RAG вернёт описание deep-agents без prerequisite-цепочки |
| MH-2 | «Какие темы охватывает комбо целиком?» | Путь: Combo→[INCLUDES]→Course→[COVERS]→Theme (2 прыжка × 4 курса); flat RAG вернёт описание комбо, темы курсов окажутся разбросаны по 4 отдельным чанкам |
| MH-3 | «Через какой курс добраться до изучения GraphRAG?» | Нужно: (GraphRAG)←[COVERS]←(deep-agents)←[RECOMMENDED_BEFORE]←(agents)←...; flat RAG найдёт упоминания GraphRAG, но не построит путь обучения |
| MH-4 | «Покрывает ли курс agents темы, на которые опирается deep-agents?» | Требует пересечения COVERS(agents) ∩ REQUIRES-зависимостей тем deep-agents; flat RAG не выполняет set-intersection по нескольким узлам |
| MH-5 | «Входит ли курс с Векторными БД в комбо?» | Путь: (Векторные БД)←[COVERS]←(agents)←[INCLUDES]←(ai-agents-combo); поиск по embedding найдёт релевантные чанки, но не докажет связь через граф |
| MH-6 | «Какие темы из курса agents являются обязательной базой для GraphRAG, который изучается в deep-agents?» | Требует пересечения: (agents)→[COVERS]→{RAG базовый, Векторные БД} + (GraphRAG)←[REQUIRES]←{Векторные БД, Графовые БД} — часть prerequisites есть только в deep-agents; 3+ узла, flat RAG не построит полное множество |
| MH-7 | «Что общего в темах fullstack-aidd и agents?» | Пересечение множеств COVERS обоих курсов (MCP, Observability, AI-driven методология); flat RAG не делает join по двум узлам |
| MH-8 | «Какой курс я должен закончить, чтобы потом делать мультиагентные системы с A2A?» | (A2A)←[COVERS]←(deep-agents)←[RECOMMENDED_BEFORE]←(agents)←...; многошаговая цепочка, flat RAG её не восстановит |

### Global (≥ 4)

| # | Вопрос | Почему Qdrant-hybrid промахнётся |
|---|--------|----------------------------------|
| GL-1 | «Сколько курсов в каталоге и какие?» | COUNT агрегат по всем Course-узлам; flat RAG не агрегирует, может пропустить курсы из разных чанков/файлов |
| GL-2 | «Какие форматы обучения предлагает LLMStart?» | Форматы разбросаны по 4 файлам (self-paced, hybrid, live, corporate, workshop, mentoring); поиск вернёт ближайший чанк, не полный список |
| GL-3 | «В каких курсах встречается тема MCP?» | MCP упоминается в fullstack-aidd, agents и deep-agents; flat RAG не даст полный список, вернёт чанки с наивысшим сходством |
| GL-4 | «Какие курсы подходят для менеджеров без опыта программирования?» | Нужен агрегат по TARGETS(Audience=non-dev); только vibe-coding явно указывает эту аудиторию, остальные нет — flat RAG смешает ответы |
| GL-5 | «Какова суммарная продолжительность всех ступеней комбо в академических часах?» | Суммирование численных свойств модулей (80 + 80 + 104 ак. часа у agents/deep-agents + интенсив) по нескольким узлам; flat RAG не агрегирует числа |

### Single-hop (flat RAG справляется)

| # | Вопрос | Почему flat RAG хорош |
|---|--------|----------------------|
| SH-1 | «Сколько стоит курс agents?» | Факт в одном чанке (39 990 ₽), прямой lookup по id |
| SH-2 | «Что изучают в Теме 5 курса agents (мониторинг RAG)?» | Содержание темы 5 сосредоточено в одном чанке ai-coding-agents-base.md |
| SH-3 | «Кто ведёт Deep Agents?» | Факт (Смирнов Сергей, Кожин Александр) лежит в одном чанке deep-agents-advanced.md |

---

## 4. Черновик схемы

### Узлы (Node Labels)

| Метка | Ключевые свойства |
|-------|-------------------|
| `Course` | `id` (slug), `title`, `price_rub`, `level` (intensive/intermediate/advanced), `format` (self-paced/hybrid/live), `duration_weeks`, `lessons_count`, `segment` (b2c/b2b/both) |
| `Combo` | `id`, `title`, `price_rub`, `discount_pct`, `description_short` |
| `Theme` | `id` (нормализованный slug), `name`, `aliases` (list) |
| `Audience` | `id`, `role` (dev/non-dev/executive/team/ai-engineer), `segment` (b2c/b2b) |
| `Format` | `id`, `name`, `duration_days_min`, `duration_days_max` |
| ~~`Expert`~~ | ~~`id`, `name`, `title`, `telegram`~~ | убран из схемы (Task 05) |

> `Module` — не выделяется на текущем объёме; темы прикреплены напрямую к Course. Вводить при расширении каталога.

### Рёбра (Relationship Types)

| Тип | Направление | Свойства |
|-----|-------------|----------|
| `INCLUDES` | (Combo)→(Course) | `step_order` (1–4) |
| `RECOMMENDED_BEFORE` | (Course)→(Course) | `mandatory` (bool), `source` (explicit/implicit) |
| `COVERS` | (Course)→(Theme) | `depth` (intro/core/advanced) |
| `REQUIRES` | (Theme)→(Theme) | — |
| `TARGETS` | (Course)→(Audience) | — |
| `AVAILABLE_AS` | (Course)→(Format) | — |
| ~~`TAUGHT_BY`~~ | ~~(Course)→(Expert)~~ | убран из схемы (Task 05) |

### Boundary rule (граф vs Qdrant)

**Граф (Neo4j):** структурные связи (RECOMMENDED_BEFORE, INCLUDES, COVERS, REQUIRES, TARGETS), короткие свойства для фильтрации (price_rub, level, format, segment, step_order).

**Qdrant:** полные описания программ, тексты тем занятий, FAQ, отзывы, описания итоговых проектов — всё для семантического поиска. Связь по `id` (slug).

---

## 5. Кандидаты на entity resolution и нестыковки данных

### 5.1 Дубль fullstack-программы в двух файлах (критично)

| Атрибут | `ai-driven-fullstack.md` | `aidd-program.md` |
|---------|--------------------------|-------------------|
| Название | AI-driven Fullstack разработка | Fullstack AI-driven разработка |
| Цена | 39 990 ₽ | не указана |
| Занятий | 10 | 12 |
| Длительность | ~1,5 мес. | 2 мес. |
| Файл | `real_data/b2c/programs/ai-driven-fullstack.md` | `real_data/b2c/programs/aidd-program.md` |

**Гипотезы:** (a) aidd-program.md — обновлённая/расширенная версия курса; (b) B2B адаптация с другим объёмом.  
**Решение при импорте:** один узел `Course(fullstack-aidd)`, свойство `lessons_count` взять из основного файла (ai-driven-fullstack.md); `aidd-program.md` обработать как вариативный формат или дублирующий документ после уточнения у владельца данных.

### 5.2 Расхождение суммы в ai-agents-combo.md

В одном файле два противоречивых числа:

| Место в файле | Значение |
|---------------|----------|
| Таблица «Сумма курсов по отдельности» | **134 960 ₽** |
| Текст тела: «Интенсив + Fullstack + Agents + Deep Agents =» | **139 960 ₽** (14 990 + 39 990 + 39 990 + 44 990) |

Арифметика текста верна: 14 990 + 39 990 + 39 990 + 44 990 = 139 960 ₽.  
Таблица занижена на 5 000 ₽ — редакционная ошибка.  
**Итог:** источник правды — цены в отдельных файлах курсов; при MERGE суммировать из них, не из таблицы комбо.

### 5.3 Расхождение цен: catalog.json vs real_data (все цены в копейках)

Цены в `data/b2c/catalog.json` выражены в копейках. При пересчёте в рубли они **не совпадают** с real_data:

| Курс | catalog.json (копейки → ₽) | real_data (₽) | Δ |
|------|----------------------------|----------------|---|
| vibe-coding-intensive | 2 900 000 к. → 29 000 ₽ | 14 990 ₽ | −14 010 ₽ |
| fullstack-aidd | 4 900 000 к. → 49 000 ₽ | 39 990 ₽ | −9 010 ₽ |
| agents | 3 900 000 к. → 39 000 ₽ | 39 990 ₽ | −990 ₽ |
| deep-agents | 5 900 000 к. → 59 000 ₽ | 44 990 ₽ | −14 010 ₽ |
| ai-agents-combo | 9 900 000 к. → 99 000 ₽ | 59 990 ₽ | −39 010 ₽ |

**Вывод:** `catalog.json` содержит устаревшие/тестовые цены. При построении графа брать цены из `real_data/b2c/programs/*.md`.

### 5.4 Алиасы курсов — расхождение slug-ов

| Slug в catalog.json | Slug в real_data URL / файле | Каноничный |
|---------------------|------------------------------|------------|
| `vibe-coding-intensive` | `vibe-coding` (URL: `/vibe-coding/`) | → `vibe-coding` |
| `agents` | `ai-coding-agents-base` (файл) | → `agents` (URL: `/agents/`) |
| `fullstack-aidd` | `ai-driven-fullstack` (файл) | → `fullstack-aidd` (URL: `/fullstack-aidd/`) |
| `deep-agents` | `deep-agents-advanced` (файл) | → `deep-agents` (URL: `/deep-agents/`) |

При MERGE использовать URL-slug как канонический ключ `id`; имена файлов — алиасы.

### 5.5 Алиасы тем — кандидаты на merge

| Алиасы | Канонический `Theme.id` |
|--------|------------------------|
| «RAG», «RAG-система», «RAG по базе знаний», «Retrieval-Augmented Generation» | `rag-basic` |
| «Advanced RAG», «Self-RAG», «Agentic RAG» | `rag-advanced` |
| «observability», «LangSmith/LangFuse», «мониторинг», «трейсинг» | `observability` |
| «AI-driven методология», «AI-driven подход», «AIDD» | `ai-driven-methodology` |
| «мультиагентные системы», «multi-agent», «мультиагентные паттерны» | `multi-agent` |
| «контекст-инжиниринг», «context engineering», «промпт-инжиниринг» | разделить на два: `context-engineering`, `prompt-engineering` |

### 5.6 Consultation — исчез из real_data

В `data/b2c/catalog.json` есть продукт `consultation` (1 500 000 копеек = 15 000 ₽).  
В `real_data/b2c/programs/` файла consultation нет.  
В `real_data/b2b/corporate-training.md` есть «Консультации и аудит» как B2B-направление без цены.  
**Решение:** не включать `consultation` как отдельный `Course`-узел без подтверждения из real_data; хранить как `Service`-узел или пропустить до уточнения.

