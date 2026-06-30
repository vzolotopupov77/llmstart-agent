"""Run naming, git sha, dataset resolution (E-9, E-16)."""

from __future__ import annotations

import subprocess
from datetime import UTC, datetime
from pathlib import Path

from app.agent.run_config import RunConfig

from scripts.dataset_models import load_manifest
from scripts.langfuse_helpers import REPO_ROOT, langfuse_dataset_name

DATASETS_ROOT = REPO_ROOT / "evals" / "datasets"


def get_git_sha() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=REPO_ROOT,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"
    return result.stdout.strip()


def build_run_name(*, config_id: str, dataset_slug: str) -> str:
    sha8 = get_git_sha()[:8]
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"{config_id}--{dataset_slug}--{sha8}--{ts}"


def resolve_dataset_slug(dataset_arg: str) -> tuple[str, str, str]:
    """Parse CLI dataset arg -> (group, slug, langfuse name)."""
    if dataset_arg in ("all", "e2e-qa"):
        group, slug, version = "e2e", "e2e-qa", "v001"
    elif "/" in dataset_arg:
        parts = dataset_arg.split("/")
        if len(parts) == 2:
            group, slug = parts[0], parts[1]
            version = "v001"
        else:
            group, slug, version = parts[0], parts[1], parts[2]
    else:
        group, slug, version = "e2e", dataset_arg, "v001"
    lf_name = langfuse_dataset_name(group, slug, version)
    return slug, version, lf_name


def find_manifest_path(group: str, slug: str, version: str, config: RunConfig) -> Path:
    pinned = config.datasets.get(slug)
    if pinned:
        version = pinned
    folder = DATASETS_ROOT / group / slug
    matches = sorted(folder.glob(f"{version}_*.yaml"))
    if not matches:
        msg = f"No manifest for {group}/{slug}/{version}"
        raise FileNotFoundError(msg)
    return matches[0]


def _group_for_arg(dataset_arg: str, config: RunConfig) -> str:
    """Derive dataset group from CLI arg and run config."""
    if "/" in dataset_arg:
        return dataset_arg.split("/")[0]
    if dataset_arg in ("all", "e2e-qa"):
        return "e2e"
    slug = dataset_arg
    if slug in config.datasets:
        pinned_version = config.datasets[slug]
        for group in ("graphrag", "e2e", "rag", "behavior", "edge"):
            folder = DATASETS_ROOT / group / slug
            if list(folder.glob(f"{pinned_version}_*.yaml")):
                return group
    if config.config_id.startswith("graphrag-"):
        return "graphrag"
    return "e2e"


def load_dataset_context(config: RunConfig, dataset_arg: str) -> dict[str, str]:
    group = _group_for_arg(dataset_arg, config)
    slug, version, _lf_name = resolve_dataset_slug(dataset_arg)
    manifest_path = find_manifest_path(group, slug, version, config)
    manifest = load_manifest(manifest_path)
    version = manifest.version
    lf_name = langfuse_dataset_name(group, slug, version)
    return {
        "group": group,
        "dataset_slug": slug,
        "dataset_version": version,
        "langfuse_dataset": lf_name,
        "manifest_path": str(manifest_path.relative_to(REPO_ROOT)),
        "description": manifest.description,
    }
