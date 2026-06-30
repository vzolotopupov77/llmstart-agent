"""Abstract retriever interface for knowledge base search."""

from typing import Literal, Protocol, TypedDict, cast

Segment = Literal["b2b", "b2c"]


class KnowledgeChunk(TypedDict, total=False):
    """Single retrieved chunk."""

    text: str
    source: str
    segment: str
    branch: str
    entity_id: str
    rank: float


class IndexNotReadyError(Exception):
    """Raised when vector index is missing or empty."""


class GraphNotReadyError(Exception):
    """Raised when Neo4j is unreachable or empty."""


class BaseRetriever(Protocol):
    """Semantic search over indexed knowledge chunks."""

    def search(self, query: str, segment: Segment, *, top_k: int) -> list[KnowledgeChunk]:
        """Return top-k chunks for query filtered by segment."""
        ...


def copy_chunk(chunk: KnowledgeChunk) -> KnowledgeChunk:
    """Return a shallow copy of a knowledge chunk."""
    return cast("KnowledgeChunk", dict(chunk))
