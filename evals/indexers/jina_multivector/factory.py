"""Jina multivector client factory and batch runner."""

from __future__ import annotations

import logging
import time
from pathlib import Path

from indexers.jina_multivector.base import JinaMultivectorResult
from indexers.jina_multivector.client import JinaMultivectorClient

logger = logging.getLogger(__name__)


def make_jina_client(
    model_id: str,
    *,
    token_dim: int = 128,
) -> JinaMultivectorClient:
    return JinaMultivectorClient(model_id, token_dim=token_dim)


def smoke_embed_image(
    model_id: str,
    image_path: Path,
    *,
    max_side: int,
    token_dim: int = 128,
) -> JinaMultivectorResult:
    """Smoke test: embed one image and return multivector matrix."""
    client = make_jina_client(model_id, token_dim=token_dim)
    return client.embed_image(image_path, max_side=max_side)


def run_embed_batch(
    model_id: str,
    corpus_dir: Path,
    *,
    max_side: int,
    token_dim: int = 128,
    slide_ids: list[int] | None = None,
) -> tuple[list[tuple[int, list[list[float]]]], float, float, int]:
    """Embed all PNG slides; return (slide_vectors, embed_time_s, total_cost, api_calls)."""
    client = make_jina_client(model_id, token_dim=token_dim)

    png_files = sorted(corpus_dir.glob("slide-*.png"))
    if slide_ids is not None:
        allowed = {f"slide-{sid:02d}.png" for sid in slide_ids}
        png_files = [path for path in png_files if path.name in allowed]

    if not png_files:
        msg = f"No PNG slides found in {corpus_dir}"
        raise ValueError(msg)

    start = time.perf_counter()
    total_cost = 0.0
    api_calls = 0
    slide_vectors: list[tuple[int, list[list[float]]]] = []

    for index, png_path in enumerate(png_files, start=1):
        slide_id = int(png_path.stem.split("-")[1])
        logger.info(
            "Jina multivector %s (%d/%d) model=%s max_side=%d",
            png_path.name,
            index,
            len(png_files),
            model_id,
            max_side,
        )
        result = client.embed_image(png_path, max_side=max_side)
        slide_vectors.append((slide_id, result.vectors))
        total_cost += result.est_cost_usd
        api_calls += 1

    embed_time_s = time.perf_counter() - start
    return slide_vectors, embed_time_s, total_cost, api_calls
