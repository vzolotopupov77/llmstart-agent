# Text-to-Graph Extraction — сравнение инструментов

> Task 05 часть В · Sprint 09 GraphRAG  
> Дата: 2026-06-28

## Контекст

Нужно извлечь из markdown-программ курсов только узлы `Course`/`Theme` и рёбра `COVERS`/`REQUIRES` строго по схеме каталога.  
`LLMGraphTransformer` (langchain-experimental) **запрещён** ADR-0010.

---

## Краткие описания

| Инструмент | Описание |
|------------|----------|
| **LLMGraphTransformer** | LangChain-обёртка над LLM: freestyle-извлечение сущностей/связей без жёсткой схемы. Deprecated-путь для Neo4j; в проекте запрещён. |
| **SimpleKGPipeline** | Официальный пайплайн `neo4j-graphrag`: chunking → LLM extraction → запись в Neo4j. Поддерживает `GraphSchema`, structured output, markdown/PDF. |
| **GLiNER** | Zero-shot NER без LLM: извлекает span-метки по списку типов. Хорош для именованных сущностей, слабее на доменных связях `REQUIRES`. |
| **Relik** | Zero-shot relation extraction: пары сущность–сущность–отношение. Требует отдельного NER-шага; схема задаётся вручную. |
| **spaCy NER** | Rule/ML NER по обученной модели. Без LLM, но нужна дообученная модель под русскоязычные темы каталога. |
| **LlamaIndex SchemaLLMPathExtractor** | LLM path extractor с заданной схемой (узлы/рёбра). Альтернатива SimpleKGPipeline при стеке LlamaIndex. |
| **MS GraphRAG** | Microsoft GraphRAG: community detection (Leiden) + global/local summaries. Оверкилл для малого каталога (ADR-0010). |

---

## Таблица сравнения

| Критерий | LLMGraphTransformer | SimpleKGPipeline | GLiNER | Relik | spaCy NER | SchemaLLMPathExtractor | MS GraphRAG |
|----------|---------------------|------------------|--------|-------|-----------|------------------------|-------------|
| **Тип** | LLM prompt | LLM prompt | zero-shot NER | zero-shot RE | rule/ML NER | LLM prompt | LLM pipeline |
| **Schema-constrained** | ❌ freestyle | ✅ `GraphSchema` | ⚠️ частично | ⚠️ частично | ❌ | ✅ | ❌ |
| **Язык** | en/ru | en/ru | en/ru/мультиязычный | en/ru | зависит от модели | en/ru | en |
| **Зависимость** | `langchain-experimental` ⚠️ | `neo4j-graphrag` ✅ | `gliner` | `relik` | `spacy` | `llama-index` | `graphrag` |
| **Требует LLM** | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ |
| **Community summaries** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ (Leiden) |
| **Используется в проекте** | ❌ ЗАПРЕЩЁН | ✅ **выбор** | исследовать | исследовать | fallback | альтернатива | ❌ оверкилл |

---

## Обоснование выбора

**Выбран: `neo4j-graphrag SimpleKGPipeline` (v1.16.0)**

1. **Схема из коробки** — `GraphSchema` с `patterns=[("Course","COVERS","Theme"), ("Theme","REQUIRES","Theme")]` ограничивает LLM только допустимыми типами (при `GRAPH_EXTRACT_STRICT=true` лишние узлы отбрасываются post-processing).
2. **Единый SDK** — тот же пакет для GraphRAG retrieval (Task 06), Text2Cypher, entity resolution (`FuzzyMatchResolver`).
3. **Markdown loader** — нативная поддержка `.md` через `from_file=True`.
4. **OpenRouter** — `OpenAILLM` + `OpenAIEmbeddings` с `base_url` из env.
5. **ADR-0010** — явный запрет `LLMGraphTransformer`; SimpleKGPipeline — рекомендованный replacement.

**Fallback:** LlamaIndex `SchemaLLMPathExtractor` — если SimpleKGPipeline не справится с русскоязычными программами; потребует отдельной интеграции с Neo4j writer.

**Не выбраны:** GLiNER/Relik/spaCy — нет готовой поддержки `REQUIRES`-цепочек между темами без дополнительного пайплайна; MS GraphRAG — community summaries не нужны на 4 курсах.

---

## Параметризация (env)

| Переменная | Назначение |
|------------|------------|
| `GRAPH_EXTRACT_MODEL` | LLM для extraction (default: `OPENAI_MODEL`) |
| `GRAPH_EXTRACT_STRICT` | `true` — drop auto-тем без match в seed aliases |
| `OPENAI_API_KEY` / `OPENAI_BASE_URL` | OpenRouter |
| `EMBEDDING_MODEL` | Embeddings для Chunk-узлов pipeline |

---

## Ссылки

- [neo4j-graphrag KG Builder](https://neo4j.com/docs/neo4j-graphrag-python/current/user_guide_kg_builder.html)
- [ADR-0010 GraphRAG](../../adrs/ADR-0010-graphrag.md)
- [Task 05 plan](../../sprints/sprint-09-graphrag/tasks/05-graph-indexing/plan.md)
- [LlamaIndex SchemaLLMPathExtractor](https://docs.llamaindex.ai/en/stable/examples/index_structs/knowledge_graph/KnowledgeGraphIndex_vs_SchemaLLMPathExtractor/)
