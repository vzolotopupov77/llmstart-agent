"""Qdrant retriever implementation."""

from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue

from mcp_server.config import get_settings
from mcp_server.rag.embeddings import EmbeddingClient, get_embedding_client
from mcp_server.retriever.base import IndexNotReadyError, KnowledgeChunk, Segment

_INDEX_EMPTY_MSG = "knowledge base index is empty; run make index first"


class QdrantRetriever:
    """Retrieve knowledge chunks from Qdrant collection."""

    def __init__(
        self,
        *,
        embedding_client: EmbeddingClient | None = None,
        client: QdrantClient | None = None,
    ) -> None:
        """Initialise retriever; prefer_grpc avoids asyncio.run() overhead on Windows."""
        settings = get_settings()
        self._collection = settings.qdrant_collection
        self._embedding_client = embedding_client or get_embedding_client()
        self._client = client or QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
            prefer_grpc=True,
        )
        self._ready = False

    def _ensure_ready(self) -> None:
        """Verify collection exists and is non-empty once per retriever instance."""
        if self._ready:
            return
        if not self._client.collection_exists(self._collection):
            raise IndexNotReadyError(_INDEX_EMPTY_MSG)

        collection_info = self._client.get_collection(self._collection)
        if collection_info.points_count == 0:
            raise IndexNotReadyError(_INDEX_EMPTY_MSG)

        self._ready = True

    def search(self, query: str, segment: Segment, *, top_k: int) -> list[KnowledgeChunk]:
        """Return top-k chunks from Qdrant filtered by segment."""
        if segment not in ("b2b", "b2c"):
            msg = f"invalid segment: {segment}"
            raise ValueError(msg)

        self._ensure_ready()
        query_embedding = self._embedding_client.embed_texts([query])[0]
        response = self._client.query_points(
            collection_name=self._collection,
            query=query_embedding,
            query_filter=Filter(
                must=[FieldCondition(key="segment", match=MatchValue(value=segment))],
            ),
            limit=top_k,
        )

        chunks: list[KnowledgeChunk] = []
        for point in response.points:
            payload = point.payload or {}
            text = payload.get("text")
            if not text:
                continue
            chunks.append(
                {
                    "text": str(text),
                    "source": str(payload.get("source", "")),
                    "segment": str(payload.get("segment", segment)),
                    "branch": "vector",
                },
            )
        return chunks
