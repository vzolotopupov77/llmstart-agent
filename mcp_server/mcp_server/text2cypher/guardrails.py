"""Text2Cypher guardrails — regex write filter and LIMIT enforcement."""

from __future__ import annotations

import re

_WRITE_PATTERN = re.compile(
    r"\b(CREATE|MERGE|DELETE|DETACH|SET|REMOVE|DROP|FOREACH)\b",
    re.IGNORECASE,
)
_LOAD_CSV_PATTERN = re.compile(r"\bLOAD\s+CSV\b", re.IGNORECASE)
_LIMIT_PATTERN = re.compile(r"\bLIMIT\b", re.IGNORECASE)


class Text2CypherGuardrailError(Exception):
    """Raised when generated Cypher violates read-only guardrails."""


def validate_read_only_cypher(cypher: str) -> None:
    """Reject write/destructive Cypher before it reaches Neo4j."""
    if _WRITE_PATTERN.search(cypher) or _LOAD_CSV_PATTERN.search(cypher):
        preview = cypher.strip().replace("\n", " ")[:120]
        msg = f"write operation blocked: {preview}"
        raise Text2CypherGuardrailError(msg)


def ensure_limit(cypher: str, *, default: int = 25) -> str:
    """Append LIMIT when the query does not already contain one."""
    if _LIMIT_PATTERN.search(cypher):
        return cypher.strip()
    return f"{cypher.strip()}\nLIMIT {default}"
