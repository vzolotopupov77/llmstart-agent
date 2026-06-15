"""Experiment runner: Agent Core + Langfuse dataset experiments (E-9)."""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.agent_task import AgentTaskRunner, check_backend_health
from scripts.evaluators import get_e2e_evaluators
from scripts.judge_client import require_openrouter_key
from scripts.langfuse_helpers import (
    auth_check,
    count_dataset_run_items,
    create_langfuse_client,
    load_env_file,
    resolve_dataset_run_url,
)
from scripts.models import load_run_config
from scripts.run_report import write_run_report
from scripts.run_utils import build_run_name, get_git_sha, load_dataset_context

REPO_ROOT = Path(__file__).resolve().parents[2]
EXPERIMENTS_LOG = REPO_ROOT / "evals" / "reports" / "experiments-log.md"


def _safe_print(text: str) -> None:
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", errors="replace").decode("ascii"))


def _slim_langfuse_metadata(run_metadata: dict[str, Any]) -> dict[str, str]:
    """E-30: keep OTEL metadata under 200 chars."""
    return {
        "config_id": str(run_metadata.get("config_id", "")),
        "git_sha8": str(run_metadata.get("git_sha", ""))[:8],
        "dataset": str(run_metadata.get("langfuse_dataset", "")),
        "judge": str(run_metadata.get("judge", {}).get("name", "")),
        "agent_model": str(run_metadata.get("agent_model", {}).get("name", "")),
    }


def _append_experiments_log(run_name: str, dataset_ctx: dict[str, str], config_id: str) -> None:
    EXPERIMENTS_LOG.parent.mkdir(parents=True, exist_ok=True)
    if not EXPERIMENTS_LOG.exists():
        EXPERIMENTS_LOG.write_text(
            "# Experiments log (E-26)\n\n| Date | Run | Config | Dataset | Status |\n"
            "|------|-----|--------|---------|--------|\n",
            encoding="utf-8",
        )
    line = (
        f"| {datetime.now(UTC).date()} | `{run_name}` | `{config_id}` | "
        f"`{dataset_ctx['langfuse_dataset']}` | done |\n"
    )
    with EXPERIMENTS_LOG.open("a", encoding="utf-8") as handle:
        handle.write(line)


def run_experiment(
    config_path: Path,
    dataset_arg: str,
    *,
    dry_run: bool = False,
    max_concurrency: int = 1,
) -> int:
    load_env_file()
    config = load_run_config(config_path)
    dataset_ctx = load_dataset_context(config, dataset_arg)

    require_openrouter_key()
    auth_check()
    check_backend_health(config.agent.api_url)

    langfuse = create_langfuse_client()
    dataset = langfuse.get_dataset(dataset_ctx["langfuse_dataset"])
    if not dataset.items:
        print("Dataset has no items", file=sys.stderr)
        return 1

    if dry_run:
        dataset.items = dataset.items[:1]
        print("Dry run: 1 item only", file=sys.stderr)

    git_sha = get_git_sha()
    run_name = build_run_name(config_id=config.config_id, dataset_slug=dataset_ctx["dataset_slug"])
    run_metadata = {
        "config_id": config.config_id,
        "git_sha": git_sha,
        "dataset_slug": dataset_ctx["dataset_slug"],
        "dataset_version": dataset_ctx["dataset_version"],
        "langfuse_dataset": dataset_ctx["langfuse_dataset"],
        "manifest_path": dataset_ctx["manifest_path"],
        "judge": config.judge.model_dump(),
        "agent_model": config.model.model_dump(),
        "prompt": config.prompt.model_dump(),
        "retrieval": config.retrieval.model_dump(),
    }

    evaluators = get_e2e_evaluators(config.judge)
    task = AgentTaskRunner(config, langfuse_client=langfuse)
    started_at = datetime.now(UTC)

    print(f"Starting experiment: {run_name}", file=sys.stderr)
    print(
        f"Dataset: {dataset_ctx['langfuse_dataset']} ({len(dataset.items)} items)", file=sys.stderr
    )

    result = dataset.run_experiment(
        name=run_name,
        run_name=run_name,
        description=f"Baseline eval for {config.config_id}",
        task=task,
        evaluators=evaluators.item_evaluators,
        run_evaluators=evaluators.run_evaluators,
        max_concurrency=max_concurrency,
        metadata=_slim_langfuse_metadata(run_metadata),
    )

    langfuse.flush()
    dataset_id = dataset.id if dataset.items else None
    linked_count = 0
    if dataset_id and result.dataset_run_id:
        linked_count = count_dataset_run_items(
            langfuse,
            dataset_id=dataset_id,
            run_name=run_name,
        )
    langfuse_linked = linked_count >= len(dataset.items)

    finished_at = datetime.now(UTC)
    report_path = write_run_report(
        run_name=run_name,
        config=config,
        dataset_ctx=dataset_ctx,
        git_sha=git_sha,
        started_at=started_at,
        finished_at=finished_at,
        experiment_result=result,
        run_metadata=run_metadata,
        langfuse_client=langfuse,
        langfuse_linked=langfuse_linked,
        dataset_id=dataset_id,
    )

    _append_experiments_log(run_name, dataset_ctx, config.config_id)

    _safe_print(result.format())
    print(f"Report: {report_path.relative_to(REPO_ROOT)}")
    if langfuse_linked:
        print(f"Langfuse linked: {linked_count}/{len(dataset.items)} items", file=sys.stderr)
    else:
        print(
            f"WARNING: Langfuse linked only {linked_count}/{len(dataset.items)} items",
            file=sys.stderr,
        )
    ui_url = resolve_dataset_run_url(
        langfuse,
        dataset_run_id=result.dataset_run_id,
        dataset_id=dataset_id,
        sdk_url=result.dataset_run_url,
    )
    if ui_url:
        print(f"UI: {ui_url}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run eval experiment on Langfuse dataset")
    parser.add_argument("--config", required=True, help="Path to run config YAML")
    parser.add_argument("--dataset", default="e2e/e2e-qa", help="Dataset group/slug")
    parser.add_argument("--dry-run", action="store_true", help="Run single item only")
    parser.add_argument("--max-concurrency", type=int, default=1)
    parser.add_argument("--no-ui", action="store_true", help="Plain logs (default)")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.is_file():
        print(f"Config not found: {config_path}", file=sys.stderr)
        return 1

    return run_experiment(
        config_path,
        args.dataset,
        dry_run=args.dry_run,
        max_concurrency=args.max_concurrency,
    )


if __name__ == "__main__":
    raise SystemExit(main())
