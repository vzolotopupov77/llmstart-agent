"""Pydantic models for multimodal RAG eval dataset (sprint-10)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, model_validator

Segment = Literal["S1_text", "S2_chart", "S3_layout", "S4_multi", "S5_unanswerable"]
MultiType = Literal["cross_slide", "single_slide_dense"]


class ItemMetadata(BaseModel):
    source: Literal["synthetic", "real_dialog"] = "synthetic"
    gt_quality: Literal["verified", "approximate"] = "verified"
    reviewed_by: str
    slide_verified: bool = True
    multi_type: MultiType | None = None
    persona: str | None = None
    optional_slides: list[int] = Field(default_factory=list)


class MultimodalDatasetItem(BaseModel):
    id: str
    segment: Segment
    question: str
    reference_answer: str
    required_slides: list[int] = Field(default_factory=list)
    trap_slides: list[int] = Field(default_factory=list)
    required_facts: list[str] = Field(default_factory=list)
    expected_behavior: Literal["refusal"] | None = None
    must_not_invent: list[str] = Field(default_factory=list)
    metadata: ItemMetadata

    @model_validator(mode="after")
    def validate_slide_refs(self) -> MultimodalDatasetItem:
        if self.segment == "S5_unanswerable":
            if not self.trap_slides and not self.required_slides:
                msg = f"{self.id}: S5 needs trap_slides (or legacy required_slides)"
                raise ValueError(msg)
            if self.trap_slides and self.required_slides:
                msg = f"{self.id}: S5 must not set both trap_slides and required_slides"
                raise ValueError(msg)
            return self
        if not self.required_slides:
            msg = f"{self.id}: non-S5 items need required_slides"
            raise ValueError(msg)
        if self.trap_slides:
            msg = f"{self.id}: trap_slides only allowed for S5"
            raise ValueError(msg)
        return self


class MultimodalDataset(BaseModel):
    dataset: str
    group: Literal["rag"] = "rag"
    version: str
    created: str
    description: str
    embedding_model: str
    embedding_dim: int
    top_k: int = 5
    items: list[MultimodalDatasetItem]

    @model_validator(mode="after")
    def unique_ids(self) -> MultimodalDataset:
        ids = [item.id for item in self.items]
        if len(ids) != len(set(ids)):
            msg = "duplicate item ids"
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def s5_has_refusal(self) -> MultimodalDataset:
        for item in self.items:
            if item.segment == "S5_unanswerable" and item.expected_behavior != "refusal":
                msg = f"{item.id}: S5 must set expected_behavior=refusal"
                raise ValueError(msg)
        return self


def item_trap_slides(item: MultimodalDatasetItem) -> set[int]:
    """Trap slides for S5; v001 fallback via required_slides."""
    if item.trap_slides:
        return set(item.trap_slides)
    return set(item.required_slides)


def item_gold_slides(item: MultimodalDatasetItem) -> set[int]:
    return set(item.required_slides)


def load_multimodal_dataset(path: Path | str) -> MultimodalDataset:
    dataset_path = Path(path)
    raw = json.loads(dataset_path.read_text(encoding="utf-8"))
    manifest = MultimodalDataset.model_validate(raw)
    if manifest.version not in dataset_path.name:
        msg = f"version {manifest.version!r} must appear in {dataset_path.name!r}"
        raise ValueError(msg)
    return manifest


def default_dataset_path() -> Path:
    return (
        Path(__file__).resolve().parents[1]
        / "datasets"
        / "multimodal"
        / "multimodal-rag"
        / "v002_2026-07-05.json"
    )
