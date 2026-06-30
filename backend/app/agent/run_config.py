"""Eval run configuration models (E-5)."""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field


class AgentConfigBlock(BaseModel):
    """Agent implementation reference."""

    impl: str
    api_url: str


class RetrievalConfigBlock(BaseModel):
    """Retrieval backend reference."""

    backend: str
    db_version: str | None = None
    embedding_model: str | None = None
    chunk_size: int | None = None
    top_k: int | None = None
    branch: str | None = None
    rrf_k: int | None = None
    reranker_model: str | None = None


class ModelConfigBlock(BaseModel):
    """LLM parameters for the agent."""

    provider: str
    name: str
    temperature: float = 0.0


class JudgeConfigBlock(BaseModel):
    """LLM-as-judge parameters (separate from agent model, E-17)."""

    provider: str
    name: str
    temperature: float = 0.0


class PromptConfigBlock(BaseModel):
    """Prompt source reference."""

    source: Literal["code", "langfuse"]
    name: str
    label: str | None = None
    version: int | None = None


class RunConfig(BaseModel):
    """Full eval run configuration loaded from evals/configs/<config_id>.yaml."""

    config_id: str
    comment: str = ""
    benchmark_only: bool = False
    agent: AgentConfigBlock
    retrieval: RetrievalConfigBlock
    model: ModelConfigBlock
    judge: JudgeConfigBlock
    prompt: PromptConfigBlock
    datasets: dict[str, str] = Field(default_factory=dict)


def load_run_config(path: Path) -> RunConfig:
    """Load and validate a run config YAML file."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        msg = f"Invalid run config (expected mapping): {path}"
        raise TypeError(msg)
    config = RunConfig.model_validate(raw)
    expected_id = path.stem
    if config.config_id != expected_id:
        msg = f"config_id {config.config_id!r} must match filename {expected_id!r}"
        raise ValueError(msg)
    return config
