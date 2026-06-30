"""Create read-only Neo4j user for text2cypher (idempotent)."""

import sys

from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Neo4jInitSettings(BaseSettings):
    """Admin and RO credentials from environment or repo-root .env."""

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    neo4j_uri: str = Field(default="bolt://localhost:7687", alias="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", alias="NEO4J_USER")
    neo4j_password: str = Field(default="", alias="NEO4J_PASSWORD")
    neo4j_ro_user: str = Field(default="text2cypher_ro", alias="NEO4J_RO_USER")
    neo4j_ro_password: str = Field(default="", alias="NEO4J_RO_PASSWORD")


def init_text2cypher_ro_user(
    *,
    uri: str | None = None,
    admin_user: str | None = None,
    admin_password: str | None = None,
    ro_user: str | None = None,
    ro_password: str | None = None,
) -> None:
    """Create RO user and grant reader role if missing."""
    settings = Neo4jInitSettings()
    resolved_uri = uri if uri is not None else settings.neo4j_uri
    resolved_admin_user = admin_user if admin_user is not None else settings.neo4j_user
    resolved_admin_password = (
        admin_password if admin_password is not None else settings.neo4j_password
    )
    resolved_ro_user = ro_user if ro_user is not None else settings.neo4j_ro_user
    resolved_ro_password = ro_password if ro_password is not None else settings.neo4j_ro_password

    if not resolved_admin_password:
        msg = "NEO4J_PASSWORD is not set"
        raise ValueError(msg)
    if not resolved_ro_password:
        msg = "NEO4J_RO_PASSWORD is not set"
        raise ValueError(msg)

    driver = GraphDatabase.driver(
        resolved_uri,
        auth=(resolved_admin_user, resolved_admin_password),
    )
    try:
        with driver.session() as session:
            session.run(
                "CREATE USER $name IF NOT EXISTS SET PASSWORD $password CHANGE NOT REQUIRED",
                name=resolved_ro_user,
                password=resolved_ro_password,
            )
            try:
                session.run(
                    "GRANT ROLE reader TO $name",
                    name=resolved_ro_user,
                )
            except Neo4jError as exc:
                if exc.code != "Neo.ClientError.Statement.UnsupportedAdministrationCommand":
                    raise
                print(
                    "Note: GRANT ROLE is Enterprise-only; "
                    "Community uses separate credentials + app guardrails (Task 07).",
                    file=sys.stderr,
                )
    finally:
        driver.close()


def main() -> int:
    """Create text2cypher_ro user."""
    try:
        init_text2cypher_ro_user()
    except (Neo4jError, ValueError, OSError) as exc:
        print(f"Init failed: {exc}", file=sys.stderr)
        return 1
    print(f"RO user ready: {Neo4jInitSettings().neo4j_ro_user}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
