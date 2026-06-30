# Graph Extraction Report
Generated: 2026-06-28T19:30:09Z

## Метрики сравнения: manual seed vs auto extraction

| Метрика | Значение | Пояснение |
|---------|----------|-----------|
| Manual seed | 29 тем | Ручной seed (`scripts/seed.cypher`), authoritative |
| Auto extract ops | 743 | 218 merge + 525 drop (chunk-level дубли) |
| Exact recall | 48% (14/29) | `Theme.id` LLM = seed id без alias-словаря |
| Semantic recall | 97% (28/29) | Seed-темы, сопоставленные через alias-index при merge |
| Proliferation | ~26× | Chunk-узлов LLM на одну seed-тему (743/29) |
| Corpus alias recall | 73% | Alias seed-тем в исходных `.md` (не LLM) |

**Вывод:** **Exact recall 48%** — половина узлов LLM совпадает со slug seed без alias-словаря; остальное — `RAG`→`rag-basic`, `LangGraph`→`langchain-langgraph`, `evals`→`evaluation`. **Semantic recall 97%** (28/29) — entity resolution сопоставил почти все seed-темы; strict mode отбросил **525** chunk-шумовых узлов (merge-операций: **218**). **Proliferation ~26×** — LLM создаёт ~26 chunk-level Theme на каждую seed-тему (дубли по чанкам); без ER граф был бы нечитаем. **Corpus alias recall 73%** — средняя доля alias seed-тем, найденных в исходных `.md` (независимо от LLM). **Не сопоставлено:** `graph-db` — оставить seed, при необходимости дополнить aliases. Продакшен: alias-словарь (`graph_common.py`) + `GRAPH_EXTRACT_STRICT=true` — см. `data/graph/entity-resolution.md`.

## Summary (граф после extract)
| Metric | Value |
|--------|-------|
| Theme nodes | 29 |
| REQUIRES edges | 12 |
| COVERS edges | 48 |
| Auto themes (new, in graph) | 0 |
| Extract merge ops | 218 |
| Seed confirmed by extract | 28 |
| Seed without extract match | 1 |
| Avg corpus alias recall | 0.73 |

## Diff: авто-темы без seed-совпадения
| theme_id | name | coveredBy |
|----------|------|-----------|
| — | — | — |

## Diff: seed-темы без авто-подтверждения
| theme_id | name |
|----------|------|
| graph-db | Графовые базы данных |

## Seed-темы, подтверждённые extraction (merge)
| theme_id | name |
|----------|------|
| a2a-a2ui | A2A / A2UI протоколы |
| agent-memory | Память агента |
| ai-driven-methodology | AI-driven методология |
| cicd | CI/CD |
| context-engineering | Context Engineering |
| dataset-management | Датасет-менеджмент |
| deep-agents-skills | Deep Agents (planning/skills/subagents) |
| docker-devops | Docker / DevOps |
| evaluation | Evaluation / Evals |
| fastapi-backend | FastAPI / Backend API |
| frontend-dev | Frontend разработка |
| graphrag | GraphRAG |
| hitl | Human-in-the-loop |
| langchain-langgraph | LangChain / LangGraph |
| llm-api | LLM API и промпт-инжиниринг |
| mcp | Model Context Protocol |
| multi-agent | Мультиагентные системы |
| multimodal-rag | Мультимодальный RAG |
| multimodality | Мультимодальность |
| observability | Observability |
| postgresql | PostgreSQL / ORM |
| prompt-management | Prompt Management |
| rag-advanced | Advanced RAG |
| rag-basic | RAG (базовый pipeline) |
| react-agent | ReAct паттерн |
| security-guardrails | Безопасность / guardrails |
| tool-calling | Tool calling |
| vector-db | Векторные базы данных |

