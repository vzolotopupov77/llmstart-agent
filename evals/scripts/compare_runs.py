"""Compare two eval runs from local JSON reports (E-16, E-27)."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNS_DIR = REPO_ROOT / "evals" / "reports" / "runs"

RUN_LEVEL_METRICS = (
    "avg_answer_correctness",
    "avg_faithfulness",
    "avg_task_completion",
    "error_rate",
    "segment_match_rate",
)

DELTA_THRESHOLD = 0.05


@dataclass(frozen=True)
class ChangeFactor:
    name: str
    value_a: str
    value_b: str
    changed: bool


@dataclass(frozen=True)
class ItemPatternStats:
    total: int
    same_agent_output: int
    changed_agent_output: int
    score_only_improved: int
    score_only_regressed: int
    zero_to_pass: int
    zero_to_fail: int


@dataclass(frozen=True)
class ItemDelta:
    index: int
    score_a: float
    score_b: float
    delta: float
    input_preview: str


def resolve_run_json(run_name: str) -> Path:
    path = RUNS_DIR / f"{run_name}.json"
    if not path.is_file():
        msg = f"Run JSON not found: {path}"
        raise FileNotFoundError(msg)
    return path


def load_run_report(run_name: str) -> dict[str, Any]:
    path = resolve_run_json(run_name)
    return json.loads(path.read_text(encoding="utf-8"))


def _dataset_version(report: dict[str, Any]) -> str:
    meta = report.get("run_metadata") or {}
    version = meta.get("dataset_version")
    if version:
        return str(version)
    langfuse_dataset = str(report.get("langfuse_dataset", ""))
    if "/v" in langfuse_dataset:
        return langfuse_dataset.rsplit("/v", 1)[-1]
    return "unknown"


def validate_comparable(run_a: dict[str, Any], run_b: dict[str, Any]) -> list[str]:
    """E-16: same dataset version required. Returns non-blocking warnings."""
    warnings: list[str] = []
    ds_a = run_a.get("langfuse_dataset")
    ds_b = run_b.get("langfuse_dataset")
    if ds_a != ds_b:
        msg = f"Несовпадение датасета (E-16): A={ds_a!r}, B={ds_b!r}"
        raise ValueError(msg)

    ver_a = _dataset_version(run_a)
    ver_b = _dataset_version(run_b)
    if ver_a != ver_b:
        msg = f"Несовпадение версии датасета (E-16): A={ver_a!r}, B={ver_b!r}"
        raise ValueError(msg)

    count_a = len(run_a.get("items") or [])
    count_b = len(run_b.get("items") or [])
    if count_a != count_b:
        warnings.append(f"Разное число items: A={count_a}, B={count_b}")

    if run_a.get("config_id") != run_b.get("config_id"):
        warnings.append(
            f"Разный config_id: A={run_a.get('config_id')!r}, B={run_b.get('config_id')!r}"
        )

    judge_a = (run_a.get("judge") or {}).get("name")
    judge_b = (run_b.get("judge") or {}).get("name")
    if judge_a != judge_b:
        warnings.append(f"Разный judge: A={judge_a!r}, B={judge_b!r}")

    if run_a.get("config_id") == run_b.get("config_id") and judge_a == judge_b:
        git_a = str(run_a.get("git_sha", ""))[:8]
        git_b = str(run_b.get("git_sha", ""))[:8]
        if git_a == git_b:
            warnings.append(
                "Одинаковые config, git и judge: дельта scores скорее от evaluators "
                "или non-determinism агента/судьи — интерпретируй с осторожностью."
            )

    return warnings


def _run_score(report: dict[str, Any], metric_name: str) -> float | None:
    for score in report.get("run_scores") or []:
        if score.get("name") == metric_name:
            value = score.get("value")
            if isinstance(value, (int, float)):
                return float(value)
    return None


def _item_score(item: dict[str, Any], metric_name: str) -> float | None:
    for score in item.get("scores") or []:
        if score.get("name") == metric_name:
            value = score.get("value")
            if isinstance(value, (int, float)):
                return float(value)
    return None


def _input_preview(item: dict[str, Any], *, limit: int = 120) -> str:
    raw = item.get("input")
    if isinstance(raw, str):
        text = raw
    elif isinstance(raw, list):
        parts: list[str] = []
        for turn in raw:
            role = turn.get("role", "user")
            content = turn.get("content", "")
            parts.append(f"{role}: {content}")
        text = "\n".join(parts)
    else:
        text = str(raw)
    text = " ".join(text.split())
    if len(text) > limit:
        return text[: limit - 1] + "…"
    return text


def _item_message(item: dict[str, Any]) -> str:
    output = item.get("output") or {}
    if isinstance(output, dict):
        return str(output.get("message") or output.get("actual_output") or "")
    return str(output)


def _meta_field(report: dict[str, Any], field: str, default: str = "—") -> str:
    meta = report.get("run_metadata") or {}
    snapshot = report.get("full_config_snapshot") or {}

    if field == "agent_model":
        block = meta.get("agent_model") or snapshot.get("model") or {}
        if isinstance(block, dict):
            return str(block.get("name") or default)
        return str(block)
    if field == "prompt":
        block = meta.get("prompt") or snapshot.get("prompt") or {}
        if isinstance(block, dict):
            return str(block.get("name") or default)
        return str(block)
    if field == "retrieval":
        block = meta.get("retrieval") or snapshot.get("retrieval") or {}
        if isinstance(block, dict):
            return str(block.get("backend") or block.get("name") or default)
        return str(block)

    for source in (meta, snapshot, report):
        val = source.get(field)
        if val is not None:
            return str(val)
    return default


def detect_change_factors(run_a: dict[str, Any], run_b: dict[str, Any]) -> list[ChangeFactor]:
    """What differs between runs — basis for factorial interpretation."""
    factors = [
        ChangeFactor(
            "config_id",
            str(run_a.get("config_id", "—")),
            str(run_b.get("config_id", "—")),
            run_a.get("config_id") != run_b.get("config_id"),
        ),
        ChangeFactor(
            "git_sha",
            str(run_a.get("git_sha", ""))[:8],
            str(run_b.get("git_sha", ""))[:8],
            str(run_a.get("git_sha", ""))[:8] != str(run_b.get("git_sha", ""))[:8],
        ),
        ChangeFactor(
            "agent_model",
            _meta_field(run_a, "agent_model"),
            _meta_field(run_b, "agent_model"),
            _meta_field(run_a, "agent_model") != _meta_field(run_b, "agent_model"),
        ),
        ChangeFactor(
            "prompt",
            _meta_field(run_a, "prompt"),
            _meta_field(run_b, "prompt"),
            _meta_field(run_a, "prompt") != _meta_field(run_b, "prompt"),
        ),
        ChangeFactor(
            "retrieval",
            _meta_field(run_a, "retrieval"),
            _meta_field(run_b, "retrieval"),
            _meta_field(run_a, "retrieval") != _meta_field(run_b, "retrieval"),
        ),
        ChangeFactor(
            "judge",
            (run_a.get("judge") or {}).get("name", "—"),
            (run_b.get("judge") or {}).get("name", "—"),
            (run_a.get("judge") or {}).get("name") != (run_b.get("judge") or {}).get("name"),
        ),
        ChangeFactor(
            "dataset",
            str(run_a.get("langfuse_dataset", "—")),
            str(run_b.get("langfuse_dataset", "—")),
            run_a.get("langfuse_dataset") != run_b.get("langfuse_dataset"),
        ),
    ]
    return factors


def analyze_item_patterns(
    run_a: dict[str, Any],
    run_b: dict[str, Any],
    *,
    primary_metric: str = "answer_correctness",
) -> ItemPatternStats:
    items_a = run_a.get("items") or []
    items_b = run_b.get("items") or []
    limit = min(len(items_a), len(items_b))

    same_output = 0
    changed_output = 0
    score_only_improved = 0
    score_only_regressed = 0
    zero_to_pass = 0
    zero_to_fail = 0

    for idx in range(limit):
        msg_a = _item_message(items_a[idx])
        msg_b = _item_message(items_b[idx])
        same_msg = msg_a.strip() == msg_b.strip()
        if same_msg:
            same_output += 1
        else:
            changed_output += 1

        score_a = _item_score(items_a[idx], primary_metric)
        score_b = _item_score(items_b[idx], primary_metric)
        if score_a is None or score_b is None:
            continue

        delta = score_b - score_a
        if same_msg and delta >= DELTA_THRESHOLD:
            score_only_improved += 1
        if same_msg and delta <= -DELTA_THRESHOLD:
            score_only_regressed += 1
        if score_a < 0.05 and score_b >= 0.5:
            zero_to_pass += 1
        if score_a >= 0.5 and score_b < 0.05:
            zero_to_fail += 1

    return ItemPatternStats(
        total=limit,
        same_agent_output=same_output,
        changed_agent_output=changed_output,
        score_only_improved=score_only_improved,
        score_only_regressed=score_only_regressed,
        zero_to_pass=zero_to_pass,
        zero_to_fail=zero_to_fail,
    )


def _metric_delta(run_a: dict[str, Any], run_b: dict[str, Any], name: str) -> float | None:
    a = _run_score(run_a, name)
    b = _run_score(run_b, name)
    if a is None or b is None:
        return None
    return b - a


def _interpret_primary_delta(
    factors: list[ChangeFactor],
    patterns: ItemPatternStats,
    ac_delta: float | None,
) -> list[str]:
    lines: list[str] = []
    agent_changed = any(
        f.changed for f in factors if f.name in ("config_id", "agent_model", "prompt", "retrieval")
    )
    judge_changed = next((f for f in factors if f.name == "judge"), None)
    git_changed = next((f for f in factors if f.name == "git_sha"), None)

    if ac_delta is not None:
        direction = "рост" if ac_delta > 0 else ("падение" if ac_delta < 0 else "без изменений")
        lines.append(
            f"- **Главная метрика (`avg_answer_correctness`):** {direction} "
            f"**{ac_delta:+.3f}** (A → B)."
        )

    if not agent_changed and not (git_changed and git_changed.changed):
        if patterns.score_only_improved > 0 or patterns.zero_to_pass > 0:
            lines.append(
                f"- **Доминирующий фактор — методология оценки (evaluator/judge input):** "
                f"{patterns.score_only_improved} items улучшились при **том же** ответе; "
                f"{patterns.zero_to_pass} items: ~0 → pass (artifact broken GEval)."
            )
        if patterns.changed_agent_output > 0:
            lines.append(
                f"- **Смешанный эффект:** {patterns.changed_agent_output} items с другим ответом "
                "агента (re-run non-determinism) — часть Δ не только от судьи."
            )
    elif agent_changed:
        changed = [f.name for f in factors if f.changed and f.name != "dataset"]
        lines.append(
            f"- **Доминирующий фактор — изменение системы:** {', '.join(changed)}. "
            "Δ отражает эффект candidate vs baseline (E-7)."
        )

    if judge_changed and judge_changed.changed:
        lines.append(
            f"- **Смена judge:** {judge_changed.value_a} → {judge_changed.value_b} — "
            "сравнение частично confound; фиксируй judge при eval-fix loop."
        )

    return lines


def build_factor_analysis_section(
    run_a: dict[str, Any],
    run_b: dict[str, Any],
    *,
    warnings: list[str] | None = None,
) -> list[str]:
    """Factorial interpretation + forward recommendations."""
    factors = detect_change_factors(run_a, run_b)
    patterns = analyze_item_patterns(run_a, run_b)
    item_deltas = compute_item_deltas(run_a, run_b)

    lines: list[str] = [
        "## Факторный анализ",
        "",
        "### Изменённые факторы",
        "",
        "| Фактор | A | B | Изменился |",
        "|--------|---|---|:---------:|",
    ]

    labels = {
        "config_id": "Config",
        "git_sha": "Git SHA",
        "agent_model": "Agent model",
        "prompt": "Prompt",
        "retrieval": "Retrieval",
        "judge": "Judge",
        "dataset": "Dataset",
    }
    for factor in factors:
        mark = "✅" if factor.changed else "—"
        lines.append(
            f"| {labels.get(factor.name, factor.name)} | `{factor.value_a}` | "
            f"`{factor.value_b}` | {mark} |"
        )
    lines.append("")

    lines.extend(["### Декомposition метрик (B − A)", ""])
    metric_notes = {
        "avg_answer_correctness": "главная (E-18): покрытие key_points",
        "avg_faithfulness": "guard: опора на retrieval context",
        "avg_task_completion": "guard: выполнение задачи пользователя",
        "error_rate": "infra: падения runner/API",
        "segment_match_rate": "guard: B2C/B2B routing",
    }
    for metric in RUN_LEVEL_METRICS:
        delta = _metric_delta(run_a, run_b, metric)
        if delta is None:
            continue
        if abs(delta) < 0.01:
            verdict = "стабильно"
        elif delta > 0:
            verdict = "улучшение" if metric != "error_rate" else "ухудшение (больше ошибок)"
        else:
            verdict = "ухудшение" if metric != "error_rate" else "улучшение (меньше ошибок)"
        lines.append(
            f"- **`{metric}`** ({metric_notes.get(metric, '')}): Δ={delta:+.3f} — {verdict}."
        )
    lines.append("")

    ac_delta = _metric_delta(run_a, run_b, "avg_answer_correctness")
    lines.extend(["### Интерпретация", ""])
    lines.extend(_interpret_primary_delta(factors, patterns, ac_delta))

    if patterns.total:
        same_pct = 100 * patterns.same_agent_output / patterns.total
        lines.append(
            f"- **Agent output:** идентичен в {patterns.same_agent_output}/{patterns.total} "
            f"items ({same_pct:.0f}%), изменён в {patterns.changed_agent_output}."
        )
    lines.append("")

    # Cross-metric item patterns for answer_correctness
    if item_deltas:
        improved = [d for d in item_deltas if d.delta >= DELTA_THRESHOLD]
        regressed = [d for d in item_deltas if d.delta <= -DELTA_THRESHOLD]
        stable = len(item_deltas) - len(improved) - len(regressed)
        lines.extend(
            [
                "### Паттерны по items (answer_correctness)",
                "",
                f"- Улучшились (Δ≥{DELTA_THRESHOLD}): **{len(improved)}** · "
                f"ухудшились: **{len(regressed)}** · стабильны: **{stable}**",
                f"- Score-only улучшения (тот же ответ агента): **{patterns.score_only_improved}**",
                f"- 0 → ≥0.5 (очистка judge artifact): **{patterns.zero_to_pass}**",
                f"- ≥0.5 → 0 (реgression / judge): **{patterns.zero_to_fail}**",
                "",
            ]
        )

    lines.extend(["### Рекомендации", ""])

    agent_changed = any(
        f.changed for f in factors if f.name in ("config_id", "agent_model", "prompt", "retrieval")
    )

    if not agent_changed:
        lines.extend(
            [
                "1. **Не трактовать Δ как улучшение агента** — config/git/agent не менялись; "
                "зафиксируй **канонический baseline** (run B) для Task 04+.",
                "2. **Следующий compare:** candidate (один параметр, E-7) vs канонический "
                "baseline на `e2e/e2e-qa/v001`.",
                "3. **При candidate-прогоне** смотри: `avg_answer_correctness` ↑ при стабильном "
                "`error_rate` и без просадки `avg_faithfulness`.",
            ]
        )
    else:
        lines.extend(
            [
                "1. **Принять candidate**, если главная метрика ↑, guard-метрики не просели, "
                "`error_rate` < 0.05.",
                "2. **Разобрать regressed items** — retrieval vs generation (analyze report).",
                "3. **Зафиксировать** winning config в `evals/configs/` и experiments-log.",
            ]
        )

    lines.extend(
        [
            "4. **Judge variance:** при пограничных Δ — повторный прогон или стабильный judge "
            "(gpt-4o-mini) для arbitration.",
        ]
    )

    if warnings:
        lines.extend(["", "_Учитывай предупреждения в начале отчёта._"])

    lines.append("")
    return lines


def compute_item_deltas(
    run_a: dict[str, Any],
    run_b: dict[str, Any],
    *,
    metric_name: str = "answer_correctness",
) -> list[ItemDelta]:
    items_a = run_a.get("items") or []
    items_b = run_b.get("items") or []
    limit = min(len(items_a), len(items_b))
    deltas: list[ItemDelta] = []
    for idx in range(limit):
        score_a = _item_score(items_a[idx], metric_name)
        score_b = _item_score(items_b[idx], metric_name)
        if score_a is None or score_b is None:
            continue
        deltas.append(
            ItemDelta(
                index=idx,
                score_a=score_a,
                score_b=score_b,
                delta=score_b - score_a,
                input_preview=_input_preview(items_a[idx]),
            )
        )
    return deltas


def _fmt_delta(value: float | None, *, higher_is_better: bool = True) -> str:
    if value is None:
        return "—"
    sign = "+" if value >= 0 else ""
    arrow = "↑" if value > 0 else ("↓" if value < 0 else "→")
    if not higher_is_better:
        arrow = "↓" if value > 0 else ("↑" if value < 0 else "→")
    return f"{sign}{value:.3f} {arrow}"


def build_compare_markdown(
    run_a_name: str,
    run_b_name: str,
    run_a: dict[str, Any],
    run_b: dict[str, Any],
    *,
    warnings: list[str] | None = None,
) -> str:
    item_deltas = compute_item_deltas(run_a, run_b)
    improved = sorted(
        [d for d in item_deltas if d.delta >= DELTA_THRESHOLD],
        key=lambda d: d.delta,
        reverse=True,
    )[:5]
    regressed = sorted(
        [d for d in item_deltas if d.delta <= -DELTA_THRESHOLD],
        key=lambda d: d.delta,
    )[:5]

    lines: list[str] = [
        f"# Compare: `{run_a_name}` (A) vs `{run_b_name}` (B)",
        "",
        "## Контекст",
        "",
        f"- **Run A:** `{run_a_name}` · config `{run_a.get('config_id')}` · "
        f"dataset `{run_a.get('langfuse_dataset')}`",
        f"- **Run B:** `{run_b_name}` · config `{run_b.get('config_id')}` · "
        f"dataset `{run_b.get('langfuse_dataset')}`",
        f"- **Items:** {len(run_a.get('items') or [])} (aligned by index)",
        "",
    ]

    if warnings:
        lines.extend(["## ⚠️ Предупреждения", ""])
        lines.extend(f"- {w}" for w in warnings)
        lines.append("")

    lines.extend(
        [
            "## Run-level metrics",
            "",
            "| Метрика | A | B | Δ (B−A) |",
            "|---------|---:|---:|--------:|",
        ]
    )

    higher_better = {
        "avg_answer_correctness": True,
        "avg_faithfulness": True,
        "avg_task_completion": True,
        "error_rate": False,
        "segment_match_rate": True,
    }

    for metric in RUN_LEVEL_METRICS:
        val_a = _run_score(run_a, metric)
        val_b = _run_score(run_b, metric)
        delta = None
        if val_a is not None and val_b is not None:
            delta = val_b - val_a
        a_str = f"{val_a:.3f}" if val_a is not None else "—"
        b_str = f"{val_b:.3f}" if val_b is not None else "—"
        d_str = _fmt_delta(delta, higher_is_better=higher_better.get(metric, True))
        lines.append(f"| `{metric}` | {a_str} | {b_str} | {d_str} |")

    lines.extend(["", "## Item-level: answer_correctness", ""])
    if item_deltas:
        avg_delta = sum(d.delta for d in item_deltas) / len(item_deltas)
        improved_n = sum(1 for d in item_deltas if d.delta >= DELTA_THRESHOLD)
        regressed_n = sum(1 for d in item_deltas if d.delta <= -DELTA_THRESHOLD)
        lines.append(
            f"- **Avg item Δ:** {avg_delta:+.3f} · "
            f"improved ≥{DELTA_THRESHOLD}: {improved_n} · "
            f"regressed ≤-{DELTA_THRESHOLD}: {regressed_n}"
        )
        lines.append("")

    def _item_section(title: str, rows: list[ItemDelta]) -> None:
        lines.extend([f"### {title}", ""])
        if not rows:
            lines.append("_Нет items с |Δ| ≥ threshold._")
            lines.append("")
            return
        for row in rows:
            lines.append(
                f"- **#{row.index}** Δ={row.delta:+.2f} "
                f"({row.score_a:.2f} → {row.score_b:.2f}): {row.input_preview}"
            )
        lines.append("")

    _item_section("Top improved (B vs A)", improved)
    _item_section("Top regressed (B vs A)", regressed)

    lines.extend(build_factor_analysis_section(run_a, run_b, warnings=warnings))

    lines.extend(
        [
            "## Source files",
            "",
            f"- A: `evals/reports/runs/{run_a_name}.json`",
            f"- B: `evals/reports/runs/{run_b_name}.json`",
        ]
    )
    return "\n".join(lines) + "\n"


def compare_runs(
    run_a_name: str,
    run_b_name: str,
    out_dir: Path,
) -> Path:
    run_a = load_run_report(run_a_name)
    run_b = load_run_report(run_b_name)
    warnings = validate_comparable(run_a, run_b)
    markdown = build_compare_markdown(run_a_name, run_b_name, run_a, run_b, warnings=warnings)

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"compare--{run_a_name}--vs--{run_b_name}.md"
    out_path.write_text(markdown, encoding="utf-8")
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare two eval runs (local JSON)")
    parser.add_argument("--a", required=True, help="Run A name (baseline / older)")
    parser.add_argument("--b", required=True, help="Run B name (candidate / newer)")
    parser.add_argument("--out", default="reports/", help="Output directory")
    args = parser.parse_args()

    out_dir = Path(args.out)
    if not out_dir.is_absolute():
        out_dir = REPO_ROOT / "evals" / out_dir

    try:
        out_path = compare_runs(args.a, args.b, out_dir)
    except (FileNotFoundError, ValueError) as exc:
        print(f"compare_runs: {exc}", file=sys.stderr)
        return 1

    print(f"Report: {out_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
