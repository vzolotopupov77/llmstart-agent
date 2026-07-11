"""Method D indexer: PNG → Jina v4 multivector → Qdrant MAX_SIM."""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    MultiVectorComparator,
    MultiVectorConfig,
    PointStruct,
    VectorParams,
)

from indexers.base import IndexCost, validate_corpus_dir
from indexers.config import MultimodalEvalConfig
from indexers.jina_multivector.factory import run_embed_batch
from scripts.multimodal_retrieval import stable_point_id

logger = logging.getLogger(__name__)


def _compute_index_size_mb(total_tokens: int, token_dim: int) -> float:
    return (total_tokens * token_dim * 4) / (1024 * 1024)


class DMultivectorIndexer:
    """Embed slide PNGs via Jina multivector API and upsert to Qdrant."""

    def __init__(self, cfg: MultimodalEvalConfig) -> None:
        self._cfg = cfg
        self.embed_model = os.environ.get("JINA_EMBED_MODEL", cfg.embedding_model)
        self.d_max_side = cfg.d_max_side or 1024
        self.token_dim = cfg.embedding_dim
        self.corpus_stats: dict[int, int] = {}
        self.indexed_slides: int = 0
        self.embed_time_s: float = 0.0
        self.upsert_time_s: float = 0.0
        self.api_calls: int = 0
        self.total_tokens: int = 0

    def build_index(self, corpus_dir: Path) -> IndexCost:
        validate_corpus_dir(corpus_dir)

        slide_vectors, embed_time_s, est_cost_usd, api_calls = run_embed_batch(
            self.embed_model,
            corpus_dir,
            max_side=self.d_max_side,
            token_dim=self.token_dim,
        )
        self.embed_time_s = embed_time_s
        self.api_calls = api_calls
        logger.info(
            "Jina multivector (%s) finished in %.2fs, cost=$%.6f, calls=%d",
            self.embed_model,
            self.embed_time_s,
            est_cost_usd,
            api_calls,
        )

        upsert_start = time.perf_counter()
        client = QdrantClient(url=self._cfg.qdrant_url)

        if client.collection_exists(self._cfg.collection):
            client.delete_collection(self._cfg.collection)
        client.create_collection(
            collection_name=self._cfg.collection,
            vectors_config=VectorParams(
                size=self.token_dim,
                distance=Distance.COSINE,
                multivector_config=MultiVectorConfig(
                    comparator=MultiVectorComparator.MAX_SIM,
                ),
            ),
        )

        method_tag = "multivector_jina_v4"
        points: list[PointStruct] = []
        total_tokens = 0
        for slide_id, vectors in slide_vectors:
            num_tokens = len(vectors)
            total_tokens += num_tokens
            points.append(
                PointStruct(
                    id=stable_point_id(method_tag, slide_id),
                    vector=vectors,
                    payload={
                        "slide_id": slide_id,
                        "source": f"slide-{slide_id:02d}.png",
                        "method": method_tag,
                        "embed_model": self.embed_model,
                        "num_tokens": num_tokens,
                    },
                ),
            )

        # One point per upsert: multivector JSON payloads exceed Qdrant batch limit (~33MB)
        for index, point in enumerate(points, start=1):
            client.upsert(collection_name=self._cfg.collection, points=[point], wait=True)
            if index % 10 == 0 or index == len(points):
                logger.info("Upserted %d/%d multivector points", index, len(points))
        self.upsert_time_s = time.perf_counter() - upsert_start
        build_time_s = self.embed_time_s + self.upsert_time_s
        self.indexed_slides = len(points)
        self.total_tokens = total_tokens
        self.corpus_stats = {slide_id: len(vectors) for slide_id, vectors in slide_vectors}

        index_size_mb = _compute_index_size_mb(total_tokens, self.token_dim)

        logger.info(
            "Indexed %d slides (%d tokens, upsert %.2fs, total %.2fs, size %.3f MB)",
            self.indexed_slides,
            total_tokens,
            self.upsert_time_s,
            build_time_s,
            index_size_mb,
        )

        return IndexCost(
            collection=self._cfg.collection,
            index_size_mb=index_size_mb,
            build_time_s=build_time_s,
            api_calls=api_calls,
            est_cost_usd=est_cost_usd,
            is_multivector=True,
        )