## Corpus alias recall по seed-темам
| theme_id | aliases_total | aliases_found | recall |
|----------|---------------|---------------|--------|
| a2a-a2ui | 9 | 6 | 0.67 |
| agent-memory | 7 | 4 | 0.57 |
| ai-driven-methodology | 21 | 17 | 0.81 |
| cicd | 6 | 4 | 0.67 |
| context-engineering | 11 | 10 | 0.91 |
| dataset-management | 8 | 5 | 0.62 |
| deep-agents-skills | 16 | 14 | 0.88 |
| docker-devops | 10 | 8 | 0.8 |
| evaluation | 13 | 9 | 0.69 |
| fastapi-backend | 12 | 9 | 0.75 |
| frontend-dev | 14 | 11 | 0.79 |
| graph-db | 7 | 3 | 0.43 |
| graphrag | 7 | 4 | 0.57 |
| hitl | 6 | 5 | 0.83 |
| langchain-langgraph | 9 | 7 | 0.78 |
| llm-api | 12 | 10 | 0.83 |
| mcp | 17 | 15 | 0.88 |
| multi-agent | 8 | 7 | 0.88 |
| multimodal-rag | 8 | 6 | 0.75 |
| multimodality | 9 | 7 | 0.78 |
| observability | 14 | 13 | 0.93 |
| postgresql | 9 | 4 | 0.44 |
| prompt-management | 7 | 4 | 0.57 |
| rag-advanced | 9 | 8 | 0.89 |
| rag-basic | 24 | 18 | 0.75 |
| react-agent | 7 | 4 | 0.57 |
| security-guardrails | 12 | 10 | 0.83 |
| tool-calling | 11 | 6 | 0.55 |
| vector-db | 11 | 7 | 0.64 |

## Решения
| theme_id | action | комментарий |
|----------|--------|-------------|
| a2a-a2ui | merge | Подтверждено auto-extraction (entity resolution) |
| agent-memory | merge | Подтверждено auto-extraction (entity resolution) |
| ai-driven-methodology | merge | Подтверждено auto-extraction (entity resolution) |
| cicd | merge | Подтверждено auto-extraction (entity resolution) |
| context-engineering | merge | Подтверждено auto-extraction (entity resolution) |
| dataset-management | merge | Подтверждено auto-extraction (entity resolution) |
| deep-agents-skills | merge | Подтверждено auto-extraction (entity resolution) |
| docker-devops | merge | Подтверждено auto-extraction (entity resolution) |
| evaluation | merge | Подтверждено auto-extraction (entity resolution) |
| fastapi-backend | merge | Подтверждено auto-extraction (entity resolution) |
| frontend-dev | merge | Подтверждено auto-extraction (entity resolution) |
| graph-db | keep | Seed-тема без авто-подтверждения — оставить (ручной seed authoritative) |
| graphrag | merge | Подтверждено auto-extraction (entity resolution) |
| hitl | merge | Подтверждено auto-extraction (entity resolution) |
| langchain-langgraph | merge | Подтверждено auto-extraction (entity resolution) |
| llm-api | merge | Подтверждено auto-extraction (entity resolution) |
| mcp | merge | Подтверждено auto-extraction (entity resolution) |
| multi-agent | merge | Подтверждено auto-extraction (entity resolution) |
| multimodal-rag | merge | Подтверждено auto-extraction (entity resolution) |
| multimodality | merge | Подтверждено auto-extraction (entity resolution) |
| observability | merge | Подтверждено auto-extraction (entity resolution) |
| postgresql | merge | Подтверждено auto-extraction (entity resolution) |
| prompt-management | merge | Подтверждено auto-extraction (entity resolution) |
| rag-advanced | merge | Подтверждено auto-extraction (entity resolution) |
| rag-basic | merge | Подтверждено auto-extraction (entity resolution) |
| react-agent | merge | Подтверждено auto-extraction (entity resolution) |
| security-guardrails | merge | Подтверждено auto-extraction (entity resolution) |
| tool-calling | merge | Подтверждено auto-extraction (entity resolution) |
| vector-db | merge | Подтверждено auto-extraction (entity resolution) |
