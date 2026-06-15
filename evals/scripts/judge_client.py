"""Judge LLM factory for eval metrics (E-17)."""

from __future__ import annotations

import os

from app.agent.run_config import JudgeConfigBlock
from deepeval.models.llms.openrouter_model import OpenRouterModel

from scripts.langfuse_helpers import load_env_file


def create_judge_model(judge: JudgeConfigBlock) -> OpenRouterModel:
    """Build DeepEval judge model via OpenRouter (project uses OPENAI_* env)."""
    load_env_file()
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        msg = "Missing OPENAI_API_KEY for judge (set in .env)"
        raise RuntimeError(msg)
    base_url = os.environ.get("OPENAI_BASE_URL", "https://openrouter.ai/api/v1").strip()
    return OpenRouterModel(
        model=judge.name,
        api_key=api_key,
        base_url=base_url,
        temperature=judge.temperature,
    )


def require_openrouter_key() -> None:
    load_env_file()
    if not os.environ.get("OPENAI_API_KEY", "").strip():
        msg = "Missing OPENAI_API_KEY (set in .env)"
        raise RuntimeError(msg)
