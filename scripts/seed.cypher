// ============================================================
// seed.cypher — Граф каталога курсов LLMStart.ru
// Источник:  data/real_data/b2c/programs/*.md + analysis.md
// Запуск:    make graph-seed
// Идемпотентен: MERGE + IF NOT EXISTS (не CREATE)
// ============================================================


// ─── 1. CONSTRAINTS ─────────────────────────────────────────
// UNIQUE на id (slug) — не на name, он может совпадать
// Должны быть созданы ДО первого MERGE
// ────────────────────────────────────────────────────────────

CREATE CONSTRAINT course_id_unique   IF NOT EXISTS
  FOR (n:Course)   REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT combo_id_unique    IF NOT EXISTS
  FOR (n:Combo)    REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT theme_id_unique    IF NOT EXISTS
  FOR (n:Theme)    REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT audience_id_unique IF NOT EXISTS
  FOR (n:Audience) REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT format_id_unique   IF NOT EXISTS
  FOR (n:Format)   REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT level_id_unique    IF NOT EXISTS
  FOR (n:Level)    REQUIRE n.id IS UNIQUE;


// ─── 2. INDEXES ──────────────────────────────────────────────

CREATE INDEX course_price_idx IF NOT EXISTS
  FOR (c:Course) ON (c.priceRub);

CREATE INDEX course_level_idx IF NOT EXISTS
  FOR (c:Course) ON (c.level);

CREATE FULLTEXT INDEX theme_name_ft IF NOT EXISTS
  FOR (t:Theme) ON EACH [t.name, t.id];


// ─── 3. LEVEL ────────────────────────────────────────────────

MERGE (n:Level {id: 'intensive'})
SET n.name = 'Интенсив', n.sortOrder = 1;

MERGE (n:Level {id: 'intermediate'})
SET n.name = 'Средний', n.sortOrder = 2;

MERGE (n:Level {id: 'advanced'})
SET n.name = 'Продвинутый', n.sortOrder = 3;


// ─── 4. FORMAT ───────────────────────────────────────────────

MERGE (n:Format {id: 'self-paced'})
SET n.name = 'Видеокурс (запись)';

MERGE (n:Format {id: 'hybrid'})
SET n.name = 'Гибрид (live + запись)';

MERGE (n:Format {id: 'live'})
SET n.name = 'Online live';

MERGE (n:Format {id: 'workshop'})
SET n.name = 'Воркшоп / интенсив',
    n.durationDaysMin = 3,
    n.durationDaysMax = 5;

MERGE (n:Format {id: 'corporate'})
SET n.name = 'Корпоративная программа';

MERGE (n:Format {id: 'mentoring'})
SET n.name = 'Менторинг';


// ─── 5. AUDIENCE ─────────────────────────────────────────────

MERGE (n:Audience {id: 'non-dev'})
SET n.role = 'non-dev', n.segment = 'b2c';

MERGE (n:Audience {id: 'dev'})
SET n.role = 'dev', n.segment = 'b2c';

MERGE (n:Audience {id: 'executive'})
SET n.role = 'executive', n.segment = 'b2c';

MERGE (n:Audience {id: 'team'})
SET n.role = 'team', n.segment = 'b2b';

MERGE (n:Audience {id: 'ai-engineer'})
SET n.role = 'ai-engineer', n.segment = 'b2c';


// ─── 6. THEME (29 узлов) ─────────────────────────────────────
// aliases — list<string>; source = 'seed' для diff с авто-извлечением
// ────────────────────────────────────────────────────────────

MERGE (t:Theme {id: 'ai-driven-methodology'})
SET t.name    = 'AI-driven методология',
    t.aliases = ['AI-driven подход', 'AIDD', 'AI-driven development'],
    t.source  = 'seed';

MERGE (t:Theme {id: 'llm-api'})
SET t.name    = 'LLM API и промпт-инжиниринг',
    t.aliases = ['LLM API', 'промпт-инжиниринг', 'prompt engineering',
                 'контекст-инжиниринг', 'context engineering'],
    t.source  = 'seed';

