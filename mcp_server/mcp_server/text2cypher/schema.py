"""Enhanced Neo4j schema and few-shot examples for Text2Cypher."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from neo4j_graphrag.schema import get_schema

from mcp_server.retriever.neo4j_driver import get_neo4j_ro_driver


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _few_shot_path() -> Path:
    return _repo_root() / "scripts" / "few_shot_examples.json"


def load_few_shot_examples() -> list[str]:
    """Load NL→Cypher pairs formatted for Text2CypherRetriever."""
    payload = json.loads(_few_shot_path().read_text(encoding="utf-8"))
    return [
        f"Q: {item['question']} A: {item['cypher']}"
        for item in payload
        if item.get("question") and item.get("cypher")
    ]


@lru_cache(maxsize=1)
def load_enhanced_schema() -> str:
    """Fetch enhanced schema from Neo4j (cached for process lifetime)."""
    driver = get_neo4j_ro_driver()
    return get_schema(
        driver,
        is_enhanced=True,
        sanitize=True,
        sample=100,
    )


def clear_enhanced_schema_cache() -> None:
    """Drop cached schema (tests)."""
    load_enhanced_schema.cache_clear()
