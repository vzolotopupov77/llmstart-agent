"""Local JSON run report writer (E-27, schema v2)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.agent.run_config import RunConfig

REPORTS_DIR = Path(__file__).resolve().parents[1] / "reports" / "runs"


def _evaluation_to_dict(evaluation: Any) -> dict[str, Any]:
    return {
        "name": evaluation.name,
        "value": evaluation.value,
        "comment": getattr(evaluation, "comment", None),
        "data_type": getattr(evaluation, "data_type", None),
    }


def _item_input(item: Any) -> Any:
    if hasattr(item, "input"):
        return item.input
    if isinstance(item, dict):
        return item.get("input")
    return item


def write_run_report(
    *,
    run_name: str,
    config: RunConfig,
    dataset_ctx: dict[str, str],
    git_sha: str,
    started_at: datetime,
    finished_at: datetime,
    experiment_result: Any,
    run_metadata: dict[str, Any],
    langfuse_client: Any | None = None,
    langfuse_linked: bool | None = None,
    dataset_id: str | None = None,
) -> Path:
    """Persist schema v2 JSON report."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    items: list[dict[str, Any]] = []
    for item_result in experiment_result.item_results:
        scores = [_evaluation_to_dict(e) for e in item_result.evaluations]
        items.append(
            {
                "input": _item_input(item_result.item),
                "output": item_result.output,
                "scores": scores,
                "trace_id": item_result.trace_id,
            }
        )

    run_scores = [_evaluation_to_dict(e) for e in experiment_result.run_evaluations]
    total_ms = int((finished_at - started_at).total_seconds() * 1000)

    dataset_run_url = experiment_result.dataset_run_url
    if langfuse_client is not None:
        from scripts.langfuse_helpers import resolve_dataset_run_url

        dataset_run_url = resolve_dataset_run_url(
            langfuse_client,
            dataset_run_id=experiment_result.dataset_run_id,
            dataset_id=dataset_id,
            sdk_url=experiment_result.dataset_run_url,
        )

    payload = {
        "schema_version": 2,
        "run_name": run_name,
        "config_id": config.config_id,
        "dataset_slug": dataset_ctx["dataset_slug"],
        "langfuse_dataset": dataset_ctx["langfuse_dataset"],
        "git_sha": git_sha,
        "started_at": started_at.astimezone(UTC).isoformat(),
        "finished_at": finished_at.astimezone(UTC).isoformat(),
        "timing": {
            "total_duration_ms": total_ms,
            "items_total": len(items),
            "items_with_timing": len(items),
        },
        "judge": {
            "provider": config.judge.provider,
            "name": config.judge.name,
            "temperature": config.judge.temperature,
        },
        "run_metadata": run_metadata,
        "full_config_snapshot": config.model_dump(),
        "items": items,
        "run_scores": run_scores,
        "langfuse": {
            "dataset_run_id": experiment_result.dataset_run_id,
            "dataset_run_url": dataset_run_url,
            "linked": langfuse_linked,
            "dataset_id": dataset_id,
        },
        "source": "experiment",
    }

    out_path = REPORTS_DIR / f"{run_name}.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path
