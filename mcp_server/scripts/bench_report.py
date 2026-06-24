"""Aggregate per-backend bench JSON reports into markdown summary."""

from __future__ import annotations

import argparse
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _latest_report(reports_dir: Path, backend: str) -> Path | None:
    candidates = sorted(reports_dir.glob(f"vector-db-{backend}-*.json"))
    return candidates[-1] if candidates else None


def _load_report(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        msg = f"Invalid bench report: {path}"
        raise TypeError(msg)
    return data


def build_summary(backends: list[str], reports_dir: Path) -> str:
    """Build markdown table from latest per-backend JSON reports."""
    rows: list[dict[str, Any]] = []
    dataset = ""
    top_k = ""
    score_threshold = ""

    for backend in backends:
        report_path = _latest_report(reports_dir, backend)
        if report_path is None:
            logger.warning("No report for backend %s", backend)
            continue
        report = _load_report(report_path)
        metrics = report.get("metrics", {})
        dataset = str(report.get("dataset", dataset))
        top_k = str(report.get("top_k", top_k))
        score_threshold = str(report.get("score_threshold", score_threshold))
        rows.append(
            {
                "backend": backend,
                "index_time_s": metrics.get("index_time_s", ""),
                "index_rss_mb": metrics.get("index_rss_mb", ""),
                "p50_latency_ms": metrics.get("p50_latency_ms", ""),
                "p95_latency_ms": metrics.get("p95_latency_ms", ""),
                "precision_at_k": metrics.get("precision_at_k", ""),
                "recall_at_k": metrics.get("recall_at_k", ""),
            },
        )

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        f"# Vector DB Benchmark — {timestamp}",
        "",
        f"dataset: {dataset}",
        f"top_k: {top_k}",
        f"score_threshold: {score_threshold}",
        "",
        "| backend | index_time_s | index_rss_mb | p50_latency_ms | p95_latency_ms | precision@k | recall@k |",
        "|---------|-------------|-------------|----------------|----------------|-------------|----------|",
    ]
    for row in rows:
        lines.append(
            f"| {row['backend']} | {row['index_time_s']} | {row['index_rss_mb']} | "
            f"{row['p50_latency_ms']} | {row['p95_latency_ms']} | "
            f"{row['precision_at_k']} | {row['recall_at_k']} |",
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate vector bench reports")
    parser.add_argument("--backends", nargs="+", required=True)
    parser.add_argument("--reports-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    summary = build_summary(args.backends, args.reports_dir)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out_path = args.out / f"vector-bench-{timestamp}.md"
    out_path.write_text(summary, encoding="utf-8")
    logger.info("Summary written: %s", out_path)


if __name__ == "__main__":
    main()
