"""Run vector bench for all backends and write markdown summary."""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

from scripts.bench import run_bench
from scripts.bench_report import build_summary

logger = logging.getLogger(__name__)


def run_all_backends(
    backends: list[str],
    configs_dir: Path,
    reports_dir: Path,
    *,
    skip_index: bool = False,
) -> Path:
    """Run bench per backend, then aggregate into vector-bench-*.md."""
    for backend in backends:
        logger.info("=== bench: %s ===", backend)
        config_path = configs_dir / f"vector-db-{backend}.yaml"
        if not config_path.exists():
            msg = f"missing bench config: {config_path}"
            raise FileNotFoundError(msg)
        run_bench(config_path, reports_dir, backend=backend, skip_index=skip_index)

    summary = build_summary(backends, reports_dir)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out_path = reports_dir / f"vector-bench-{timestamp}.md"
    out_path.write_text(summary, encoding="utf-8")
    logger.info("Summary written: %s", out_path)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run full vector DB benchmark")
    parser.add_argument("--backends", nargs="+", required=True)
    parser.add_argument("--configs-dir", type=Path, required=True)
    parser.add_argument("--reports-dir", type=Path, required=True)
    parser.add_argument(
        "--skip-index",
        action="store_true",
        help="skip re-indexing; use existing indexes from make index",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    try:
        run_all_backends(
            args.backends,
            args.configs_dir,
            args.reports_dir,
            skip_index=args.skip_index,
        )
    except Exception:
        logger.exception("bench failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
