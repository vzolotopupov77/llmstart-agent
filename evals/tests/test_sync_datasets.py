"""Tests for Langfuse dataset sync (E-16)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from scripts.dataset_models import (
    DatasetItem,
    DatasetManifest,
    ExpectedOutputCriteria,
    ItemMetadata,
)
from scripts.sync_datasets import (
    OTEL_METADATA_MAX_CHARS,
    _langfuse_metadata,
    _metadata_json_len,
    langfuse_dataset_item_id,
    sync_manifest,
)


def _sample_manifest() -> DatasetManifest:
    item = DatasetItem(
        id="e2e-qa-0001",
        input="test question",
        expected_output=ExpectedOutputCriteria(
            segment="b2c",
            answer_key_points=["point"],
        ),
        metadata=ItemMetadata(
            segment="b2c",
            intent="G1.1",
            source="synthetic",
            gt_quality="verified",
            reviewed_by="tester",
        ),
    )
    return DatasetManifest(
        dataset="e2e-qa",
        group="e2e",
        version="v001",
        created="2026-06-14",
        description="test",
        items=[item],
    )


def test_sync_skips_existing_items() -> None:
    manifest = _sample_manifest()
    client = MagicMock()
    client.api.dataset_items.list.return_value = SimpleNamespace(
        data=[SimpleNamespace(id="e2e-qa-0001")],
        meta=SimpleNamespace(total_pages=1),
    )

    created, skipped, refreshed = sync_manifest(manifest, client=client)

    assert created == 0
    assert skipped == 1
    assert refreshed == 0
    client.create_dataset_item.assert_not_called()


def test_sync_creates_missing_items() -> None:
    manifest = _sample_manifest()
    client = MagicMock()
    client.api.dataset_items.list.return_value = SimpleNamespace(
        data=[],
        meta=SimpleNamespace(total_pages=1),
    )

    created, skipped, refreshed = sync_manifest(manifest, client=client)

    assert created == 1
    assert skipped == 0
    assert refreshed == 0
    client.create_dataset_item.assert_called_once()
    assert client.create_dataset_item.call_args.kwargs["id"] == "e2e-qa-0001"


def test_sync_v002_uses_version_prefixed_langfuse_id() -> None:
    manifest = _sample_manifest().model_copy(update={"version": "v002"})
    client = MagicMock()
    client.api.dataset_items.list.return_value = SimpleNamespace(
        data=[],
        meta=SimpleNamespace(total_pages=1),
    )

    created, _skipped, refreshed = sync_manifest(manifest, client=client)

    assert created == 1
    assert refreshed == 0
    assert client.create_dataset_item.call_args.kwargs["id"] == "v002--e2e-qa-0001"


def test_langfuse_metadata_fits_otel_limit() -> None:
    manifest = _sample_manifest()
    lf_id = langfuse_dataset_item_id(manifest.version, manifest.items[0].id)
    metadata = _langfuse_metadata(manifest.items[0], langfuse_id=lf_id)
    assert _metadata_json_len(metadata) <= OTEL_METADATA_MAX_CHARS


def test_refresh_metadata_recreates_existing_items() -> None:
    manifest = _sample_manifest()
    client = MagicMock()
    client.api.dataset_items.list.return_value = SimpleNamespace(
        data=[SimpleNamespace(id="e2e-qa-0001")],
        meta=SimpleNamespace(total_pages=1),
    )

    created, skipped, refreshed = sync_manifest(
        manifest,
        client=client,
        refresh_metadata=True,
    )

    assert created == 0
    assert skipped == 0
    assert refreshed == 1
    client.api.dataset_items.delete.assert_called_once_with(id="e2e-qa-0001")
    client.create_dataset_item.assert_called_once()
    metadata = client.create_dataset_item.call_args.kwargs["metadata"]
    assert _metadata_json_len(metadata) <= OTEL_METADATA_MAX_CHARS
