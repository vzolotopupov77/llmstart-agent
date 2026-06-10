"""Upload a local JSONL dataset to Langfuse as dataset items."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATASET_NAME = "llmstart-agent-v1"
DEFAULT_SOURCE = ROOT / "datasets" / "b2c" / "v2" / "dataset.jsonl"


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if value and value[0] in "\"'" and value[-1] == value[0]:
            value = value[1:-1]
        if key:
            os.environ[key] = value


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            msg = f"{path}:{line_no} invalid JSON: {exc}"
            raise ValueError(msg) from exc
        records.append(record)
    return records


def require_langfuse_env() -> tuple[str, str, str]:
    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY", "").strip()
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY", "").strip()
    host = os.environ.get("LANGFUSE_HOST", os.environ.get("LANGFUSE_BASE_URL", "")).strip()
    missing = [
        name
        for name, value in (
            ("LANGFUSE_PUBLIC_KEY", public_key),
            ("LANGFUSE_SECRET_KEY", secret_key),
            ("LANGFUSE_HOST", host),
        )
        if not value
    ]
    if missing:
        msg = f"Missing required env vars: {', '.join(missing)} (set them in .env)"
        raise RuntimeError(msg)
    return public_key, secret_key, host.rstrip("/")


def dataset_ui_url(host: str, project_id: str, dataset_id: str) -> str:
    return f"{host}/project/{project_id}/datasets/{dataset_id}"


def list_dataset_items(client: Any, dataset_name: str) -> list[Any]:
    items: list[Any] = []
    page = 1
    while True:
        response = client.api.dataset_items.list(
            dataset_name=dataset_name,
            page=page,
            limit=100,
        )
        items.extend(response.data)
        total_pages = getattr(response.meta, "total_pages", page)
        if page >= total_pages or not response.data:
            break
        page += 1
    return items


def ensure_dataset(client: Any, dataset_name: str, description: str | None) -> Any:
    encoded_name = quote(dataset_name, safe="")
    try:
        return client.api.datasets.get(dataset_name=encoded_name)
    except Exception as exc:
        status_code = getattr(exc, "status_code", None)
        if status_code != 404:
            raise
    return client.create_dataset(name=dataset_name, description=description)


def clear_dataset_items(client: Any, dataset_name: str) -> int:
    deleted = 0
    for item in list_dataset_items(client, dataset_name):
        client.api.dataset_items.delete(id=item.id)
        deleted += 1
    return deleted


def upload_items(client: Any, dataset_name: str, records: list[dict[str, Any]]) -> int:
    uploaded = 0
    for record in records:
        item_id = record.get("id")
        if not item_id:
            msg = "Each record must have top-level 'id'"
            raise ValueError(msg)
        for field in ("input", "expected_output", "metadata"):
            if field not in record:
                msg = f"{item_id}: missing top-level field '{field}'"
                raise ValueError(msg)
        client.create_dataset_item(
            id=str(item_id),
            dataset_name=dataset_name,
            input=record["input"],
            expected_output=record["expected_output"],
            metadata=record["metadata"],
        )
        uploaded += 1
    return uploaded


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset-name",
        default=DEFAULT_DATASET_NAME,
        help=f"Langfuse dataset name (default: {DEFAULT_DATASET_NAME})",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help="Path to JSONL file with input/expected_output/metadata fields",
    )
    parser.add_argument(
        "--description",
        default="LLMStart agent validation dataset (B2C v2)",
        help="Dataset description when creating a new dataset",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Delete all existing dataset items before upload",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=ROOT / ".env",
        help="Path to .env with LANGFUSE_* credentials",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    load_env_file(args.env_file)
    public_key, secret_key, host = require_langfuse_env()

    source = args.source.resolve()
    if not source.is_file():
        print(f"Source file not found: {source}", file=sys.stderr)
        return 1

    records = load_jsonl(source)
    if not records:
        print(f"No records found in {source}", file=sys.stderr)
        return 1

    from langfuse import Langfuse

    client = Langfuse(public_key=public_key, secret_key=secret_key, host=host)

    dataset = ensure_dataset(client, args.dataset_name, args.description)
    deleted = 0
    if args.reload:
        deleted = clear_dataset_items(client, args.dataset_name)
        print(f"Reload: deleted {deleted} existing item(s)")

    uploaded = upload_items(client, args.dataset_name, records)
    client.flush()

    url = dataset_ui_url(host, dataset.project_id, dataset.id)
    print(f"Dataset: {args.dataset_name}")
    print(f"Source: {source}")
    print(f"Uploaded items: {uploaded}")
    print(f"UI: {url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