MERGE (t:Theme {id: 'react-agent'})
SET t.name    = 'ReAct паттерн',
    t.aliases = ['ReAct', 'Reasoning+Acting', 'ReAct pattern'],
    t.source  = 'seed';

MERGE (t:Theme {id: 'multimodality'})
SET t.name    = 'Мультимодальность',
    t.aliases = ['голос', 'изображения', 'мультимодальные возможности',
                 'speech', 'vision', 'multimodal'],
    t.source  = 'seed';

MERGE (t:Theme {id: 'rag-basic'})
SET t.name    = 'RAG (базовый pipeline)',
    t.aliases = ['RAG', 'RAG-система', 'RAG pipeline',
                 'Retrieval-Augmented Generation', 'retrieval augmented generation'],
    t.source  = 'seed';

MERGE (t:Theme {id: 'rag-advanced'})
SET t.name    = 'Advanced RAG',
    t.aliases = ['Self-RAG', 'Agentic RAG', 'Hybrid Search',
                 'Query Transformation', 'Advanced RAG', 'Query Routing'],
    t.source  = 'seed';

MERGE (t:Theme {id: 'vector-db'})
SET t.name    = 'Векторные базы данных',
    t.aliases = ['ChromaDB', 'Qdrant', 'векторные БД',
                 'embedding', 'vector store', 'векторное хранилище'],
    t.source  = 'seed';

MERGE (t:Theme {id: 'langchain-langgraph'})
SET t.name    = 'LangChain / LangGraph',
    t.aliases = ['LangChain', 'LangGraph', 'LangSmith', 'langgraph'],
    t.source  = 'seed';

MERGE (t:Theme {id: 'tool-calling'})
SET t.name    = 'Tool calling',
    t.aliases = ['tool calling', 'инструменты агента', 'function calling',
                 'tool use', 'external tools'],
    t.source  = 'seed';

MERGE (t:Theme {id: 'agent-memory'})
SET t.name    = 'Память агента',
    t.aliases = ['краткосрочная память', 'долгосрочная память',
                 'memory', 'agent memory', 'long-term memory'],
    t.source  = 'seed';

MERGE (t:Theme {id: 'hitl'})
SET t.name    = 'Human-in-the-loop',
    t.aliases = ['HITL', 'human-in-the-loop', 'human in the loop'],
    t.source  = 'seed';

MERGE (t:Theme {id: 'multi-agent'})
SET t.name    = 'Мультиагентные системы',
    t.aliases = ['мультиагентные паттерны', 'multi-agent',
                 'Network', 'Supervisor', 'Hierarchical',
                 'мультиагентные архитектуры'],
    t.source  = 'seed';

MERGE (t:Theme {id: 'evaluation'})
SET t.name    = 'Evaluation / Evals',
    t.aliases = ['RAGAS', 'DeepEval', 'LLM-as-Judge', 'evals',
                 'оценка качества', 'evaluation framework',
                 'Task Tool Trajectory Topic'],
    t.source  = 'seed';

MERGE (t:Theme {id: 'security-guardrails'})
SET t.name    = 'Безопасность / guardrails',
    t.aliases = ['guardrails', 'LLMGuard', 'Giskard',
                 'adversarial prompting', 'jailbreaking',
                 'prompt injection', 'red teaming'],
    t.source  = 'seed';

MERGE (t:Theme {id: 'mcp'})
SET t.name    = 'Model Context Protocol',
    t.aliases = ['MCP', 'Model Context Protocol', 'MCP-сервер',
                 'MCP server', 'MCP tools'],
    t.source  = 'seed';

MERGE (t:Theme {id: 'observability'})
SET t.name    = 'Observability',
    t.aliases = ['LangSmith', 'LangFuse', 'мониторинг', 'трейсинг',
                 'Prometheus', 'Grafana', 'tracing', 'logging'],
    t.source  = 'seed';

MERGE (t:Theme {id: 'fastapi-backend'})
SET t.name    = 'FastAPI / Backend API',
    t.aliases = ['FastAPI', 'Backend API', 'REST API',
                 'API-сервис', 'uvicorn'],
    t.source  = 'seed';

