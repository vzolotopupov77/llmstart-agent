"""E-30: Langfuse dataset item metadata must fit OTEL propagation limit."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.dataset_models import load_manifest
from scripts.sync_datasets import (
    OTEL_METADATA_MAX_CHARS,
    _langfuse_metadata,
    _metadata_json_len,
    langfuse_dataset_item_id,
)

DATASETS_ROOT = Path(__file__).resolve().parents[1] / "datasets"


def test_all_manifest_items_metadata_under_otel_limit() -> None:
    manifests = sorted(DATASETS_ROOT.glob("*/*/v*_*.yaml"))
    assert manifests, "expected at least one dataset manifest"
    worst: tuple[int, str, str] | None = None
    for path in manifests:
        manifest = load_manifest(path, require_reviewed=False)
        for item in manifest.items:
            lf_id = langfuse_dataset_item_id(manifest.version, item.id)
            metadata = _langfuse_metadata(item, langfuse_id=lf_id)
            size = _metadata_json_len(metadata)
            if worst is None or size > worst[0]:
                worst = (size, str(path.name), lf_id)
            assert size <= OTEL_METADATA_MAX_CHARS, (
                f"{path.name}/{lf_id}: {size} chars > {OTEL_METADATA_MAX_CHARS}: "
                f"{json.dumps(metadata, ensure_ascii=False)}"
            )
    assert worst is not None
