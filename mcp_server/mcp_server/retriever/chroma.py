"""ChromaDB retriever implementation."""

from mcp_server.rag.embeddings import EmbeddingClient
from mcp_server.rag.retriever import search_knowledge_base
from mcp_server.retriever.base import KnowledgeChunk, Segment


class ChromaRetriever:
    """Retrieve knowledge chunks from embedded Chroma index."""

    def __init__(self, *, embedding_client: EmbeddingClient | None = None) -> None:
        """Initialise retriever with optional embedding client."""
        self._embedding_client = embedding_client

    def search(self, query: str, segment: Segment, *, top_k: int) -> list[KnowledgeChunk]:
        """Return top-k chunks from Chroma filtered by segment."""
        return search_knowledge_base(
            query,
            segment,
            top_k=top_k,
            embedding_client=self._embedding_client,
        )
