"""Tests for Text2Cypher guardrails and guarded retriever."""

from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from neo4j_graphrag.exceptions import Text2CypherRetrievalError

from mcp_server.retriever.text2cypher import GuardedText2CypherRetriever
from mcp_server.server import text2cypher_tool
from mcp_server.text2cypher.guardrails import (
    Text2CypherGuardrailError,
    ensure_limit,
    validate_read_only_cypher,
)
from mcp_server.text2cypher.schema import load_few_shot_examples
from mcp_server.tools.text2cypher import TEXT2CYPHER_TOOL_DESCRIPTION


@pytest.mark.parametrize(
    "cypher",
    [
        "CREATE (n:Course {id: 'x'}) RETURN n",
        "MERGE (c:Course {id: 'x'}) RETURN c",
        "MATCH (n) DELETE n",
        "MATCH (n) DETACH DELETE n",
        "MATCH (n) SET n.title = 'hack' RETURN n",
        "MATCH (n) REMOVE n.title RETURN n",
        "DROP INDEX course_id_unique IF EXISTS",
        "FOREACH (x IN [1] | CREATE (n:Test))",
        "LOAD CSV FROM 'file:///tmp/x.csv' AS row CREATE (n:Test)",
    ],
)
def test_text2cypher_blocks_write(cypher: str) -> None:
    with pytest.raises(Text2CypherGuardrailError, match="write operation blocked"):
        validate_read_only_cypher(cypher)


def test_text2cypher_allows_read() -> None:
    validate_read_only_cypher(
        "MATCH (c:Course)-[:COVERS]->(t:Theme) RETURN c.id, t.id LIMIT 10",
    )


def test_text2cypher_adds_limit() -> None:
    query = "MATCH (c:Course) RETURN c.id, c.title"
    assert ensure_limit(query, default=25).endswith("LIMIT 25")


def test_text2cypher_preserves_existing_limit() -> None:
    query = "MATCH (c:Course) RETURN c.id LIMIT 10"
    assert ensure_limit(query, default=25) == query


def test_few_shot_examples_loaded() -> None:
    examples = load_few_shot_examples()
    assert len(examples) == 5
    assert examples[0].startswith("Q:")
    assert "A: MATCH" in examples[0]


def test_text2cypher_tool_description_scope() -> None:
    assert "structural" in TEXT2CYPHER_TOOL_DESCRIPTION.lower()
    assert "count" in TEXT2CYPHER_TOOL_DESCRIPTION.lower()
    assert "NOT for descriptions" in TEXT2CYPHER_TOOL_DESCRIPTION
    assert text2cypher_tool.__doc__ == TEXT2CYPHER_TOOL_DESCRIPTION


def _read_only_summary() -> MagicMock:
    summary = MagicMock()
    summary.query_type = "r"
    return summary


def _make_guarded_retriever(*, driver: MagicMock, llm: MagicMock) -> GuardedText2CypherRetriever:
    """Build retriever without SDK pydantic driver validation (unit tests)."""
    retriever = GuardedText2CypherRetriever.__new__(GuardedText2CypherRetriever)
    retriever.driver = driver
    retriever.llm = llm
    retriever.examples = []
    retriever.custom_prompt = None
    retriever.neo4j_schema = "Node labels: Course"
    retriever.neo4j_database = None
    retriever.result_formatter = None
    retriever._result_limit = 25
    retriever._query_timeout = timedelta(seconds=5.0)
    return retriever


def test_guarded_retriever_blocks_write_before_execute() -> None:
    driver = MagicMock()
    llm = MagicMock()
    llm.invoke.return_value = SimpleNamespace(
        content="CREATE (n:Course {id: 'x'}) RETURN n",
    )
    retriever = _make_guarded_retriever(driver=driver, llm=llm)

    with pytest.raises(Text2CypherGuardrailError):
        retriever.get_search_results("create a course")

    driver.execute_query.assert_not_called()


def test_guarded_retriever_adds_limit_before_explain() -> None:
    driver = MagicMock()
    driver.execute_query.side_effect = [
        ([], _read_only_summary(), None),
        ([], None, None),
    ]
    llm = MagicMock()
    llm.invoke.return_value = SimpleNamespace(
        content="MATCH (c:Course) RETURN count(c) AS total",
    )
    retriever = _make_guarded_retriever(driver=driver, llm=llm)

    result = retriever.get_search_results("how many courses")

    explain_call = driver.execute_query.call_args_list[0]
    assert "LIMIT 25" in explain_call.kwargs["query_"]
    assert result.metadata is not None
    assert result.metadata["cypher"].endswith("LIMIT 25")


def test_guarded_retriever_rejects_non_read_explain() -> None:
    driver = MagicMock()
    summary = MagicMock()
    summary.query_type = "w"
    driver.execute_query.return_value = ([], summary, None)
    llm = MagicMock()
    llm.invoke.return_value = SimpleNamespace(content="MATCH (c:Course) RETURN c LIMIT 5")
    retriever = _make_guarded_retriever(driver=driver, llm=llm)

    with pytest.raises(Text2CypherRetrievalError, match="non-read-only"):
        retriever.get_search_results("list courses")


def test_text2cypher_ro_blocks_create_via_guardrail() -> None:
    """RO path must reject CREATE before Neo4j (Community has no RBAC)."""
    with pytest.raises(Text2CypherGuardrailError):
        validate_read_only_cypher("CREATE (n:GuardrailTest {id: 't'}) RETURN n")
