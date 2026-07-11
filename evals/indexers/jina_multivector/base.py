"""Jina multivector embed result types."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class JinaMultivectorResult:
    """Multivector embedding response from Jina API (N x token_dim)."""

    vectors: list[list[float]]
    total_tokens: int
    latency_s: float
    est_cost_usd: float

    @property
    def num_vectors(self) -> int:
        return len(self.vectors)
