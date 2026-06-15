"""Pydantic models for eval dataset manifests (E-12, E-15)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator


class ItemMetadata(BaseModel):
    """Per-item metadata (E-12, E-13, E-14)."""

    segment: Literal["b2c", "b2b"]
    intent: str = Field(description="Taxonomy category, e.g. G1.1")
    source: Literal["real_dialog", "synthetic"]
    source_chat: str | None = None
    source_trace_id: str | None = None
    turn_mode: Literal["single", "multi"] = "single"
    gt_quality: Literal["verified", "approximate"]
    reviewed_by: str | None = None
    difficulty: Literal["easy", "medium", "hard"] | None = None
    legacy_id: str | None = Field(default=None, description="Original id from datasets/b2c/v2")


class ExpectedOutputCriteria(BaseModel):
    """Evaluation criteria pattern (K-4)."""

    segment: Literal["b2c", "b2b"] | None = None
    product_codes: list[str] = Field(default_factory=list)
    answer_key_points: list[str] = Field(default_factory=list)
    should_clarify: bool | None = None
    acceptable_clarifications: list[str] = Field(default_factory=list)
    must_not: list[str] = Field(default_factory=list)
    tools: list[dict[str, Any]] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class DatasetItem(BaseModel):
    """Single eval dataset item."""

    id: str
    input: str | list[dict[str, str]]
    expected_output: ExpectedOutputCriteria
    metadata: ItemMetadata

    @field_validator("id")
    @classmethod
    def id_not_empty(cls, value: str) -> str:
        if not value.strip():
            msg = "item id must not be empty"
            raise ValueError(msg)
        return value


class DatasetManifest(BaseModel):
    """Top-level dataset manifest file."""

    dataset: str
    group: Literal["e2e", "rag", "behavior", "edge"]
    version: str
    created: str
    description: str
    items: list[DatasetItem]

    @model_validator(mode="after")
    def unique_item_ids(self) -> DatasetManifest:
        ids = [item.id for item in self.items]
        if len(ids) != len(set(ids)):
            msg = "duplicate item ids in manifest"
            raise ValueError(msg)
        return self


def load_manifest(path: Path | str, *, require_reviewed: bool = True) -> DatasetManifest:
    """Load and validate a dataset manifest YAML file."""
    manifest_path = Path(path)
    raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest = DatasetManifest.model_validate(raw)
    version_token = manifest.version
    if version_token not in manifest_path.name:
        msg = f"version {version_token!r} must appear in filename {manifest_path.name!r}"
        raise ValueError(msg)
    if require_reviewed:
        for item in manifest.items:
            if not item.metadata.reviewed_by:
                msg = f"{item.id}: missing reviewed_by (E-13)"
                raise ValueError(msg)
    return manifest


def validate_manifest_file(path: Path | str, *, require_reviewed: bool = True) -> DatasetManifest:
    """Validate manifest; alias for sync/validate entrypoint."""
    return load_manifest(path, require_reviewed=require_reviewed)
