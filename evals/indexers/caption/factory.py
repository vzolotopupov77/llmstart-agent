"""Caption client factory, preflight, and batch runner."""

from __future__ import annotations

import logging
from pathlib import Path

from indexers.caption.base import CaptionResult
from indexers.caption.openrouter import OpenRouterCaptionClient, require_openrouter_key
from indexers.caption.pricing import fetch_model_pricing, list_model_ids, model_slug

logger = logging.getLogger(__name__)

FREE_TIER_FALLBACK_MODEL = "qwen/qwen3-vl-8b-instruct"


def make_caption_client(model_id: str) -> OpenRouterCaptionClient:
    require_openrouter_key()
    pricing = fetch_model_pricing(model_id)
    return OpenRouterCaptionClient(model_id, pricing=pricing)


def preflight_models(model_ids: list[str]) -> dict[str, str]:
    """Verify models exist in OpenRouter catalog. Returns id -> status."""
    catalog = list_model_ids()
    return {model_id: "FOUND" if model_id in catalog else "MISSING" for model_id in model_ids}


def smoke_caption(model_id: str, image_path: Path) -> CaptionResult:
    """Single-image smoke test before full batch."""
    client = make_caption_client(model_id)
    return client.caption_image(image_path)


def _artifact_header(
    *,
    slide_id: int,
    png_name: str,
    model_id: str,
    result: CaptionResult,
    fallback_from: str | None = None,
    fallback_reason: str | None = None,
) -> str:
    lines = [
        f"# slide-{slide_id:02d}",
        f"# source: VLM caption ({png_name})",
        f"# model: {model_id}",
    ]
    if fallback_from:
        lines.append(f"# fallback_from: {fallback_from}")
    if fallback_reason:
        lines.append(f"# fallback_reason: {fallback_reason}")
    lines.extend(
        [
            f"# prompt_tokens: {result.prompt_tokens}",
            f"# completion_tokens: {result.completion_tokens}",
            f"# latency_s: {result.latency_s:.2f}",
            f"# est_cost_usd: {result.est_cost_usd:.8f}",
        ],
    )
    return "\n".join(lines) + "\n"


def write_caption_artifact(
    artifact_dir: Path,
    *,
    slide_id: int,
    png_name: str,
    model_id: str,
    result: CaptionResult,
    fallback_from: str | None = None,
    fallback_reason: str | None = None,
) -> None:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    out_path = artifact_dir / f"slide-{slide_id:02d}.txt"
    header = _artifact_header(
        slide_id=slide_id,
        png_name=png_name,
        model_id=model_id,
        result=result,
        fallback_from=fallback_from,
        fallback_reason=fallback_reason,
    )
    out_path.write_text(header + result.text, encoding="utf-8")


def _read_artifact_cost(path: Path) -> float:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# est_cost_usd:"):
            raw = line.split(":", 1)[1].strip()
            try:
                return float(raw)
            except ValueError:
                return 0.0
    return 0.0


def run_caption_batch(
    model_id: str,
    corpus_dir: Path,
    artifact_dir: Path,
    *,
    slide_ids: list[int] | None = None,
) -> tuple[float, float, int]:
    """Caption all PNG slides; return (caption_time_s, total_cost_usd, api_calls)."""
    client = make_caption_client(model_id)
    active_model_id = model_id
    fallback_from: str | None = None
    fallback_reason: str | None = None
    png_files = sorted(corpus_dir.glob("slide-*.png"))
    if slide_ids is not None:
        allowed = {f"slide-{sid:02d}.png" for sid in slide_ids}
        png_files = [p for p in png_files if p.name in allowed]

    if not png_files:
        msg = f"No PNG slides found in {corpus_dir}"
        raise ValueError(msg)

    import time

    start = time.perf_counter()
    total_cost = 0.0
    api_calls = 0

    for index, png_path in enumerate(png_files, start=1):
        slide_id = int(png_path.stem.split("-")[1])
        out_path = artifact_dir / f"slide-{slide_id:02d}.txt"
        if out_path.exists() and out_path.stat().st_size > 0:
            logger.info(
                "Skip %s (%d/%d) — artifact exists",
                png_path.name,
                index,
                len(png_files),
            )
            api_calls += 1
            total_cost += _read_artifact_cost(out_path)
            continue

        logger.info(
            "Caption %s (%d/%d) model=%s",
            png_path.name,
            index,
            len(png_files),
            model_slug(active_model_id),
        )
        try:
            result = client.caption_image(png_path)
        except RuntimeError as exc:
            if (
                ":free" in model_id
                and "429" in str(exc)
                and active_model_id == model_id
            ):
                logger.warning(
                    "Rate limit on %s — switching to fallback %s for remaining slides",
                    model_id,
                    FREE_TIER_FALLBACK_MODEL,
                )
                active_model_id = FREE_TIER_FALLBACK_MODEL
                fallback_from = model_id
                fallback_reason = "rate_limit_429_free_tier"
                client = make_caption_client(active_model_id)
                result = client.caption_image(png_path)
            else:
                raise
        write_caption_artifact(
            artifact_dir,
            slide_id=slide_id,
            png_name=png_path.name,
            model_id=active_model_id,
            result=result,
            fallback_from=fallback_from,
            fallback_reason=fallback_reason,
        )
        total_cost += result.est_cost_usd
        api_calls += 1

    caption_time_s = time.perf_counter() - start
    return caption_time_s, total_cost, api_calls
