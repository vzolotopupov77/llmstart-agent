"""text2cypher_tool MCP handler."""

from __future__ import annotations

from typing import Literal

from neo4j_graphrag.exceptions import Text2CypherRetrievalError

from mcp_server.config import get_settings
from mcp_server.retriever.base import GraphNotReadyError, KnowledgeChunk
from mcp_server.retriever.text2cypher import get_text2cypher_retriever
from mcp_server.text2cypher.guardrails import Text2CypherGuardrailError

Segment = Literal["b2b", "b2c"]

TEXT2CYPHER_TOOL_DESCRIPTION = """
Run a read-only structural query against the course catalog Neo4j graph (counts, lists, filters).

Use for structural/catalog queries: exact counts ("сколько курсов"), membership lists
("какие курсы входят в комбо"), theme coverage, audience filters, combo composition.

NOT for descriptions, FAQ, program details, or semantic search — use vector_search instead.

Examples:
- YES: "Сколько курсов покрывают тему RAG?"
- YES: "Какие курсы входят в комбо ai-agents-combo?"
- NO: "Расскажи подробно про курс agents"
""".strip()


def handle_text2cypher(query: str, segment: Segment) -> list[KnowledgeChunk]:
    """Execute guarded NL→Cypher retrieval for structural catalog questions."""
    if segment not in ("b2b", "b2c"):
        msg = f"segment must be 'b2b' or 'b2c', got: {segment}"
        raise ValueError(msg)
    if not query.strip():
        msg = "query must not be empty"
        raise ValueError(msg)

    try:
        retriever = get_text2cypher_retriever()
        return retriever.search_catalog(
            query=query.strip(),
            segment=segment,
            top_k=get_settings().rag_top_k,
        )
    except Text2CypherGuardrailError as exc:
        raise ValueError(str(exc)) from exc
    except Text2CypherRetrievalError as exc:
        raise ValueError(str(exc)) from exc
    except GraphNotReadyError as exc:
        raise ValueError(str(exc)) from exc
