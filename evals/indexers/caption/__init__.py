"""VLM caption ingestion for method B."""

from indexers.caption.base import CAPTION_PROMPT, CaptionResult
from indexers.caption.factory import make_caption_client, preflight_models, run_caption_batch
from indexers.caption.pricing import model_slug

__all__ = [
    "CAPTION_PROMPT",
    "CaptionResult",
    "make_caption_client",
    "model_slug",
    "preflight_models",
    "run_caption_batch",
]
