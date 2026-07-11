"""VL embedding clients for method C (unified image embed)."""

from indexers.vl_embed.base import VLEmbedResult
from indexers.vl_embed.factory import (
    make_vl_embed_client,
    preflight_model,
    run_embed_batch,
    smoke_embed,
)
from indexers.vl_embed.openrouter import OpenRouterVLEmbedClient

__all__ = [
    "OpenRouterVLEmbedClient",
    "VLEmbedResult",
    "make_vl_embed_client",
    "preflight_model",
    "run_embed_batch",
    "smoke_embed",
]
