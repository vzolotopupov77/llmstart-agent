"""Backfill Langfuse dataset_run_items from local run JSON (E-27)."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

from langfuse.model import CreateDatasetRunItemRequest

from scripts.langfuse_helpers import (
    count_dataset_run_items,
    create_langfuse_client,
    load_env_file,
    resolve_dataset_run_url,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNS_DIR = REPO_ROOT / "evals" / "reports" / "runs"


def _input_key(item_input: Any) -> str:
    return json.dumps(item_input, ensure_ascii=False, sort_keys=True)


def _build_item_id_by_input(client: Any, dataset_name: str) -> dict[str, str]:
    dataset = client.get_dataset(dataset_name)
    mapping: dict[str, str] = {}
    for item in dataset.items:
        mapping[_input_key(item.input)] = item.id
    return mapping, dataset.id


def _existing_trace_ids(client: Any, *, dataset_id: str, run_name: str) -> set[str]:
    response = client.api.dataset_run_items.list(dataset_id=dataset_id, run_name=run_name)
    return {row.trace_id for row in response.data if row.trace_id}


def _wait_for_linked_count(
    client: Any,
    *,
    dataset_id: str,
    run_name: str,
    expected: int,
    timeout_s: float = 45.0,
    poll_s: float = 3.0,
) -> int:
    deadline = time.monotonic() + timeout_s
    linked = 0
    while time.monotonic() < deadline:
        linked = count_dataset_run_items(client, dataset_id=dataset_id, run_name=run_name)
        if linked >= expected:
            return linked
        time.sleep(poll_s)
    return linked


def backfill_run_json(
    client: Any,
    json_path: Path,
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    report = json.loads(json_path.read_text(encoding="utf-8"))
    run_name = report["run_name"]
    langfuse_meta = report.get("langfuse", {})
    if langfuse_meta.get("linked") is True:
        return {"run_name": run_name, "status": "skipped", "reason": "already linked"}

    dataset_name = report.get("langfuse_dataset") or report.get("run_metadata", {}).get(
        "langfuse_dataset"
    )
    if not dataset_name:
        return {"run_name": run_name, "status": "error", "reason": "missing langfuse_dataset"}

    item_id_by_input, dataset_id = _build_item_id_by_input(client, dataset_name)
    existing_traces = _existing_trace_ids(client, dataset_id=dataset_id, run_name=run_name)

    created = 0
    skipped = 0
    errors: list[str] = []

    for idx, item in enumerate(report.get("items", [])):
        trace_id = item.get("trace_id")
        if not trace_id:
            errors.append(f"item[{idx}]: missing trace_id")
            continue
        if trace_id in existing_traces:
            skipped += 1
            continue

        dataset_item_id = item_id_by_input.get(_input_key(item.get("input")))
        if not dataset_item_id:
            errors.append(f"item[{idx}]: input not found in dataset {dataset_name}")
            continue

        if dry_run:
            created += 1
            continue

        try:
            client.api.dataset_run_items.create(
                request=CreateDatasetRunItemRequest(
                    runName=run_name,
                    datasetItemId=dataset_item_id,
                    traceId=trace_id,
                )
            )
            created += 1
            existing_traces.add(trace_id)
        except Exception as exc:
            errors.append(f"item[{idx}]: {exc}")

    if not dry_run and created:
        client.flush()

    linked_count = 0
    expected = len(report.get("items", []))
    if not dry_run and expected > 0:
        linked_count = _wait_for_linked_count(
            client,
            dataset_id=dataset_id,
            run_name=run_name,
            expected=expected,
        )
    linked = linked_count >= expected and expected > 0

    dataset_run_id = langfuse_meta.get("dataset_run_id")
    if not dry_run and linked:
        for score in report.get("run_scores", []):
            if not dataset_run_id:
                break
            try:
                client.create_score(
                    dataset_run_id=dataset_run_id,
                    name=score.get("name", "unknown"),
                    value=score.get("value"),
                    comment=score.get("comment"),
                    data_type=score.get("data_type"),
                )
            except Exception as exc:
                errors.append(f"run_score {score.get('name')}: {exc}")
        client.flush()

    if not dry_run:
        report.setdefault("langfuse", {})
        report["langfuse"]["linked"] = linked
        report["langfuse"]["dataset_id"] = dataset_id
        report["langfuse"]["dataset_run_url"] = resolve_dataset_run_url(
            client,
            dataset_run_id=dataset_run_id,
            dataset_id=dataset_id,
            sdk_url=report["langfuse"].get("dataset_run_url"),
        )
        json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    status = "ok" if linked or dry_run else "partial"
    return {
        "run_name": run_name,
        "status": status,
        "created": created,
        "skipped": skipped,
        "linked": linked_count if not dry_run else None,
        "expected": expected,
        "errors": errors,
    }


def backfill_runs(
    *,
    run_name: str | None = None,
    dry_run: bool = False,
) -> list[dict[str, Any]]:
    load_env_file()
    client = create_langfuse_client()

    if run_name:
        paths = [RUNS_DIR / f"{run_name}.json"]
        if not paths[0].is_file():
            msg = f"Run JSON not found: {paths[0]}"
            raise FileNotFoundError(msg)
    else:
        paths = sorted(RUNS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime)

    results: list[dict[str, Any]] = []
    for path in paths:
        result = backfill_run_json(client, path, dry_run=dry_run)
        results.append(result)
        print(
            f"{result['run_name']}: {result['status']} "
            f"(created={result.get('created', 0)}, linked={result.get('linked')})",
            file=sys.stderr,
        )
        if result.get("errors"):
            for err in result["errors"][:5]:
                print(f"  ! {err}", file=sys.stderr)
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill Langfuse dataset_run_items from JSON")
    parser.add_argument("--run", default="", help="Single run name (default: all JSON in runs/)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    results = backfill_runs(run_name=args.run or None, dry_run=args.dry_run)
    failed = [r for r in results if r["status"] == "error"]
    partial = [r for r in results if r["status"] == "partial"]
    return 1 if failed else (1 if partial and not args.dry_run else 0)


if __name__ == "__main__":
    raise SystemExit(main())
