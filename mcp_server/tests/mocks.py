"""Shared test doubles for mcp_server."""

from mcp_server.retriever.base import KnowledgeChunk, Segment


class MockRetriever:
    """In-memory retriever for tool-level tests."""

    def search(self, query: str, segment: Segment, *, top_k: int) -> list[KnowledgeChunk]:
        """Return a deterministic chunk for the query."""
        chunk: KnowledgeChunk = {
            "text": f"Cursor интенсив details for {query}",
            "source": "mock.md",
            "segment": segment,
        }
        return [chunk][:top_k]
