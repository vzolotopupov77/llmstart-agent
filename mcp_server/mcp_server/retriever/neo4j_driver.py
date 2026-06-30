"""Neo4j driver lifecycle for graph retrievers."""

from functools import lru_cache

from neo4j import Driver, GraphDatabase
from neo4j.exceptions import Neo4jError, ServiceUnavailable

from mcp_server.config import get_settings
from mcp_server.retriever.base import GraphNotReadyError

_GRAPH_EMPTY_MSG = "graph is empty; run make graph-index first"
_GRAPH_CONN_MSG = "neo4j is not reachable; run make graph-up && make graph-index"
_RO_CONN_MSG = "neo4j RO user is not configured; set NEO4J_RO_PASSWORD and run make graph-init-ro"


@lru_cache
def get_neo4j_driver() -> Driver:
    """Return cached Neo4j driver; fails fast if password missing."""
    settings = get_settings()
    if not settings.neo4j_password:
        raise GraphNotReadyError(_GRAPH_CONN_MSG)
    driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )
    try:
        driver.verify_connectivity()
    except (ServiceUnavailable, Neo4jError) as exc:
        driver.close()
        raise GraphNotReadyError(_GRAPH_CONN_MSG) from exc
    return driver


def ensure_graph_ready(driver: Driver) -> None:
    """Verify graph has at least one Course node."""
    try:
        records, _, _ = driver.execute_query(
            "MATCH (c:Course) RETURN count(c) AS n LIMIT 1",
            database_="neo4j",
        )
    except (ServiceUnavailable, Neo4jError) as exc:
        raise GraphNotReadyError(_GRAPH_CONN_MSG) from exc
    count = int(records[0]["n"]) if records else 0
    if count == 0:
        raise GraphNotReadyError(_GRAPH_EMPTY_MSG)


@lru_cache
def get_neo4j_ro_driver() -> Driver:
    """Return cached Neo4j driver for text2cypher read-only user."""
    settings = get_settings()
    if not settings.neo4j_ro_password:
        raise GraphNotReadyError(_RO_CONN_MSG)
    driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_ro_user, settings.neo4j_ro_password),
    )
    try:
        driver.verify_connectivity()
    except (ServiceUnavailable, Neo4jError) as exc:
        driver.close()
        raise GraphNotReadyError(_GRAPH_CONN_MSG) from exc
    return driver


def clear_neo4j_driver_cache() -> None:
    """Close and drop cached driver (tests)."""
    if get_neo4j_driver.cache_info().currsize:
        get_neo4j_driver().close()
    get_neo4j_driver.cache_clear()
    if get_neo4j_ro_driver.cache_info().currsize:
        get_neo4j_ro_driver().close()
    get_neo4j_ro_driver.cache_clear()
