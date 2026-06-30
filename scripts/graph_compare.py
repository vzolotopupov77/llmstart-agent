"""Compare seed vs auto-extracted themes; compute keyword recall; write report.

Usage:
    cd mcp_server && uv run python ../scripts/graph_compare.py
    cd mcp_server && uv run python ../scripts/graph_compare.py --output data/graph/extraction-report.md
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError

sys.path.insert(0, str(Path(__file__).resolve().parent))
from graph_common import (
    REPO_ROOT,
    GraphSettings,
    load_program_texts,
    load_seed_themes,
    normalize_key,
)

DEFAULT_OUTPUT = REPO_ROOT / "data" / "graph" / "extraction-report.md"
EXTRACTION_STATS_PATH = REPO_ROOT / "data" / "graph" / "extraction-stats.json"

AUTO_WITHOUT_SEED_QUERY = """
MATCH (t:Theme {source: 'auto'})
WHERE NOT EXISTS {
  MATCH (s:Theme {source: 'seed'})
  WHERE s.id = t.id OR t.id IN coalesce(s.aliases, [])
}
RETURN t.id AS theme_id, t.name AS name,
       [(c:Course)-[:COVERS]->(t) | c.id] AS coveredBy
ORDER BY theme_id
"""

SEED_WITHOUT_AUTO_QUERY = """
MATCH (t:Theme {source: 'seed'})
WHERE NOT EXISTS {
  MATCH (a:Theme)
  WHERE coalesce(a.source, 'auto') <> 'seed'
    AND (a.id = t.id OR t.id IN coalesce(a.aliases, []))
}
  AND NOT EXISTS {
    MATCH (doc:Document)-[:FROM_DOCUMENT]-(:Chunk)<-[:FROM_CHUNK]-(m:Theme)
    WHERE m.id = t.id OR toString(m.name) IN coalesce(t.aliases, [])
  }
