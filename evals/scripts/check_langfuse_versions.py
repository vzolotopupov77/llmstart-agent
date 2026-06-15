"""Langfuse version preflight: running server vs compose pin (E-31/E-33)."""

from __future__ import annotations

import re
import sys

import httpx

from scripts.langfuse_helpers import REPO_ROOT, load_env_file, require_langfuse_env

COMPOSE_FILE = REPO_ROOT / "devops" / "docker-compose.yml"


def _compose_image(service: str) -> str | None:
    if not COMPOSE_FILE.is_file():
        return None
    in_service = False
    for line in COMPOSE_FILE.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith(f"{service}:"):
            in_service = True
            continue
        if in_service and stripped and not line.startswith(" ") and stripped.endswith(":"):
            break
        if in_service and stripped.startswith("image:"):
            return stripped.split(":", maxsplit=1)[1].strip()
    return None


def _parse_semver(tag: str) -> str | None:
    match = re.search(r":(\d+\.\d+\.\d+)", tag)
    return match.group(1) if match else None


def check_langfuse_versions() -> list[str]:
    """Return warning messages (empty = ok)."""
    load_env_file()
    _, _, host = require_langfuse_env()
    warnings: list[str] = []

    try:
        response = httpx.get(f"{host}/api/public/health", timeout=10.0)
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPError as exc:
        warnings.append(f"Langfuse health check failed ({host}): {exc}")
        return warnings

    server_version = str(payload.get("version", ""))
    compose_web = _compose_image("langfuse-web")
    compose_worker = _compose_image("langfuse-worker")

    if compose_web:
        compose_ver = _parse_semver(compose_web)
        if compose_ver and server_version and compose_ver != server_version:
            warnings.append(
                f"Langfuse server {server_version} != compose pin {compose_ver} ({compose_web})"
            )

    if compose_web and compose_worker:
        web_ver = _parse_semver(compose_web)
        worker_ver = _parse_semver(compose_worker)
        if web_ver and worker_ver and web_ver != worker_ver:
            warnings.append(
                f"Langfuse web/worker version skew: web={web_ver}, worker={worker_ver}. "
                "Align tags in devops/docker-compose.yml."
            )

    return warnings


def main() -> int:
    warnings = check_langfuse_versions()
    if warnings:
        for message in warnings:
            print(f"WARNING: {message}", file=sys.stderr)
        return 1
    print("Langfuse version check ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
