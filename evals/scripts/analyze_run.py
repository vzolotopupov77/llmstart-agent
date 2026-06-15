"""Generate markdown analysis report from local run JSON (E-27)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from scripts.failure_analysis import (
    analyze_items,
    distribution,
    layer_counts,
    top_worst,
)
from scripts.langfuse_helpers import load_env_file

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNS_DIR = REPO_ROOT / "evals" / "reports" / "runs"


def resolve_run_json(run_name: str) -> Path:
    if run_name:
        path = RUNS_DIR / f"{run_name}.json"
        if not path.is_file():
            msg = f"Run JSON not found: {path}"
            raise FileNotFoundError(msg)
        return path
    candidates = sorted(RUNS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        msg = f"No run JSON files in {RUNS_DIR}"
        raise FileNotFoundError(msg)
    return candidates[0]


def load_run_report(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _run_score(report: dict[str, Any], name: str) -> float | None:
    for score in report.get("run_scores", []):
        if score.get("name") == name:
            return float(score["value"])
    return None


def _threshold_status(
    value: float | None, green: float, red: float, *, higher_is_better: bool
) -> str:
    if value is None:
        return "—"
    if higher_is_better:
        if value >= green:
            return "🟢"
        if value < red:
            return "🔴"
        return "🟡"
    if value <= green:
        return "🟢"
    if value >= red:
        return "🔴"
    return "🟡"


def _format_dist_row(name: str, stats: dict[str, float | int]) -> str:
    return (
        f"| `{name}` | {stats['count']} | {stats['min']:.2f} | {stats['p25']:.2f} | "
        f"{stats['p50']:.2f} | {stats['p75']:.2f} | {stats['max']:.2f} | {stats['avg']:.2f} |"
    )


def build_markdown_report(
    report: dict[str, Any],
    *,
    span_evidence: dict[int, list[str]] | None = None,
    langfuse_host: str | None = None,
    project_id: str | None = None,
) -> str:
    run_name = report["run_name"]
    items_raw = report.get("items", [])
    analyzed = analyze_items(items_raw)
    worst = top_worst(analyzed, 5)
    layers = layer_counts(analyzed)

    ac_run = _run_score(report, "avg_answer_correctness")
    ff_run = _run_score(report, "avg_faithfulness")
    tc_run = _run_score(report, "avg_task_completion")
    er_run = _run_score(report, "error_rate")

    def _fmt(v: float | None) -> str:
        return f"{v:.3f}" if v is not None else "—"

    lines: list[str] = [
        f"# Experiment report: {run_name}",
        "",
        "## Контекст прогона",
        "",
        f"- **Config:** `{report.get('config_id')}`",
        f"- **Dataset:** `{report.get('langfuse_dataset')}`",
        f"- **Judge:** `{report.get('judge', {}).get('name')}`",
        f"- **Agent model:** "
        f"`{report.get('full_config_snapshot', {}).get('model', {}).get('name')}`",
        f"- **Items:** {len(items_raw)}",
        f"- **Duration:** {report.get('timing', {}).get('total_duration_ms', 0) // 1000}s",
        f"- **Git SHA:** `{report.get('git_sha', '')[:8]}`",
        f"- **Source JSON:** `evals/reports/runs/{run_name}.json`",
        "",
        "## Сводка vs пороги (metrics-map, e2e-qa)",
        "",
        "| Метрика | Value | 🟢 порог | 🔴 порог | Статус |",
        "|---------|------:|---------:|---------:|:------:|",
        f"| avg_answer_correctness | {_fmt(ac_run)} | ≥0.75 | <0.60 | "
        f"{_threshold_status(ac_run, 0.75, 0.60, higher_is_better=True)} |",
        f"| avg_faithfulness | {_fmt(ff_run)} | ≥0.85 | <0.70 | "
        f"{_threshold_status(ff_run, 0.85, 0.70, higher_is_better=True)} |",
        f"| avg_task_completion | {_fmt(tc_run)} | ≥0.80 | <0.65 | "
        f"{_threshold_status(tc_run, 0.80, 0.65, higher_is_better=True)} |",
        f"| error_rate | {_fmt(er_run)} | <0.05 | ≥0.10 | "
        f"{_threshold_status(er_run, 0.05, 0.10, higher_is_better=False)} |",
        "",
        "**Вердикт baseline:** главная метрика "
        f"{_threshold_status(ac_run, 0.75, 0.60, higher_is_better=True)} "
        f"({_fmt(ac_run)} vs 0.75). Faithfulness "
        f"{_threshold_status(ff_run, 0.85, 0.70, higher_is_better=True)}, "
        f"task_completion "
        f"{_threshold_status(tc_run, 0.80, 0.65, higher_is_better=True)}. "
        f"Инфрастабильность "
        f"{_threshold_status(er_run, 0.05, 0.10, higher_is_better=False)} "
        f"(error_rate={_fmt(er_run)}).",
        "",
        "## Распределение item-level scores",
        "",
        "| Метрика | n | min | p25 | p50 | p75 | max | avg |",
        "|---------|--:|----:|----:|----:|----:|----:|----:|",
        _format_dist_row(
            "answer_correctness",
            distribution([i.answer_correctness for i in analyzed]),
        ),
        _format_dist_row("faithfulness", distribution([i.faithfulness for i in analyzed])),
        _format_dist_row(
            "task_completion",
            distribution([i.task_completion for i in analyzed]),
        ),
        "",
        "## Таксономия провалов (топ-5 worst + общая)",
        "",
        f"- **retrieval:** {layers['retrieval']} items",
        f"- **generation:** {layers['generation']} items",
        f"- **behavior:** {layers['behavior']} items",
        f"- **unknown:** {layers['unknown']} items",
        "",
        "## Топ-5 худших items",
        "",
    ]

    for rank, item in enumerate(worst, 1):
        lines.extend(
            [
                f"### #{rank} — item index {item.index}",
                "",
                f"- **Input:** {item.input_preview}",
                f"- **Scores:** correctness={item.answer_correctness:.2f}, "
                f"faithfulness={item.faithfulness:.2f}, "
                f"task_completion={item.task_completion:.2f}, "
                f"segment={item.segment_match:.0f}",
                f"- **Слой провала:** `{item.failure_layer}` — {item.layer_reason}",
                f"- **Tools:** {', '.join(item.tools) or '—'}",
            ]
        )
        if item.judge_comment:
            lines.append(f"- **Judge (answer_correctness):** {item.judge_comment[:400]}")
        if item.trace_id and langfuse_host and project_id:
            exp_url = f"{langfuse_host.rstrip('/')}/project/{project_id}/trace/{item.trace_id}"
            lines.append(f"- **Experiment trace (scores):** [{item.trace_id[:12]}…]({exp_url})")
        if item.session_id and langfuse_host and project_id:
            sess_url = (
                f"{langfuse_host.rstrip('/')}/project/{project_id}/sessions/{item.session_id}"
            )
            lines.append(f"- **Agent session (spans):** [{item.session_id[:8]}…]({sess_url})")
        if span_evidence and item.index in span_evidence:
            lines.append("- **Span evidence (agent trace):**")
            lines.extend(span_evidence[item.index])
        lines.append("")

    lines.extend(
        [
            "## Рекомендации (eval-fix, v0.2)",
            "",
            "1. **Generation (приоритет):** низкий answer_correctness при нормальном "
            "faithfulness — улучшить prompt/guardrails (key_points не покрываются; "
            "проверить GEval comments).",
            "2. **Retrieval:** items с faithfulness < 0.70 — проверить chunking/top-k и "
            "обязательность `search_knowledge_base` до ответа.",
            "3. **Behavior:** segment_match / task_completion — multi-turn и objection handling.",
            "4. **Judge:** часть variance от gemini-2.5-flash-lite JSON — рассмотреть judge "
            "gpt-4o-mini для стабильности.",
            "",
            "## Что дальше",
            "",
            "- Согласовать top-3 исправления → candidate config → compare vs baseline (v0.2).",
            "- Задача sprint-01 закрывается после апрува этого отчёта.",
            "",
        ]
    )
    return "\n".join(lines)


def analyze_run(run_name: str, out_dir: Path, *, fetch_spans: bool = True) -> Path:
    json_path = resolve_run_json(run_name)
    report = load_run_report(json_path)
    actual_run_name = report["run_name"]

    span_evidence: dict[int, list[str]] = {}
    langfuse_host: str | None = None
    project_id: str | None = None

    if fetch_spans:
        load_env_file()
        langfuse_host = os.environ.get("LANGFUSE_HOST", "http://localhost:3001")
        try:
            from scripts.langfuse_helpers import create_langfuse_client
            from scripts.trace_evidence import fetch_agent_trace_spans

            client = create_langfuse_client()
            # project id from a sample trace if available
            for item in report.get("items", [])[:1]:
                tid = item.get("trace_id")
                if tid:
                    trace = client.api.trace.get(tid)
                    project_id = getattr(trace, "project_id", None) or "cmq0y543r0006ujmnyb937ki7"
                    break
            analyzed = analyze_items(report.get("items", []))
            for item in top_worst(analyzed, 5):
                if item.session_id:
                    span_evidence[item.index] = fetch_agent_trace_spans(client, item.session_id)
        except Exception as exc:  # noqa: BLE001
            print(f"analyze_run: span fetch skipped ({exc})", file=sys.stderr)

    markdown = build_markdown_report(
        report,
        span_evidence=span_evidence or None,
        langfuse_host=langfuse_host,
        project_id=project_id,
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{actual_run_name}.md"
    out_path.write_text(markdown, encoding="utf-8")
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze eval run from local JSON")
    parser.add_argument("--run", default="", help="Run name (default: latest JSON)")
    parser.add_argument("--out", default="reports/", help="Output directory")
    parser.add_argument("--no-spans", action="store_true", help="Skip Langfuse span fetch")
    args = parser.parse_args()

    out_dir = Path(args.out)
    if not out_dir.is_absolute():
        out_dir = REPO_ROOT / "evals" / out_dir

    try:
        out_path = analyze_run(args.run, out_dir, fetch_spans=not args.no_spans)
    except FileNotFoundError as exc:
        print(f"analyze_run: {exc}", file=sys.stderr)
        return 1

    print(f"Report: {out_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