RETURN t.id AS theme_id, t.name AS name
ORDER BY theme_id
"""

MERGED_AUTO_QUERY = """
MATCH (t:Theme {source: 'auto'})
MATCH (s:Theme {source: 'seed'})
WHERE s.id = t.id OR t.id IN coalesce(s.aliases, [])
RETURN count(DISTINCT t) AS cnt
"""


def _keyword_recall(
    seed_themes: list[dict[str, object]], source_text: str
) -> list[dict[str, object]]:
    """For each seed theme, check alias hits in combined source text."""
    lower_text = source_text.lower()
    rows: list[dict[str, object]] = []
    for theme in seed_themes:
        theme_id = str(theme["id"])
        keywords = [theme_id, str(theme["name"])] + [str(a) for a in (theme.get("aliases") or [])]
        keywords = list(dict.fromkeys(keywords))
        hits = [
            kw for kw in keywords if normalize_key(kw) in lower_text or kw.lower() in lower_text
        ]
        total = len(keywords)
        recall = round(len(hits) / total, 2) if total else 0.0
        rows.append(
            {
                "theme_id": theme_id,
                "aliases_total": total,
                "aliases_found": len(hits),
                "recall": recall,
                "hits": hits,
            }
        )
    return rows


def _theme_row_id(row: dict[str, object]) -> str:
    return str(row.get("theme_id") or row.get("id") or "")


def _theme_row_name(row: dict[str, object]) -> str:
    return str(row.get("name") or "")

def _decision_for_theme(
    theme_id: str, auto_new: set[str], seed_unconfirmed: set[str]
) -> tuple[str, str]:
    """Suggest merge/keep/drop action per theme."""
    if theme_id in auto_new:
        return "drop", "Авто-узел без seed-совпадения — merge в canonical или удалить после ревью"
    if theme_id in seed_unconfirmed:
        return "keep", "Seed-тема без авто-подтверждения — оставить (ручной seed authoritative)"
    return "merge", "Совпадение seed/auto или подтверждено alias-recall"


def _load_extraction_stats() -> dict[str, object] | None:
    if not EXTRACTION_STATS_PATH.is_file():
        return None
    try:
        return json.loads(EXTRACTION_STATS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _build_conclusion(
    *,
    seed_count: int,
    stats: dict[str, object],
    avg_alias_recall: float,
    unmatched_ids: list[str],
) -> str:
    exact_pct = float(stats.get("exact_recall_pct", 0.0))
    semantic_pct = float(stats.get("semantic_recall_pct", 0.0))
    semantic_count = int(stats.get("semantic_seed_count", 0))
    merged = int(stats.get("merged", 0))
    dropped = int(stats.get("dropped", 0))
    prolif = float(stats.get("proliferation_factor", 0.0))

    parts = [
        f"**Exact recall {exact_pct:.0f}%** — половина узлов LLM совпадает со slug seed без alias-словаря; "
        "остальное — `RAG`→`rag-basic`, `LangGraph`→`langchain-langgraph`, `evals`→`evaluation`.",
        f"**Semantic recall {semantic_pct:.0f}%** ({semantic_count}/{seed_count}) — entity resolution "
        f"сопоставил почти все seed-темы; strict mode отбросил **{dropped}** chunk-шумовых узлов "
        f"(merge-операций: **{merged}**).",
        f"**Proliferation ~{prolif:.0f}×** — LLM создаёт ~{prolif:.0f} chunk-level Theme на каждую seed-тему "
        "(дубли по чанкам); без ER граф был бы нечитаем.",
        f"**Corpus alias recall {avg_alias_recall:.0%}** — средняя доля alias seed-тем, "
        "найденных в исходных `.md` (независимо от LLM).",
    ]
    if unmatched_ids:
        ids = ", ".join(f"`{x}`" for x in unmatched_ids)
        parts.append(f"**Не сопоставлено:** {ids} — оставить seed, при необходимости дополнить aliases.")
    else:
        parts.append(
            "Все seed-темы подтверждены extraction (merge) или остаются authoritative без LLM-дублей."
        )
    parts.append(
        "Продакшен: alias-словарь (`graph_common.py`) + `GRAPH_EXTRACT_STRICT=true` — см. "
        "`data/graph/entity-resolution.md`."
    )
    return " ".join(parts)


def _seed_ids_from_stats(
    stats: dict[str, object] | None,
    all_seed_ids: set[str],
) -> tuple[set[str], set[str]]:
    """Return (confirmed, unconfirmed) seed ids using extraction-stats when graph is post-merge."""
    if not stats:
        return set(), all_seed_ids
    semantic_raw = stats.get("semantic_seed_ids")
    if isinstance(semantic_raw, list) and semantic_raw:
        confirmed = {str(x) for x in semantic_raw}
        return confirmed, all_seed_ids - confirmed
    semantic_count = int(stats.get("semantic_seed_count", 0))
    if semantic_count <= 0:
        return set(), all_seed_ids
    # Stats exist but id lists missing (older run): cannot infer per-theme confirmation.
    return set(), all_seed_ids


def _render_comparison_section(
    *,
    seed_count: int,
    stats: dict[str, object] | None,
    avg_alias_recall: float,
    unmatched_ids: list[str],
) -> list[str]:
    if stats and int(stats.get("auto_raw", 0)):
        auto_raw = int(stats.get("auto_raw", 0))
        exact_pct = float(stats.get("exact_recall_pct", 0.0))
        semantic_pct = float(stats.get("semantic_recall_pct", 0.0))
        exact_count = int(stats.get("exact_seed_count", 0))
        semantic_count = int(stats.get("semantic_seed_count", 0))
        merged = int(stats.get("merged", 0))
        dropped = int(stats.get("dropped", 0))
        prolif = float(stats.get("proliferation_factor", 0.0))
    else:
        auto_raw = 0
        exact_pct = 0.0
        semantic_pct = 0.0
        exact_count = 0
        semantic_count = 0
        merged = 0
        dropped = 0
        prolif = 0.0

    lines = [
        "## Метрики сравнения: manual seed vs auto extraction",
        "",
        "| Метрика | Значение | Пояснение |",
        "|---------|----------|-----------|",
        f"| Manual seed | {seed_count} тем | Ручной seed (`scripts/seed.cypher`), authoritative |",
    ]
    if auto_raw:
        lines += [
            f"| Auto extract ops | {auto_raw} | {merged} merge + {dropped} drop (chunk-level дубли) |",
            f"| Exact recall | {exact_pct:.0f}% ({exact_count}/{seed_count}) | "
            "`Theme.id` LLM = seed id без alias-словаря |",
            f"| Semantic recall | {semantic_pct:.0f}% ({semantic_count}/{seed_count}) | "
            "Seed-темы, сопоставленные через alias-index при merge |",
            f"| Proliferation | ~{prolif:.0f}× | Chunk-узлов LLM на одну seed-тему ({auto_raw}/{seed_count}) |",
            f"| Corpus alias recall | {avg_alias_recall:.0%} | Alias seed-тем в исходных `.md` (не LLM) |",
        ]
    else:
        lines += [
            "| Auto extract ops | — | Запустите `make graph-extract` |",
            f"| Corpus alias recall | {avg_alias_recall:.0%} | Alias seed-тем в `.md`-программах |",
        ]

    conclusion = (
        _build_conclusion(
            seed_count=seed_count,
            stats=stats or {},
            avg_alias_recall=avg_alias_recall,
            unmatched_ids=unmatched_ids,
        )
        if stats and auto_raw
        else (
            "Запустите `make graph-index` для полного сравнения manual vs auto extraction."
        )
    )
    lines += ["", f"**Вывод:** {conclusion}", ""]
    return lines


def _render_report(
    *,
    seed_themes: list[dict[str, object]],
    auto_new: list[dict[str, object]],
    seed_unconfirmed: list[dict[str, object]],
    seed_confirmed: list[dict[str, object]],
    merged_count: int,
    recall_rows: list[dict[str, object]],
    extraction_stats: dict[str, object] | None,
    graph_summary: dict[str, int],
) -> str:
    ts = datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    avg_recall = (
        round(
            sum(float(r["recall"]) for r in recall_rows) / len(recall_rows),
            2,
        )
        if recall_rows
        else 0.0
    )

    auto_new_ids = {str(r["theme_id"]) for r in auto_new}
    seed_unconf_ids = {_theme_row_id(r) for r in seed_unconfirmed}
    unmatched_ids = sorted(seed_unconf_ids)

    lines = [
        "# Graph Extraction Report",
        f"Generated: {ts}",
        "",
        *_render_comparison_section(
            seed_count=len(seed_themes),
            stats=extraction_stats,
            avg_alias_recall=avg_recall,
            unmatched_ids=unmatched_ids,
        ),
        "## Summary (граф после extract)",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Theme nodes | {graph_summary.get('themes', len(seed_themes))} |",
        f"| REQUIRES edges | {graph_summary.get('requires', 0)} |",
        f"| COVERS edges | {graph_summary.get('covers', 0)} |",
        f"| Auto themes (new, in graph) | {len(auto_new)} |",
        f"| Extract merge ops | {int(extraction_stats.get('merged', 0)) if extraction_stats else merged_count} |",
        f"| Seed confirmed by extract | {len(seed_confirmed)} |",
        f"| Seed without extract match | {len(seed_unconfirmed)} |",
        f"| Avg corpus alias recall | {avg_recall} |",
        "",
        "## Diff: авто-темы без seed-совпадения",
        "| theme_id | name | coveredBy |",
        "|----------|------|-----------|",
    ]
    if auto_new:
        for row in auto_new:
            covered = ", ".join(row["coveredBy"] or []) or "—"
            lines.append(f"| {row['theme_id']} | {row['name']} | {covered} |")
    else:
        lines.append("| — | — | — |")

    lines += [
        "",
        "## Diff: seed-темы без авто-подтверждения",
        "| theme_id | name |",
        "|----------|------|",
    ]
    if seed_unconfirmed:
        for row in seed_unconfirmed:
            lines.append(f"| {_theme_row_id(row)} | {_theme_row_name(row)} |")
    else:
        lines.append("| — | — |")

    lines += [
        "",
        "## Seed-темы, подтверждённые extraction (merge)",
        "| theme_id | name |",
        "|----------|------|",
    ]
    if seed_confirmed:
        for row in seed_confirmed:
            lines.append(f"| {_theme_row_id(row)} | {_theme_row_name(row)} |")
    else:
        lines.append("| — | см. extraction-stats.json (перезапустите extract для списка id) |")

    lines += [
        "",
        "## Corpus alias recall по seed-темам",
        "| theme_id | aliases_total | aliases_found | recall |",
        "|----------|---------------|---------------|--------|",
    ]
    for row in recall_rows:
        lines.append(
            f"| {row['theme_id']} | {row['aliases_total']} | {row['aliases_found']} | {row['recall']} |"
        )

    lines += [
        "",
        "## Решения",
        "| theme_id | action | комментарий |",
        "|----------|--------|-------------|",
    ]
    all_theme_ids = sorted({str(t["id"]) for t in seed_themes} | auto_new_ids)
    for theme_id in all_theme_ids:
        action, comment = _decision_for_theme(theme_id, auto_new_ids, seed_unconf_ids)
        if theme_id in auto_new_ids:
            action = "drop"
            comment = (
                "Нет seed-id — удалить или вручную merge в canonical (см. entity-resolution.md)"
            )
        elif theme_id not in seed_unconf_ids:
            action = "merge"
            comment = "Подтверждено auto-extraction (entity resolution)"
        lines.append(f"| {theme_id} | {action} | {comment} |")

    lines.append("")
    return "\n".join(lines)


def run_compare(output: Path) -> int:
    settings = GraphSettings()
    if not settings.neo4j_password:
        print("ERROR: NEO4J_PASSWORD is not set", file=sys.stderr)
        return 1

    driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )
    try:
        driver.verify_connectivity()
    except (Neo4jError, OSError) as exc:
        print(f"ERROR: Neo4j unavailable: {exc}", file=sys.stderr)
        driver.close()
        return 1

    seed_themes = load_seed_themes(driver)
    texts = load_program_texts()
    combined_text = "\n".join(texts.values())

    auto_new_records, _, _ = driver.execute_query(AUTO_WITHOUT_SEED_QUERY, database_="neo4j")
    merged_records, _, _ = driver.execute_query(MERGED_AUTO_QUERY, database_="neo4j")

    auto_new = [dict(r) for r in auto_new_records]
    merged_count = int(merged_records[0]["cnt"]) if merged_records else 0

    extraction_stats = _load_extraction_stats()
    all_seed_ids = {str(t["id"]) for t in seed_themes}
    confirmed_ids, unconfirmed_ids = _seed_ids_from_stats(extraction_stats, all_seed_ids)

    if confirmed_ids:
        seed_confirmed = [t for t in seed_themes if str(t["id"]) in confirmed_ids]
        seed_unconfirmed = [t for t in seed_themes if str(t["id"]) in unconfirmed_ids]
    else:
        seed_unconf_records, _, _ = driver.execute_query(
            SEED_WITHOUT_AUTO_QUERY, database_="neo4j"
        )
        seed_unconfirmed = [dict(r) for r in seed_unconf_records]
        seed_confirmed = [t for t in seed_themes if str(t["id"]) not in unconfirmed_ids]

    graph_summary: dict[str, int] = {}
    for key, query in [
        ("themes", "MATCH (t:Theme) RETURN count(t) AS c"),
        ("requires", "MATCH ()-[r:REQUIRES]->() RETURN count(r) AS c"),
        ("covers", "MATCH ()-[r:COVERS]->() RETURN count(r) AS c"),
    ]:
        recs, _, _ = driver.execute_query(query, database_="neo4j")
        graph_summary[key] = int(recs[0]["c"]) if recs else 0

    recall_rows = _keyword_recall(seed_themes, combined_text)
    report = _render_report(
        seed_themes=seed_themes,
        auto_new=auto_new,
        seed_unconfirmed=seed_unconfirmed,
        seed_confirmed=seed_confirmed,
        merged_count=merged_count,
        recall_rows=recall_rows,
        extraction_stats=extraction_stats,
        graph_summary=graph_summary,
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    driver.close()

    print(f"Report written: {output}")
    print(
        f"  auto-new: {len(auto_new)}, seed-unconfirmed: {len(seed_unconfirmed)}, merged: {merged_count}"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare seed vs auto graph extraction")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output markdown report path",
    )
    args = parser.parse_args()
    return run_compare(args.output)


if __name__ == "__main__":
    raise SystemExit(main())
