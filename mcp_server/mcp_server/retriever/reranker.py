"""Multilingual cross-encoder reranking for hybrid retrieval."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Protocol, cast

from mcp_server.config import get_settings
from mcp_server.retriever.base import KnowledgeChunk, copy_chunk

logger = logging.getLogger(__name__)


class _CrossEncoderLike(Protocol):
    def predict(self, pairs: list[tuple[str, str]]) -> object: ...


@lru_cache
def _get_cross_encoder(model_name: str) -> _CrossEncoderLike:
    from sentence_transformers import CrossEncoder  # noqa: PLC0415

    return cast("_CrossEncoderLike", CrossEncoder(model_name))


def rerank_chunks(
    query: str,
    chunks: list[KnowledgeChunk],
    *,
    top_k: int,
) -> list[KnowledgeChunk]:
    """Rerank chunks with CrossEncoder; fall back to score order if disabled."""
    if not chunks:
        return []
    if len(chunks) <= top_k:
        return chunks[:top_k]

    settings = get_settings()
    if not settings.reranker_enabled:
        return chunks[:top_k]

    try:
        model = _get_cross_encoder(settings.reranker_model)
    except ImportError:
        logger.warning("sentence-transformers not installed; skipping rerank")
        return chunks[:top_k]

    pairs = [(query, chunk.get("text", "")) for chunk in chunks]
    scores = cast("list[float]", model.predict(pairs))
    ranked = sorted(
        zip(chunks, scores, strict=True),
        key=lambda item: float(item[1]),
        reverse=True,
    )
    result: list[KnowledgeChunk] = []
    for chunk, score in ranked[:top_k]:
        updated = copy_chunk(chunk)
        updated["rank"] = float(score)
        result.append(updated)
    return result
