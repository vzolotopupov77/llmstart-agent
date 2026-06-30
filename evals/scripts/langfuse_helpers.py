"""Shared Langfuse client helpers for eval contour."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any
from urllib.parse import quote

REPO_ROOT = Path(__file__).resolve().parents[2]


def load_env_file(path: Path | None = None) -> None:
    env_path = path or REPO_ROOT / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
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


def langfuse_dataset_name(group: str, dataset: str, version: str) -> str:
    """E-16 folders-as-versions: ``e2e/e2e-qa/v001``."""
    return f"{group}/{dataset}/{version}"


def dataset_ui_url(host: str, project_id: str, dataset_id: str) -> str:
    return f"{host}/project/{project_id}/datasets/{dataset_id}"


def dataset_run_ui_url(
    host: str,
    *,
    project_id: str,
    dataset_id: str,
    dataset_run_id: str,
) -> str:
    return f"{host}/project/{project_id}/datasets/{dataset_id}/runs/{dataset_run_id}"


def count_dataset_run_items(client: Any, *, dataset_id: str, run_name: str) -> int:
    """Count linked run items with pagination (default page size is 10 — must paginate)."""
    total = 0
    page = 1
    while True:
        response = client.api.dataset_run_items.list(
            dataset_id=dataset_id,
            run_name=run_name,
            page=page,
            limit=100,
        )
        total += len(response.data)
        total_pages = getattr(response.meta, "total_pages", page)
        if page >= total_pages or not response.data:
            break
        page += 1
    return total


def resolve_dataset_run_url(
    client: Any,
    *,
    dataset_run_id: str | None,
    dataset_id: str | None,
    sdk_url: str | None,
) -> str | None:
    """Fallback when SDK returns dataset_run_url=null."""
    if sdk_url:
        return sdk_url
    if not dataset_run_id or not dataset_id:
        return None
    _, _, host = require_langfuse_env()
    project_id = getattr(client, "_get_project_id", lambda: None)()
    if not project_id:
        return None
    return dataset_run_ui_url(
        host,
        project_id=project_id,
        dataset_id=dataset_id,
        dataset_run_id=dataset_run_id,
    )


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


def create_langfuse_client() -> Any:
    load_env_file()
    public_key, secret_key, host = require_langfuse_env()
    from langfuse import Langfuse

    return Langfuse(public_key=public_key, secret_key=secret_key, host=host)


def auth_check() -> None:
    """Fail-fast Langfuse credentials check."""
    load_env_file()
    require_langfuse_env()


def log_langfuse_error(message: str) -> None:
    print(message, file=sys.stderr)
