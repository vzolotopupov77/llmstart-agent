"""Hybrid retrieval: vector + graph with RRF merge and reranking."""

from __future__ import annotations

from mcp_server.config import get_settings
from mcp_server.retriever.base import BaseRetriever, KnowledgeChunk, Segment, copy_chunk
from mcp_server.retriever.fusion import merge_rrf
from mcp_server.retriever.reranker import rerank_chunks


class HybridRetriever:
    """Combine vector and graph branches via RRF and cross-encoder rerank."""

    def __init__(
        self,
        *,
        vector: BaseRetriever,
        graph: BaseRetriever,
    ) -> None:
        self._vector = vector
        self._graph = graph

    def search(self, query: str, segment: Segment, *, top_k: int) -> list[KnowledgeChunk]:
        candidate_k = max(top_k * 2, top_k)
        settings = get_settings()

        vector_hits = self._tag_branch(
            self._vector.search(query, segment, top_k=candidate_k),
            branch="vector",
        )
        graph_hits = self._graph.search(query, segment, top_k=candidate_k)
        merged = merge_rrf(vector_hits, graph_hits, k=settings.rrf_k)
        reranked = rerank_chunks(query, merged, top_k=top_k)
        return self._tag_branch(reranked, branch="hybrid")

    @staticmethod
    def _tag_branch(chunks: list[KnowledgeChunk], *, branch: str) -> list[KnowledgeChunk]:
        tagged: list[KnowledgeChunk] = []
        for chunk in chunks:
            updated = copy_chunk(chunk)
            updated["branch"] = branch
            tagged.append(updated)
        return tagged