MERGE (t:Theme {id: 'postgresql'})
SET t.name    = 'PostgreSQL / ORM',
    t.aliases = ['PostgreSQL', 'ORM', 'база данных',
                 'Alembic', 'SQLAlchemy', 'asyncpg'],
    t.source  = 'seed';

MERGE (t:Theme {id: 'frontend-dev'})
SET t.name    = 'Frontend разработка',
    t.aliases = ['React', 'Next.js', 'веб-интерфейс', 'SPA',
                 'Tailwind', 'shadcn'],
    t.source  = 'seed';

MERGE (t:Theme {id: 'docker-devops'})
SET t.name    = 'Docker / DevOps',
    t.aliases = ['Docker', 'контейнеризация', 'DevOps',
                 'docker-compose', 'Dockerfile'],
    t.source  = 'seed';

MERGE (t:Theme {id: 'cicd'})
SET t.name    = 'CI/CD',
    t.aliases = ['CI/CD', 'GitHub Actions', 'pipeline',
                 'continuous integration'],
    t.source  = 'seed';

MERGE (t:Theme {id: 'graph-db'})
SET t.name    = 'Графовые базы данных',
    t.aliases = ['Neo4j', 'графовые БД', 'граф знаний',
                 'Knowledge Graph', 'graph database'],
    t.source  = 'seed';

MERGE (t:Theme {id: 'graphrag'})
SET t.name    = 'GraphRAG',
    t.aliases = ['GraphRAG', 'граф + RAG',
                 'гибридный поиск граф+вектор', 'graph RAG'],
    t.source  = 'seed';

MERGE (t:Theme {id: 'multimodal-rag'})
SET t.name    = 'Мультимодальный RAG',
    t.aliases = ['мультимодальный RAG', 'Vision API',
                 'визуально-насыщенные документы', 'multimodal RAG'],
    t.source  = 'seed';

MERGE (t:Theme {id: 'context-engineering'})
SET t.name    = 'Context Engineering',
    t.aliases = ['управление контекстом', 'Deep Context Engineering',
                 'dynamic context', 'context management'],
    t.source  = 'seed';

MERGE (t:Theme {id: 'deep-agents-skills'})
SET t.name    = 'Deep Agents (planning/skills/subagents)',
    t.aliases = ['planning', 'skills', 'subagents',
                 'task decomposition', 'checkpoint/resume',
                 'long-term memory', 'deep agents'],
    t.source  = 'seed';

MERGE (t:Theme {id: 'dataset-management'})
SET t.name    = 'Датасет-менеджмент',
    t.aliases = ['annotation queues', 'валидационные датасеты',
                 'data-driven подход', 'dataset management'],
    t.source  = 'seed';

MERGE (t:Theme {id: 'prompt-management'})
SET t.name    = 'Prompt Management',
    t.aliases = ['версионирование промптов', 'A/B тесты промптов',
                 'Prompt Playground', 'prompt versioning'],
    t.source  = 'seed';

MERGE (t:Theme {id: 'a2a-a2ui'})
SET t.name    = 'A2A / A2UI протоколы',
    t.aliases = ['Agent-to-Agent', 'Agent-to-UI', 'A2A', 'A2UI',
                 'масштабирование агентов'],
    t.source  = 'seed';


// ─── 7. COURSE (4 ступени) ───────────────────────────────────
// Цены — из real_data/*.md (не catalog.json)
// Entity resolution: aidd-program.md → fullstack-aidd (один узел)
// ────────────────────────────────────────────────────────────

MERGE (c:Course {id: 'vibe-coding'})
SET c.title        = 'Интенсив AI-кодинг ИИ-агентов в Cursor',
    c.priceRub     = 14990,
    c.level        = 'intensive',
    c.format       = 'self-paced',
    c.lessonsCount = 4,
    c.segment      = 'b2c'
REMOVE c.academicHours;

