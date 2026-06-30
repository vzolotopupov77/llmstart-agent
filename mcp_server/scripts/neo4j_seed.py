"""Execute scripts/seed.cypher against Neo4j via the Python driver.

Usage:
    cd mcp_server && uv run python -m scripts.neo4j_seed

The script reads <repo_root>/scripts/seed.cypher, splits it into individual
Cypher statements (semicolon-delimited), strips comment-only blocks, and
executes each statement via driver.execute_query().

Idempotent: safe to run multiple times (seed uses MERGE + IF NOT EXISTS).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import NoReturn

from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SeedSettings(BaseSettings):
    """Neo4j connection settings loaded from .env."""

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    neo4j_uri: str = Field(default="bolt://localhost:7687", alias="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", alias="NEO4J_USER")
    neo4j_password: str = Field(default="", alias="NEO4J_PASSWORD")


# Seed file is two levels up from mcp_server/scripts/
_SEED_FILE = Path(__file__).parent.parent.parent / "scripts" / "seed.cypher"

_COMMENT_LINE = re.compile(r"^\s*//")


def _parse_statements(cypher: str) -> list[str]:
    """Split cypher text into individual statements, dropping comment lines.

    Comments are stripped BEFORE splitting on ';' so that semicolons inside
    comment text (e.g. ``// a; b``) don't produce spurious empty statements.
    """
    # Remove comment lines from the whole file first
    clean_lines = [
        line for line in cypher.splitlines() if not _COMMENT_LINE.match(line)
    ]
    cleaned = "\n".join(clean_lines)
    return [stmt.strip() for stmt in cleaned.split(";") if stmt.strip()]


def run_seed(*, uri: str, user: str, password: str) -> int:
    """Read and execute seed.cypher. Returns exit code."""
    if not _SEED_FILE.exists():
        print(f"ERROR: seed file not found: {_SEED_FILE}", file=sys.stderr)
        return 1

    cypher = _SEED_FILE.read_text(encoding="utf-8")
    statements = _parse_statements(cypher)
    print(f"Parsed {len(statements)} statements from {_SEED_FILE.name}")

    driver = GraphDatabase.driver(uri, auth=(user, password))
    try:
        driver.verify_connectivity()
    except (Neo4jError, OSError) as exc:
        print(f"ERROR: cannot connect to Neo4j: {exc}", file=sys.stderr)
        driver.close()
        return 1

    errors: list[tuple[int, str, str]] = []
    for idx, stmt in enumerate(statements, start=1):
        # First line of statement for progress display (truncated)
        first_line = stmt.splitlines()[0][:80] if stmt else ""
        try:
            driver.execute_query(stmt, database_="neo4j")
            print(f"  [{idx:02d}/{len(statements)}] OK  {first_line}")
        except Neo4jError as exc:
            print(f"  [{idx:02d}/{len(statements)}] ERR {first_line}", file=sys.stderr)
            print(f"         {exc}", file=sys.stderr)
            errors.append((idx, first_line, str(exc)))

    driver.close()

    if errors:
        print(f"\nSeed completed with {len(errors)} error(s):", file=sys.stderr)
        for idx, line, msg in errors:
            print(f"  stmt {idx}: {line!r} → {msg}", file=sys.stderr)
        return 1

    print(f"\nSeed OK — {len(statements)} statements executed successfully.")
    return 0


def main() -> int:
    settings = SeedSettings()
    if not settings.neo4j_password:
        print("ERROR: NEO4J_PASSWORD is not set", file=sys.stderr)
        return 1
    return run_seed(
        uri=settings.neo4j_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password,
    )


def run() -> NoReturn:
    raise SystemExit(main())


if __name__ == "__main__":
    run()
