"""Smoke test for Neo4j connectivity."""

import pytest

from scripts.neo4j_smoke import Neo4jSmokeSettings, verify_neo4j_connectivity


@pytest.mark.skipif(
    not Neo4jSmokeSettings().neo4j_password,
    reason="NEO4J_PASSWORD not set — skip without local Neo4j",
)
def test_neo4j_verify_connectivity() -> None:
    """driver.verify_connectivity() succeeds when Neo4j is up."""
    verify_neo4j_connectivity()
