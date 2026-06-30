"""Run graph-qa.cypher QA checks against Neo4j and print tabular results.

Usage:
    cd mcp_server && uv run python -m scripts.neo4j_qa           # full QA
    cd mcp_server && uv run python -m scripts.neo4j_qa --inspect # stats only
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, NoReturn

from neo4j import Driver, GraphDatabase
from neo4j.exceptions import Neo4jError
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).parent.parent.parent
_QA_FILE = _REPO_ROOT / "scripts" / "graph-qa.cypher"
_COMMENT_LINE = re.compile(r"^\s*//")

# Inline inspect queries (make graph-inspect — no external .cypher file needed)
_INSPECT_QUERIES: list[tuple[str, str]] = [
    (
        "Node counts by label",
        "MATCH (n) RETURN labels(n)[0] AS label, count(n) AS cnt ORDER BY cnt DESC",
    ),
    (
        "Relationship counts by type",
        "MATCH ()-[r]->() RETURN type(r) AS rel, count(r) AS cnt ORDER BY cnt DESC",
    ),
    (
        "Orphan nodes (expect 0)",
        "MATCH (n) WHERE NOT (n)--() RETURN labels(n)[0] AS label, n.id AS id",
    ),
    (
        "COVERS coverage per course",
        "MATCH (c:Course) OPTIONAL MATCH (c)-[:COVERS]->(t:Theme) "
        "RETURN c.id AS course, count(t) AS themes ORDER BY themes DESC",
    ),
]


class QaSettings(BaseSettings):
    """Neo4j connection settings loaded from .env."""

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    neo4j_uri: str = Field(default="bolt://localhost:7687", alias="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", alias="NEO4J_USER")
    neo4j_password: str = Field(default="", alias="NEO4J_PASSWORD")


def _parse_statements(cypher: str) -> list[tuple[str, str]]:
    """Return list of (label, statement) pairs parsed from a .cypher file.

    Comment lines immediately before a statement are collected as its label.
    Comments are stripped before splitting on ';' to avoid splitting on ';'
    inside comment text.
    """
    # Collect block comments (stripped of '//' prefix) associated with each statement
    result: list[tuple[str, str]] = []
    current_comment_lines: list[str] = []

    for raw_chunk in cypher.split(";"):
        lines = raw_chunk.splitlines()
        comment_lines: list[str] = []
        code_lines: list[str] = []
        for line in lines:
            if _COMMENT_LINE.match(line):
                comment_lines.append(line.strip().lstrip("/").strip())
            else:
                code_lines.append(line)

        stmt = "\n".join(code_lines).strip()
        if not stmt:
            # Accumulate trailing comment text for the next real statement
            current_comment_lines.extend(comment_lines)
            continue

        # Use accumulated + current comments as label
        all_comments = current_comment_lines + comment_lines
        label = " | ".join(c for c in all_comments if c) or stmt.splitlines()[0][:60]
        result.append((label, stmt))
        current_comment_lines = []

    return result


def _print_table(keys: list[str], rows: list[dict[str, Any]]) -> None:
    if not rows:
        print("  (no rows)")
        return
    col_widths = {k: len(k) for k in keys}
    for row in rows:
        for k in keys:
            col_widths[k] = max(col_widths[k], len(str(row.get(k, ""))))
    header = "  " + "  ".join(k.ljust(col_widths[k]) for k in keys)
    sep = "  " + "  ".join("-" * col_widths[k] for k in keys)
    print(header)
    print(sep)
    for row in rows:
        print("  " + "  ".join(str(row.get(k, "")).ljust(col_widths[k]) for k in keys))


def _run_query(driver: Driver, stmt: str) -> tuple[list[str], list[dict[str, Any]]]:
    result = driver.execute_query(stmt, database_="neo4j")
    keys: list[str] = result.keys
    rows: list[dict[str, Any]] = [
        dict(zip(keys, rec.values(), strict=True)) for rec in result.records
    ]
    return keys, rows


def run_inspect(*, uri: str, user: str, password: str) -> int:
    """Print quick stats (graph-inspect mode)."""
    driver = GraphDatabase.driver(uri, auth=(user, password))
    try:
        driver.verify_connectivity()
    except (Neo4jError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        driver.close()
        return 1

    print("=== graph-inspect ===\n")
    for title, stmt in _INSPECT_QUERIES:
        print(f"-- {title}")
        try:
            keys, rows = _run_query(driver, stmt)
            _print_table(keys, rows)
        except Neo4jError as exc:
            print(f"  ERROR: {exc}", file=sys.stderr)
        print()

    driver.close()
    return 0


def run_qa(*, uri: str, user: str, password: str) -> int:
    """Execute graph-qa.cypher and print results."""
    if not _QA_FILE.exists():
        print(f"ERROR: QA file not found: {_QA_FILE}", file=sys.stderr)
        return 1

    statements = _parse_statements(_QA_FILE.read_text(encoding="utf-8"))
    print(f"=== graph-qa ({len(statements)} queries from {_QA_FILE.name}) ===\n")

    driver = GraphDatabase.driver(uri, auth=(user, password))
    try:
        driver.verify_connectivity()
    except (Neo4jError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        driver.close()
        return 1

    failed = 0
    for idx, (label, stmt) in enumerate(statements, start=1):
        print(f"[{idx:02d}] {label}")
        try:
            keys, rows = _run_query(driver, stmt)
            _print_table(keys, rows)
        except Neo4jError as exc:
            print(f"  ERROR: {exc}", file=sys.stderr)
            failed += 1
        print()

    driver.close()
    if failed:
        print(f"QA completed with {failed} error(s).", file=sys.stderr)
        return 1
    print("QA done.")
    return 0


def main() -> int:
    """Entry point: --inspect flag → run_inspect, default → run_qa."""
    settings = QaSettings()
    if not settings.neo4j_password:
        print("ERROR: NEO4J_PASSWORD is not set", file=sys.stderr)
        return 1

    kwargs = {
        "uri": settings.neo4j_uri,
        "user": settings.neo4j_user,
        "password": settings.neo4j_password,
    }
    if "--inspect" in sys.argv:
        return run_inspect(**kwargs)
    return run_qa(**kwargs)


def run() -> NoReturn:
    raise SystemExit(main())


if __name__ == "__main__":
    run()
