"""Launch interactive cypher-shell via docker compose (cross-platform)."""

import subprocess
import sys
from pathlib import Path

from scripts.neo4j_smoke import Neo4jSmokeSettings


def main() -> int:
    """Open cypher-shell in the neo4j container."""
    settings = Neo4jSmokeSettings()
    if not settings.neo4j_password:
        print("NEO4J_PASSWORD is not set", file=sys.stderr)
        return 1

    repo_root = Path(__file__).resolve().parents[2]
    compose_file = repo_root / "devops" / "docker-compose.yml"
    env_file = repo_root / ".env"

    cmd = [
        "docker",
        "compose",
        "--env-file",
        str(env_file),
        "-f",
        str(compose_file),
        "exec",
        "neo4j",
        "cypher-shell",
        "-a",
        "bolt://localhost:7687",
        "-u",
        settings.neo4j_user,
        "-p",
        settings.neo4j_password,
    ]
    try:
        return subprocess.call(cmd)
    except OSError as exc:
        print(f"Failed to start cypher-shell: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
