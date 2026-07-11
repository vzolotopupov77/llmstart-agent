"""OpenRouter model pricing and slug helpers."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass

DEFAULT_MODELS_URL = "https://openrouter.ai/api/v1/models"


@dataclass(frozen=True)
class ModelPricing:
    """Per-token pricing from OpenRouter catalog."""

    model_id: str
    prompt_per_token: float
    completion_per_token: float


def model_slug(model_id: str) -> str:
    """nvidia/nemotron-nano-12b-v2-vl:free -> nemotron-nano-12b-v2-vl."""
    base = model_id.split("/")[-1] if "/" in model_id else model_id
    return base.split(":")[0]


def estimate_cost_usd(
    pricing: ModelPricing,
    *,
    prompt_tokens: int,
    completion_tokens: int,
) -> float:
    return (
        prompt_tokens * pricing.prompt_per_token + completion_tokens * pricing.completion_per_token
    )


def _parse_price(raw: object) -> float:
    if raw is None:
        return 0.0
    try:
        return float(raw)
    except (TypeError, ValueError):
        return 0.0


def fetch_model_pricing(
    model_id: str,
    *,
    models_url: str = DEFAULT_MODELS_URL,
    timeout_s: float = 20.0,
) -> ModelPricing:
    request = urllib.request.Request(
        models_url,
        headers={"Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            payload = json.loads(response.read())
    except urllib.error.URLError as exc:
        msg = f"Failed to fetch OpenRouter models: {exc}"
        raise RuntimeError(msg) from exc

    for entry in payload.get("data", []):
        if entry.get("id") == model_id:
            pricing = entry.get("pricing", {})
            return ModelPricing(
                model_id=model_id,
                prompt_per_token=_parse_price(pricing.get("prompt")),
                completion_per_token=_parse_price(pricing.get("completion")),
            )

    msg = f"Model {model_id!r} not found in OpenRouter catalog"
    raise ValueError(msg)


def list_model_ids(
    *,
    models_url: str = DEFAULT_MODELS_URL,
    timeout_s: float = 20.0,
) -> set[str]:
    request = urllib.request.Request(
        models_url,
        headers={"Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout_s) as response:
        payload = json.loads(response.read())
    return {entry["id"] for entry in payload.get("data", []) if entry.get("id")}
