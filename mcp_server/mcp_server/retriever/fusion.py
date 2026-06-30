"""Reciprocal Rank Fusion for hybrid retrieval."""

from __future__ import annotations

from mcp_server.retriever.base import KnowledgeChunk, copy_chunk


def _chunk_key(chunk: KnowledgeChunk) -> str:
    entity_id = chunk.get("entity_id")
    if entity_id:
        return f"entity:{entity_id}"
    text = chunk.get("text", "")
    return f"text:{text[:200]}"


def rrf_score(rank: int, *, k: int) -> float:
    """Compute RRF contribution for a 1-based rank."""
    return 1.0 / (k + rank)


def merge_rrf(
    *ranked_lists: list[KnowledgeChunk],
    k: int,
) -> list[KnowledgeChunk]:
    """Merge ranked chunk lists using Reciprocal Rank Fusion."""
    scores: dict[str, float] = {}
    chunks_by_key: dict[str, KnowledgeChunk] = {}

    for ranked in ranked_lists:
        for index, chunk in enumerate(ranked, start=1):
            key = _chunk_key(chunk)
            scores[key] = scores.get(key, 0.0) + rrf_score(index, k=k)
            if key not in chunks_by_key:
                chunks_by_key[key] = copy_chunk(chunk)

    merged: list[KnowledgeChunk] = []
    for key, score in sorted(scores.items(), key=lambda item: item[1], reverse=True):
        item = copy_chunk(chunks_by_key[key])
        item["rank"] = score
        merged.append(item)
    return merged
