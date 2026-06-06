"""search_knowledge_base tool handler."""

from typing import Literal

from mcp_server.rag.retriever import IndexNotReadyError, KnowledgeChunk
from mcp_server.rag.retriever import search_knowledge_base as retrieve

Segment = Literal["b2b", "b2c"]


def handle_search_knowledge_base(query: str, segment: Segment) -> list[KnowledgeChunk]:
    """Search knowledge base for a segment."""
    if segment not in ("b2b", "b2c"):
        msg = f"segment must be 'b2b' or 'b2c', got: {segment}"
        raise ValueError(msg)
    if not query.strip():
        msg = "query must not be empty"
        raise ValueError(msg)
    try:
        return retrieve(query=query.strip(), segment=segment)
    except IndexNotReadyError as exc:
        msg = str(exc)
        raise ValueError(msg) from exc
