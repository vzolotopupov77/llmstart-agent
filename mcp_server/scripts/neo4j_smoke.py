"""Neo4j connectivity smoke check for make graph-status."""

import sys
from typing import NoReturn

from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Neo4jSmokeSettings(BaseSettings):
    """Load Neo4j credentials from environment or repo-root .env."""

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    neo4j_uri: str = Field(default="bolt://localhost:7687", alias="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", alias="NEO4J_USER")
    neo4j_password: str = Field(default="", alias="NEO4J_PASSWORD")


def verify_neo4j_connectivity(
    *,
    uri: str | None = None,
    user: str | None = None,
    password: str | None = None,
) -> None:
    """Verify Bolt connectivity using driver.verify_connectivity()."""
    settings = Neo4jSmokeSettings()
    resolved_uri = uri if uri is not None else settings.neo4j_uri
    resolved_user = user if user is not None else settings.neo4j_user
    resolved_password = password if password is not None else settings.neo4j_password
    if not resolved_password:
        msg = "NEO4J_PASSWORD is not set"
        raise ValueError(msg)

    driver = GraphDatabase.driver(
        resolved_uri,
        auth=(resolved_user, resolved_password),
    )
    try:
        driver.verify_connectivity()
    finally:
        driver.close()


def main() -> int:
    """Print Connection OK on success, non-zero exit on failure."""
    try:
        verify_neo4j_connectivity()
    except (Neo4jError, ValueError, OSError) as exc:
        print(f"Connection failed: {exc}", file=sys.stderr)
        return 1
    print("Connection OK")
    return 0


def run() -> NoReturn:
    """CLI entrypoint."""
    raise SystemExit(main())


if __name__ == "__main__":
    run()
