"""Shared retrieval and embedding for multimodal RAG eval."""

from __future__ import annotations

import uuid
from dataclasses import asdict
from typing import Protocol

from qdrant_client import QdrantClient

from indexers.config import MultimodalEvalConfig
from scripts.multimodal_metrics import aggregate_by_segment, score_item
from scripts.multimodal_models import MultimodalDataset


class QueryEmbedder(Protocol):
    """Embed text queries for Qdrant search."""

    def embed_queries(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per query text."""
        ...


E5_QUERY_PREFIX = "query: "
E5_PASSAGE_PREFIX = "passage: "


def stable_point_id(method: str, slide_id: int) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"multimodal-{method}:slide-{slide_id:02d}"))


def strip_corpus_header(body: str) -> str:
    content_lines = [line for line in body.splitlines() if not line.startswith("#")]
    return "\n".join(content_lines).strip()


class E5Embedder:
    """Multilingual E5 via sentence-transformers (CPU)."""

    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer  # noqa: PLC0415

        self._model = SentenceTransformer(model_name)

    def embed_queries(self, texts: list[str]) -> list[list[float]]:
        prefixed = [E5_QUERY_PREFIX + text for text in texts]
        vectors = self._model.encode(prefixed, normalize_embeddings=True)
        return [vector.tolist() for vector in vectors]

    def embed_passages(self, texts: list[str]) -> list[list[float]]:
        prefixed = [E5_PASSAGE_PREFIX + (text or " ") for text in texts]
        vectors = self._model.encode(prefixed, normalize_embeddings=True)
        return [vector.tolist() for vector in vectors]


class VLEmbedder:
    """OpenRouter VL embeddings for query side (method C retrieval)."""

    def __init__(self, model_id: str) -> None:
        from indexers.vl_embed.factory import make_vl_embed_client  # noqa: PLC0415

        self._client = make_vl_embed_client(model_id)
        self.model_id = model_id

    def embed_queries(self, texts: list[str]) -> list[list[float]]:
        return [self._client.embed_query(text).vector for text in texts]


class JinaMultivectorEmbedder:
    """Jina v4 multivector embeddings for query side (method D retrieval)."""

    def __init__(self, model_id: str, *, token_dim: int = 128) -> None:
        from indexers.jina_multivector.factory import make_jina_client  # noqa: PLC0415

        self._client = make_jina_client(model_id, token_dim=token_dim)
        self.model_id = model_id
        self.token_dim = token_dim

    def embed_queries(self, texts: list[str]) -> list[list[list[float]]]:
        return [self._client.embed_query(text).vectors for text in texts]


def search_slides(
    cfg: MultimodalEvalConfig,
    query: str,
    *,
    embedder: QueryEmbedder | JinaMultivectorEmbedder,
    client: QdrantClient,
) -> list[int]:
    if cfg.is_multivector:
        if not isinstance(embedder, JinaMultivectorEmbedder):
            msg = "Multivector retrieval requires JinaMultivectorEmbedder"
            raise TypeError(msg)
        vector = embedder.embed_queries([query])[0]
    else:
        vector = embedder.embed_queries([query])[0]
    response = client.query_points(
        collection_name=cfg.collection,
        query=vector,
        limit=cfg.top_k,
    )
    ranked: list[int] = []
    for point in response.points:
        payload = point.payload or {}
        slide_id = payload.get("slide_id")
        if isinstance(slide_id, int):
            ranked.append(slide_id)
    return ranked


def run_retrieval_eval(
    cfg: MultimodalEvalConfig,
    dataset: MultimodalDataset,
    *,
    embedder: QueryEmbedder | JinaMultivectorEmbedder,
    client: QdrantClient,
) -> tuple[list[dict[str, object]], dict[str, dict[str, float]]]:
    rows: list[dict[str, object]] = []
    score_rows: list[tuple[str, object]] = []

    for item in dataset.items:
        ranked = search_slides(cfg, item.question, embedder=embedder, client=client)
        scores = score_item(item, ranked, k=cfg.top_k)
        row = {
            "id": item.id,
            "segment": item.segment,
            "required_slides": item.required_slides or None,
            "trap_slides": item.trap_slides or None,
            "ranked_slides": ranked,
            **asdict(scores),
        }
        rows.append(row)
        score_rows.append((item.segment, scores))

    aggregates = aggregate_by_segment(score_rows)
    return rows, aggregates
