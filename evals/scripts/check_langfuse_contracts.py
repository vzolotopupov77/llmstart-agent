"""Smoke Langfuse dataset_run_items contract (E-33)."""

from __future__ import annotations

import sys
import time
import uuid

from langfuse.model import CreateDatasetRunItemRequest

from scripts.langfuse_helpers import (
    count_dataset_run_items,
    create_langfuse_client,
    load_env_file,
)


def check_dataset_run_item_contract() -> None:
    """Create + list a dataset run item; fail if worker did not persist it."""
    load_env_file()
    client = create_langfuse_client()
    datasets = client.api.datasets.list(page=1, limit=50)
    ds = None
    item = None
    for entry in datasets.data:
        candidate = client.get_dataset(entry.name)
        if candidate.items:
            ds = candidate
            item = candidate.items[0]
            break
    if ds is None or item is None:
        msg = "No dataset with items in Langfuse — run make eval-sync first"
        raise RuntimeError(msg)

    run_name = f"contract-smoke-{uuid.uuid4().hex[:8]}"

    with client.start_as_current_span(name="contract-smoke") as span:
        client.flush()
        client.api.dataset_run_items.create(
            request=CreateDatasetRunItemRequest(
                runName=run_name,
                datasetItemId=item.id,
                traceId=span.trace_id,
            )
        )
    client.flush()
    time.sleep(5)

    linked = count_dataset_run_items(client, dataset_id=item.dataset_id, run_name=run_name)
    if linked < 1:
        msg = (
            f"dataset_run_items.create ok but list returned {linked} items "
            f"(run={run_name}). Check langfuse-worker logs / DB migrations."
        )
        raise RuntimeError(msg)


def main() -> int:
    try:
        check_dataset_run_item_contract()
    except Exception as exc:
        print(f"Langfuse contract check failed: {exc}", file=sys.stderr)
        return 1
    print("Langfuse dataset_run_item contract ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
