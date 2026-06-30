"""Dataset sync to Langfuse (E-16)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from scripts.dataset_models import DatasetItem, DatasetManifest, load_manifest
from scripts.langfuse_helpers import (
    REPO_ROOT,
    create_langfuse_client,
    dataset_ui_url,
    ensure_dataset,
    langfuse_dataset_name,
    list_dataset_items,
    load_env_file,
    log_langfuse_error,
)

DATASETS_ROOT = REPO_ROOT / "evals" / "datasets"
OTEL_METADATA_MAX_CHARS = 200


def _metadata_json_len(metadata: dict[str, str]) -> int:
    return len(json.dumps(metadata, ensure_ascii=False, separators=(",", ":")))


def _langfuse_metadata(item: DatasetItem, *, langfuse_id: str) -> dict[str, str]:
    """Compact metadata for Langfuse (E-30: OTEL propagates as experiment_item_metadata)."""
    meta = item.metadata
    compact: dict[str, str] = {
        "id": langfuse_id,
        "seg": meta.segment,
        "int": meta.intent,
        "tm": meta.turn_mode,
    }
    if meta.gt_quality != "verified":
        compact["gq"] = meta.gt_quality[:1]
    if meta.source == "synthetic":
        compact["src"] = "syn"
    if meta.graphrag_type is not None:
        compact["gr_type"] = meta.graphrag_type
    if _metadata_json_len(compact) > OTEL_METADATA_MAX_CHARS:
        compact = {k: compact[k] for k in ("id", "seg", "int")}
    if _metadata_json_len(compact) > OTEL_METADATA_MAX_CHARS:
        msg = (
            f"Langfuse item metadata exceeds {OTEL_METADATA_MAX_CHARS} chars "
            f"for {langfuse_id!r}: {compact!r}"
        )
        raise ValueError(msg)
    return compact


def _discover_manifests(dataset: str) -> list[Path]:
    if dataset == "all":
        return sorted(DATASETS_ROOT.glob("*/*/v*_*.yaml"))
    if "/" in dataset:
        group, name = dataset.split("/", maxsplit=1)
        folder = DATASETS_ROOT / group / name
        return sorted(folder.glob("v*_*.yaml"))
    manifests: list[Path] = []
    for group in ("graphrag", "e2e", "rag", "behavior", "edge"):
        folder = DATASETS_ROOT / group / dataset
        if folder.is_dir():
            manifests.extend(sorted(folder.glob("v*_*.yaml")))
    if manifests:
        return manifests
    folder = DATASETS_ROOT / dataset
    return sorted(folder.glob("v*_*.yaml"))


def langfuse_dataset_item_id(version: str, manifest_item_id: str) -> str:
    """Langfuse item ids are project-global; versioned datasets need a prefix (E-16)."""
    if version == "v001":
        return manifest_item_id
    return f"{version}--{manifest_item_id}"


def sync_manifest(
    manifest: DatasetManifest,
    *,
    client: Any,
    refresh_metadata: bool = False,
) -> tuple[int, int, int]:
    """Upsert manifest items to Langfuse. Returns (created, skipped, refreshed)."""
    dataset_name = langfuse_dataset_name(manifest.group, manifest.dataset, manifest.version)
    ensure_dataset(client, dataset_name, manifest.description)

    existing_ids = {item.id for item in list_dataset_items(client, dataset_name)}
    created = 0
    skipped = 0
    refreshed = 0

    for item in manifest.items:
        lf_id = langfuse_dataset_item_id(manifest.version, item.id)
        metadata = _langfuse_metadata(item, langfuse_id=lf_id)
        if lf_id in existing_ids:
            if refresh_metadata:
                client.api.dataset_items.delete(id=lf_id)
                client.create_dataset_item(
                    id=lf_id,
                    dataset_name=dataset_name,
                    input=item.input,
                    expected_output=item.expected_output.model_dump(exclude_none=True),
                    metadata=metadata,
                )
                refreshed += 1
            else:
                skipped += 1
            continue
        client.create_dataset_item(
            id=lf_id,
            dataset_name=dataset_name,
            input=item.input,
            expected_output=item.expected_output.model_dump(exclude_none=True),
            metadata=metadata,
        )
        created += 1

    return created, skipped, refreshed


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync eval datasets to Langfuse")
    parser.add_argument("--dataset", default="all", help="group/name or all")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument(
        "--draft",
        action="store_true",
        help="Skip reviewed_by gate (draft manifest review phase)",
    )
    parser.add_argument(
        "--refresh-metadata",
        action="store_true",
        help="Re-create existing items with compact OTEL-safe metadata (E-30)",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=REPO_ROOT / ".env",
        help="Path to .env with LANGFUSE_* credentials",
    )
    args = parser.parse_args()

    manifests = _discover_manifests(args.dataset)
    if not manifests:
        print("sync_datasets: no dataset manifests found", file=sys.stderr)
        return 0

    require_reviewed = not args.draft
    for path in manifests:
        load_manifest(path, require_reviewed=require_reviewed)
        print(f"validated: {path.relative_to(REPO_ROOT)}")

    if args.validate_only:
        return 0

    load_env_file(args.env_file)
    try:
        from scripts.langfuse_helpers import require_langfuse_env

        _public, _secret, host = require_langfuse_env()
        client = create_langfuse_client()
    except RuntimeError as exc:
        log_langfuse_error(f"sync_datasets: {exc}")
        return 1

    total_created = 0
    total_refreshed = 0
    last_manifest: DatasetManifest | None = None
    for path in manifests:
        manifest = load_manifest(path, require_reviewed=require_reviewed)
        last_manifest = manifest
        dataset_name = langfuse_dataset_name(manifest.group, manifest.dataset, manifest.version)
        created, skipped, refreshed = sync_manifest(
            manifest,
            client=client,
            refresh_metadata=args.refresh_metadata,
        )
        total_created += created
        total_refreshed += refreshed
        refresh_note = f", {refreshed} metadata refreshed" if refreshed else ""
        print(f"synced: {dataset_name} (+{created} new, {skipped} existing{refresh_note})")

    client.flush()
    if total_created == 0 and total_refreshed == 0:
        print(
            "sync_datasets: all items already present (idempotent). "
            "Use --refresh-metadata to fix OTEL metadata warnings.",
            file=sys.stderr,
        )
    if last_manifest is not None:
        dataset_name = langfuse_dataset_name(
            last_manifest.group,
            last_manifest.dataset,
            last_manifest.version,
        )
        dataset = ensure_dataset(client, dataset_name, last_manifest.description)
        print(f"UI: {dataset_ui_url(host, dataset.project_id, dataset.id)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