MERGE (c:Course {id: 'fullstack-aidd'})
SET c.title        = 'AI-driven Fullstack разработка',
    c.priceRub     = 39990,
    c.level        = 'intermediate',
    c.format       = 'self-paced',
    c.durationWeeks = 6,
    c.lessonsCount = 10,
    c.academicHours = 80,
    c.segment      = 'b2c';

// agents: источник ai-coding-agents-base.md; id = URL-slug /agents/
MERGE (c:Course {id: 'agents'})
SET c.title        = 'AI-driven разработка ИИ-агентов',
    c.priceRub     = 39990,
    c.level        = 'intermediate',
    c.format       = 'hybrid',
    c.durationWeeks = 6,
    c.lessonsCount = 11,
    c.academicHours = 80,
    c.segment      = 'both';

MERGE (c:Course {id: 'deep-agents'})
SET c.title        = 'Deep Agents: продвинутая разработка ИИ-агентов',
    c.priceRub     = 44990,
    c.level        = 'advanced',
    c.format       = 'live',
    c.durationWeeks = 8,
    c.lessonsCount = 12,
    c.academicHours = 104,
    c.segment      = 'b2c';


// ─── 8. COMBO ────────────────────────────────────────────────
// priceRub 59990; discountPct рассчитан по реальным ценам курсов:
//   14990+39990+39990+44990 = 139960; round(1-59990/139960,2) = 0.57
// Значение 134960 в таблице файла — редакционная ошибка
// ────────────────────────────────────────────────────────────

MERGE (cb:Combo {id: 'ai-agents-combo'})
SET cb.title            = 'Комбо «ИИ-агенты»: траектория от 0 до эксперта',
    cb.priceRub         = 59990,
    cb.discountPct      = 57,
    cb.descriptionShort = 'Единая траектория по AI-driven разработке: от AI-кодинга до production-ready мультиагентных систем';


// ─── 9. AT_LEVEL ─────────────────────────────────────────────

MATCH (c:Course {id: 'vibe-coding'}),   (l:Level {id: 'intensive'})
MERGE (c)-[:AT_LEVEL]->(l);

MATCH (c:Course {id: 'fullstack-aidd'}), (l:Level {id: 'intermediate'})
MERGE (c)-[:AT_LEVEL]->(l);

MATCH (c:Course {id: 'agents'}),         (l:Level {id: 'intermediate'})
MERGE (c)-[:AT_LEVEL]->(l);

MATCH (c:Course {id: 'deep-agents'}),    (l:Level {id: 'advanced'})
MERGE (c)-[:AT_LEVEL]->(l);


// ─── 10. AVAILABLE_AS ────────────────────────────────────────

MATCH (c:Course {id: 'vibe-coding'}),    (f:Format {id: 'self-paced'})
MERGE (c)-[:AVAILABLE_AS]->(f);

MATCH (c:Course {id: 'fullstack-aidd'}), (f:Format {id: 'self-paced'})
MERGE (c)-[:AVAILABLE_AS]->(f);

MATCH (c:Course {id: 'agents'}), (f:Format {id: 'hybrid'})
MERGE (c)-[:AVAILABLE_AS]->(f);

MATCH (c:Course {id: 'agents'}), (f:Format {id: 'workshop'})
MERGE (c)-[:AVAILABLE_AS]->(f);

MATCH (c:Course {id: 'agents'}), (f:Format {id: 'corporate'})
MERGE (c)-[:AVAILABLE_AS]->(f);

MATCH (c:Course {id: 'agents'}), (f:Format {id: 'mentoring'})
MERGE (c)-[:AVAILABLE_AS]->(f);

MATCH (c:Course {id: 'deep-agents'}), (f:Format {id: 'live'})
MERGE (c)-[:AVAILABLE_AS]->(f);


// ─── 11. TARGETS ─────────────────────────────────────────────

MATCH (c:Course {id: 'vibe-coding'}), (a:Audience {id: 'non-dev'})
MERGE (c)-[:TARGETS]->(a);

MATCH (c:Course {id: 'vibe-coding'}), (a:Audience {id: 'executive'})
MERGE (c)-[:TARGETS]->(a);

