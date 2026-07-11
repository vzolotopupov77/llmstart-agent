"""Tests for caption pricing and slug helpers."""

from __future__ import annotations

from indexers.caption.pricing import (
    ModelPricing,
    estimate_cost_usd,
    model_slug,
)


def test_model_slug_strips_vendor_and_free_suffix() -> None:
    assert model_slug("nvidia/nemotron-nano-12b-v2-vl:free") == "nemotron-nano-12b-v2-vl"
    assert model_slug("google/gemini-2.5-flash-lite") == "gemini-2.5-flash-lite"


def test_estimate_cost_usd() -> None:
    pricing = ModelPricing(
        model_id="google/gemini-2.5-flash-lite",
        prompt_per_token=0.0000001,
        completion_per_token=0.0000004,
    )
    cost = estimate_cost_usd(pricing, prompt_tokens=1000, completion_tokens=500)
    assert abs(cost - (1000 * 0.0000001 + 500 * 0.0000004)) < 1e-12


def test_estimate_cost_usd_free_model() -> None:
    pricing = ModelPricing(
        model_id="nvidia/nemotron-nano-12b-v2-vl:free",
        prompt_per_token=0.0,
        completion_per_token=0.0,
    )
    assert estimate_cost_usd(pricing, prompt_tokens=5000, completion_tokens=2000) == 0.0
