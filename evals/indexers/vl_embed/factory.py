"""VL embed client factory, preflight, and batch runner."""

from __future__ import annotations

import logging
from pathlib import Path

from indexers.caption.pricing import ModelPricing, fetch_model_pricing, list_model_ids, model_slug
from indexers.openrouter_common import require_openrouter_key
from indexers.vl_embed.base import VLEmbedResult
from indexers.vl_embed.openrouter import OpenRouterVLEmbedClient

logger = logging.getLogger(__name__)

PAID_FALLBACK_MODEL = "nvidia/llama-nemotron-embed-vl-1b-v2"


def make_vl_embed_client(model_id: str) -> OpenRouterVLEmbedClient:
    require_openrouter_key()
    try:
        pricing = fetch_model_pricing(model_id)
    except ValueError:
        logger.warning(
            "Model %s not in OpenRouter pricing catalog — using $0 defaults",
            model_id,
        )
        pricing = ModelPricing(
            model_id=model_id,
            prompt_per_token=0.0,
            completion_per_token=0.0,
        )
    return OpenRouterVLEmbedClient(model_id, pricing=pricing)


def preflight_model(model_id: str) -> str:
    """Check model in OpenRouter catalog (embed models may be absent)."""
    catalog = list_model_ids()
    if model_id in catalog:
        return "FOUND"
    return "NOT_IN_CATALOG"


def smoke_embed(model_id: str, image_path: Path) -> VLEmbedResult:
    """Smoke test: embed one image and return result with vector dim."""
    client = make_vl_embed_client(model_id)
    return client.embed_image(image_path)


def run_embed_batch(
    model_id: str,
    corpus_dir: Path,
    *,
    slide_ids: list[int] | None = None,
) -> tuple[list[tuple[int, list[float]]], float, float, int]:
    """Embed all PNG slides; return (slide_vectors, embed_time_s, total_cost, api_calls)."""
    client = make_vl_embed_client(model_id)
    active_model_id = model_id
    fallback_from: str | None = None

    png_files = sorted(corpus_dir.glob("slide-*.png"))
    if slide_ids is not None:
        allowed = {f"slide-{sid:02d}.png" for sid in slide_ids}
        png_files = [path for path in png_files if path.name in allowed]

    if not png_files:
        msg = f"No PNG slides found in {corpus_dir}"
        raise ValueError(msg)

    import time

    start = time.perf_counter()
    total_cost = 0.0
    api_calls = 0
    slide_vectors: list[tuple[int, list[float]]] = []

    for index, png_path in enumerate(png_files, start=1):
        slide_id = int(png_path.stem.split("-")[1])
        logger.info(
            "VL embed %s (%d/%d) model=%s",
            png_path.name,
            index,
            len(png_files),
            model_slug(active_model_id),
        )
        try:
            result = client.embed_image(png_path)
        except RuntimeError as exc:
            if ":free" in model_id and "429" in str(exc) and active_model_id == model_id:
                logger.warning(
                    "Rate limit on %s — switching to fallback %s for remaining slides",
                    model_id,
                    PAID_FALLBACK_MODEL,
                )
                active_model_id = PAID_FALLBACK_MODEL
                fallback_from = model_id
                client = make_vl_embed_client(active_model_id)
                result = client.embed_image(png_path)
            else:
                raise
        if fallback_from and index == 1:
            logger.info("Fallback active from slide %s (was %s)", png_path.name, fallback_from)
        slide_vectors.append((slide_id, result.vector))
        total_cost += result.est_cost_usd
        api_calls += 1

    embed_time_s = time.perf_counter() - start
    return slide_vectors, embed_time_s, total_cost, api_calls
