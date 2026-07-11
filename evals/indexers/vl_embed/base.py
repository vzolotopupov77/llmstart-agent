"""VL embed result types."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VLEmbedResult:
    """Single embedding response from VL embed API."""

    vector: list[float]
    prompt_tokens: int
    latency_s: float
    est_cost_usd: float