MATCH (c:Course {id: 'vibe-coding'}), (a:Audience {id: 'dev'})
MERGE (c)-[:TARGETS]->(a);

MATCH (c:Course {id: 'fullstack-aidd'}), (a:Audience {id: 'dev'})
MERGE (c)-[:TARGETS]->(a);

MATCH (c:Course {id: 'agents'}), (a:Audience {id: 'dev'})
MERGE (c)-[:TARGETS]->(a);

MATCH (c:Course {id: 'agents'}), (a:Audience {id: 'ai-engineer'})
MERGE (c)-[:TARGETS]->(a);

MATCH (c:Course {id: 'agents'}), (a:Audience {id: 'team'})
MERGE (c)-[:TARGETS]->(a);

MATCH (c:Course {id: 'deep-agents'}), (a:Audience {id: 'dev'})
MERGE (c)-[:TARGETS]->(a);

MATCH (c:Course {id: 'deep-agents'}), (a:Audience {id: 'ai-engineer'})
MERGE (c)-[:TARGETS]->(a);


// ─── 12. INCLUDES (Combo → Course) ───────────────────────────
// stepOrder = порядок ступени в траектории

MATCH (cb:Combo {id: 'ai-agents-combo'}), (c:Course {id: 'vibe-coding'})
MERGE (cb)-[r:INCLUDES]->(c)
SET r.stepOrder = 1;

MATCH (cb:Combo {id: 'ai-agents-combo'}), (c:Course {id: 'fullstack-aidd'})
MERGE (cb)-[r:INCLUDES]->(c)
SET r.stepOrder = 2;

MATCH (cb:Combo {id: 'ai-agents-combo'}), (c:Course {id: 'agents'})
MERGE (cb)-[r:INCLUDES]->(c)
SET r.stepOrder = 3;

MATCH (cb:Combo {id: 'ai-agents-combo'}), (c:Course {id: 'deep-agents'})
MERGE (cb)-[r:INCLUDES]->(c)
SET r.stepOrder = 4;


// ─── 13. RECOMMENDED_BEFORE (Course → Course) ────────────────
// mandatory: true  = жёсткое требование (явно указано в программе)
// mandatory: false = рекомендация (порядок ступеней)
// source: 'explicit' = указано в ai-agents-combo.md

MATCH (a:Course {id: 'vibe-coding'}),    (b:Course {id: 'fullstack-aidd'})
MERGE (a)-[r:RECOMMENDED_BEFORE]->(b)
SET r.mandatory = false, r.source = 'explicit';

MATCH (a:Course {id: 'fullstack-aidd'}), (b:Course {id: 'agents'})
MERGE (a)-[r:RECOMMENDED_BEFORE]->(b)
SET r.mandatory = false, r.source = 'explicit';

// mandatory=true: deep-agents явно требует базовых знаний LLM и агентов
MATCH (a:Course {id: 'agents'}), (b:Course {id: 'deep-agents'})
MERGE (a)-[r:RECOMMENDED_BEFORE]->(b)
SET r.mandatory = true, r.source = 'explicit';


// ─── 14. COVERS (Course → Theme, 42 рёбра) ───────────────────
// depth: 'intro' | 'core' | 'advanced'
// Batch через UNWIND — один запрос вместо 42 операторов
// ────────────────────────────────────────────────────────────

