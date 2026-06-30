"""Branch-specific knowledge retrieval tool handlers."""

from typing import Literal

from mcp_server.config import get_settings
from mcp_server.retriever.base import (
    BaseRetriever,
    GraphNotReadyError,
    IndexNotReadyError,
    KnowledgeChunk,
)
from mcp_server.retriever.factory import get_retriever

Segment = Literal["b2b", "b2c"]
RetrieverBranch = Literal["vector", "graph", "global"]

VECTOR_SEARCH_TOOL_DESCRIPTION = """
Semantic search in the B2B/B2C knowledge base (Qdrant):
program descriptions, FAQ, policies, one course/topic.

Use for single-hop factual questions about a specific course, module,
format details, or semantic content.

NOT for prerequisite chains, catalog aggregates, counts, or structural graph queries —
use graph_search, global_catalog, or text2cypher_tool instead.

Examples:
- YES: "Расскажи про курс deep-agents"
- YES: "Есть ли рассрочка на комбо?"
- NO: "Что нужно пройти перед deep-agents?" → graph_search
- NO: "Сколько курсов в каталоге?" → global_catalog or text2cypher_tool
""".strip()

GRAPH_SEARCH_TOOL_DESCRIPTION = """
Graph traversal retrieval: prerequisite chains, course dependencies,
theme intersections, combo composition.

Use when the answer requires following 2+ nodes in the catalog graph
(RECOMMENDED_BEFORE, COVERS, INCLUDES).

NOT for simple descriptions of one course, catalog-wide aggregates, or exact counts —
use vector_search, global_catalog, or text2cypher_tool instead.

Examples:
- YES: "Что нужно пройти перед курсом deep-agents?"
- YES: "Что общего в темах курсов fullstack-aidd и agents?"
- NO: "Расскажи про agents" → vector_search
""".strip()

GLOBAL_CATALOG_TOOL_DESCRIPTION = """
Catalog-wide structural overview via Neo4j aggregates:
all formats, audiences, combo hours, theme→courses, course lists.

Use only for explicit catalog-wide questions across multiple courses or the whole catalog
(aggregates, filters by audience, theme coverage).

NOT for one course, schedule/start time, seminar days, recordings, price/policy details,
or follow-up questions about a concrete product — use vector_search instead.
NOT for ad-hoc Cypher — use text2cypher_tool instead.

Examples:
- YES: "Какие форматы обучения предлагает LLMStart?"
- YES: "в каких курсах встречается тема MCP?"
- YES: "Суммарная учебная нагрузка по курсам комбо"
- NO: "Расскажи подробно про модуль 3 курса agents" → vector_search
""".strip()


def handle_branch_search(
    query: str,
    segment: Segment,
    branch: RetrieverBranch,
    *,
    retriever: BaseRetriever | None = None,
) -> list[KnowledgeChunk]:
    """Search knowledge base using an explicit retriever branch."""
    if segment not in ("b2b", "b2c"):
        msg = f"segment must be 'b2b' or 'b2c', got: {segment}"
        raise ValueError(msg)
    if not query.strip():
        msg = "query must not be empty"
        raise ValueError(msg)
    try:
        active = retriever or get_retriever(branch=branch)
        return active.search(
            query=query.strip(),
            segment=segment,
            top_k=get_settings().rag_top_k,
        )
    except IndexNotReadyError as exc:
        msg = str(exc)
        raise ValueError(msg) from exc
    except GraphNotReadyError as exc:
        msg = str(exc)
        raise ValueError(msg) from exc


def handle_search_knowledge_base(
    query: str,
    segment: Segment,
    *,
    retriever: BaseRetriever | None = None,
) -> list[KnowledgeChunk]:
    """Backward-compatible vector-only search (tests, internal callers)."""
    return handle_branch_search(query, segment, "vector", retriever=retriever)
