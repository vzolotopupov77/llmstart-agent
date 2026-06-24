"""search_knowledge_base tool handler."""

from typing import Literal

from mcp_server.config import get_settings
from mcp_server.retriever.base import BaseRetriever, IndexNotReadyError, KnowledgeChunk
from mcp_server.retriever.factory import get_retriever

Segment = Literal["b2b", "b2c"]


def handle_search_knowledge_base(
    query: str,
    segment: Segment,
    *,
    retriever: BaseRetriever | None = None,
) -> list[KnowledgeChunk]:
    """Search knowledge base for a segment."""
    if segment not in ("b2b", "b2c"):
        msg = f"segment must be 'b2b' or 'b2c', got: {segment}"
        raise ValueError(msg)
    if not query.strip():
        msg = "query must not be empty"
        raise ValueError(msg)
    try:
        return (retriever or get_retriever()).search(
            query=query.strip(),
            segment=segment,
            top_k=get_settings().rag_top_k,
        )
    except IndexNotReadyError as exc:
        msg = str(exc)
        raise ValueError(msg) from exc