UNWIND [
  // vibe-coding (4)
  {c: 'vibe-coding', t: 'ai-driven-methodology', depth: 'core'},
  {c: 'vibe-coding', t: 'llm-api',               depth: 'intro'},
  {c: 'vibe-coding', t: 'react-agent',            depth: 'core'},
  {c: 'vibe-coding', t: 'multimodality',          depth: 'core'},
  // fullstack-aidd (9)
  {c: 'fullstack-aidd', t: 'ai-driven-methodology', depth: 'core'},
  {c: 'fullstack-aidd', t: 'llm-api',               depth: 'intro'},
  {c: 'fullstack-aidd', t: 'fastapi-backend',        depth: 'core'},
  {c: 'fullstack-aidd', t: 'postgresql',             depth: 'core'},
  {c: 'fullstack-aidd', t: 'frontend-dev',           depth: 'core'},
  {c: 'fullstack-aidd', t: 'docker-devops',          depth: 'core'},
  {c: 'fullstack-aidd', t: 'cicd',                   depth: 'core'},
  {c: 'fullstack-aidd', t: 'observability',          depth: 'core'},
  {c: 'fullstack-aidd', t: 'mcp',                   depth: 'intro'},
  // agents (15)
  {c: 'agents', t: 'ai-driven-methodology', depth: 'intro'},
  {c: 'agents', t: 'llm-api',               depth: 'core'},
  {c: 'agents', t: 'rag-basic',             depth: 'core'},
  {c: 'agents', t: 'rag-advanced',          depth: 'core'},
  {c: 'agents', t: 'vector-db',             depth: 'core'},
  {c: 'agents', t: 'langchain-langgraph',   depth: 'core'},
  {c: 'agents', t: 'tool-calling',          depth: 'core'},
  {c: 'agents', t: 'agent-memory',          depth: 'core'},
  {c: 'agents', t: 'hitl',                 depth: 'intro'},
  {c: 'agents', t: 'multi-agent',           depth: 'intro'},
  {c: 'agents', t: 'evaluation',            depth: 'core'},
  {c: 'agents', t: 'security-guardrails',   depth: 'core'},
  {c: 'agents', t: 'mcp',                  depth: 'core'},
  {c: 'agents', t: 'observability',         depth: 'core'},
  {c: 'agents', t: 'multimodality',         depth: 'intro'},
  // deep-agents (14)
  {c: 'deep-agents', t: 'ai-driven-methodology', depth: 'intro'},
  {c: 'deep-agents', t: 'graph-db',              depth: 'core'},
  {c: 'deep-agents', t: 'graphrag',              depth: 'core'},
  {c: 'deep-agents', t: 'vector-db',             depth: 'intro'},
  {c: 'deep-agents', t: 'multimodal-rag',        depth: 'core'},
  {c: 'deep-agents', t: 'context-engineering',   depth: 'advanced'},
  {c: 'deep-agents', t: 'deep-agents-skills',    depth: 'advanced'},
  {c: 'deep-agents', t: 'dataset-management',    depth: 'core'},
  {c: 'deep-agents', t: 'prompt-management',     depth: 'core'},
  {c: 'deep-agents', t: 'a2a-a2ui',             depth: 'core'},
  {c: 'deep-agents', t: 'multi-agent',           depth: 'advanced'},
  {c: 'deep-agents', t: 'evaluation',            depth: 'advanced'},
  {c: 'deep-agents', t: 'security-guardrails',   depth: 'advanced'},
  {c: 'deep-agents', t: 'langchain-langgraph',   depth: 'intro'}
] AS row
MATCH (c:Course {id: row.c}), (t:Theme {id: row.t})
MERGE (c)-[r:COVERS]->(t)
SET r.depth = row.depth;


// ─── 15. REQUIRES (Theme → Theme, 12 рёбер) ──────────────────
// Направление: (A)-[:REQUIRES]->(B) = «для изучения A нужна B»
// ────────────────────────────────────────────────────────────

UNWIND [
  {from: 'graphrag',             to: 'rag-basic'},
  {from: 'graphrag',             to: 'vector-db'},
  {from: 'graphrag',             to: 'graph-db'},
  {from: 'rag-advanced',         to: 'rag-basic'},
  {from: 'multimodal-rag',       to: 'rag-basic'},
  {from: 'multimodal-rag',       to: 'multimodality'},
  {from: 'multi-agent',          to: 'langchain-langgraph'},
  {from: 'multi-agent',          to: 'tool-calling'},
  {from: 'deep-agents-skills',   to: 'multi-agent'},
  {from: 'hitl',                 to: 'react-agent'},
  {from: 'context-engineering',  to: 'mcp'},
  {from: 'evaluation',           to: 'observability'}
] AS row
MATCH (t1:Theme {id: row.from}), (t2:Theme {id: row.to})
MERGE (t1)-[:REQUIRES]->(t2);
