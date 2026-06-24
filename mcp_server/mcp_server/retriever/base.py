"""Abstract retriever interface for knowledge base search."""

from typing import Literal, Protocol, TypedDict

Segment = Literal["b2b", "b2c"]


class KnowledgeChunk(TypedDict):
    """Single retrieved chunk."""

    text: str
    source: str
    segment: str


class IndexNotReadyError(Exception):
    """Raised when vector index is missing or empty."""


class BaseRetriever(Protocol):
    """Semantic search over indexed knowledge chunks."""

    def search(self, query: str, segment: Segment, *, top_k: int) -> list[KnowledgeChunk]:
        """Return top-k chunks for query filtered by segment."""
        ...
