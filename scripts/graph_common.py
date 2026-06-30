"""Shared helpers for graph indexing and comparison scripts."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from neo4j import Driver
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parent.parent
PROGRAMS_DIR = REPO_ROOT / "data" / "real_data" / "b2c" / "programs"

SEED_COURSE_IDS: frozenset[str] = frozenset(
    {"vibe-coding", "fullstack-aidd", "agents", "deep-agents"},
)

# Theme prerequisite edges from seed.cypher: (A)-[:REQUIRES]->(B) = «для A нужна B»
SEED_THEME_REQUIRES: tuple[tuple[str, str], ...] = (
    ("graphrag", "rag-basic"),
    ("graphrag", "vector-db"),
    ("graphrag", "graph-db"),
    ("rag-advanced", "rag-basic"),
    ("multimodal-rag", "rag-basic"),
    ("multimodal-rag", "multimodality"),
    ("multi-agent", "langchain-langgraph"),
    ("multi-agent", "tool-calling"),
    ("deep-agents-skills", "multi-agent"),
    ("hitl", "react-agent"),
    ("context-engineering", "mcp"),
    ("evaluation", "observability"),
)

# Part D: extra aliases for seed themes not matched by auto-extract (action: keep)
THEME_ALIAS_PATCHES: dict[str, tuple[str, ...]] = {
    "tool-calling": ("Tools", "tools", "Tool Use", "function tools"),
}

# Filename → canonical Course.id (None = combo / no single course)
FILE_TO_COURSE: dict[str, str | None] = {
    "ai-coding-intensive-cursor.md": "vibe-coding",
    "ai-driven-fullstack.md": "fullstack-aidd",
    "aidd-program.md": "fullstack-aidd",
    "ai-coding-agents-base.md": "agents",
    "deep-agents-advanced.md": "deep-agents",
    "ai-agents-combo.md": None,
}

# Manual alias → canonical Theme.id (supplements seed Theme.aliases)
THEME_ALIAS_OVERRIDES: dict[str, str] = {
    "rag": "rag-basic",
    "rag-система": "rag-basic",
    "rag pipeline": "rag-basic",
    "rag по базе знаний": "rag-basic",
    "retrieval-augmented generation": "rag-basic",
    "retrieval augmented generation": "rag-basic",
    "advanced rag": "rag-advanced",
    "self-rag": "rag-advanced",
    "agentic rag": "rag-advanced",
    "graphrag": "graphrag",
    "graph rag": "graphrag",
    "neo4j": "graph-db",
    "prompt engineering": "llm-api",
    "промпт-инжиниринг": "llm-api",
    "context engineering": "context-engineering",
    "контекст-инжиниринг": "context-engineering",
}

# Course slug/file aliases → canonical Course.id
COURSE_ALIAS_OVERRIDES: dict[str, str] = {
    "ai-driven-fullstack": "fullstack-aidd",
    "ai-coding-agents-base": "agents",
    "deep-agents-advanced": "deep-agents",
    "vibe-coding-intensive": "vibe-coding",
    "aidd-program": "fullstack-aidd",
    "fullstack ai-driven разработка": "fullstack-aidd",
    "fullstack aidd": "fullstack-aidd",
}

_SLUG_RE = re.compile(r"[^a-z0-9]+")


class GraphSettings(BaseSettings):
    """Neo4j + LLM settings for graph indexing scripts."""

    model_config = SettingsConfigDict(
        env_file=(str(REPO_ROOT / ".env"), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    neo4j_uri: str = Field(default="bolt://localhost:7687", alias="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", alias="NEO4J_USER")
    neo4j_password: str = Field(default="", alias="NEO4J_PASSWORD")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        alias="OPENAI_BASE_URL",
    )
    openai_model: str = Field(default="openai/gpt-4o-mini", alias="OPENAI_MODEL")
    embedding_model: str = Field(
        default="openai/text-embedding-3-small",
        alias="EMBEDDING_MODEL",
    )
    graph_extract_model: str = Field(default="", alias="GRAPH_EXTRACT_MODEL")
    graph_extract_strict: bool = Field(default=True, alias="GRAPH_EXTRACT_STRICT")

    @property
    def extract_model(self) -> str:
        return self.graph_extract_model or self.openai_model


def slugify(text: str) -> str:
    """Normalize text to URL-style slug (ASCII, lowercase, hyphen-separated)."""
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    slug = _SLUG_RE.sub("-", ascii_text.lower().strip())
    return slug.strip("-")


def normalize_key(text: str) -> str:
    return text.lower().strip()


def load_program_texts() -> dict[str, str]:
    """Read all program markdown files; key = filename."""
    texts: dict[str, str] = {}
    if not PROGRAMS_DIR.is_dir():
        return texts
    for path in sorted(PROGRAMS_DIR.glob("*.md")):
        texts[path.name] = path.read_text(encoding="utf-8")
    return texts


def load_seed_themes(driver: Driver) -> list[dict[str, object]]:
    """Load canonical seed themes from Neo4j."""
    records, _, _ = driver.execute_query(
        """
        MATCH (t:Theme {source: 'seed'})
        RETURN t.id AS id, t.name AS name, coalesce(t.aliases, []) AS aliases
        ORDER BY t.id
        """,
        database_="neo4j",
    )
    return [dict(rec) for rec in records]


def build_theme_alias_index(
    seed_themes: list[dict[str, object]],
) -> tuple[dict[str, str], frozenset[str]]:
    """Build lowercase alias → canonical Theme.id index."""
    canonical_ids: set[str] = set()
    index: dict[str, str] = {}

    for theme in seed_themes:
        theme_id = str(theme["id"])
        canonical_ids.add(theme_id)
        index[normalize_key(theme_id)] = theme_id
        name = theme.get("name")
        if name:
            index[normalize_key(str(name))] = theme_id
            slug = slugify(str(name))
            if slug:
                index[normalize_key(slug)] = theme_id
        for alias in theme.get("aliases") or []:
            index[normalize_key(str(alias))] = theme_id
            alias_slug = slugify(str(alias))
            if alias_slug:
                index[normalize_key(alias_slug)] = theme_id

    for alias, canon in THEME_ALIAS_OVERRIDES.items():
        index[normalize_key(alias)] = canon

    return index, frozenset(canonical_ids)


def exact_theme_id_match(
    *,
    name: str | None,
    node_id: str | None,
    canonical_ids: frozenset[str],
) -> str | None:
    """Match when raw LLM id/name equals a seed Theme.id (no alias dictionary)."""
    if node_id and node_id in canonical_ids:
        return node_id
    if node_id:
        slug = slugify(node_id)
        if slug in canonical_ids:
            return slug
    if name:
        slug = slugify(name)
        if slug in canonical_ids:
            return slug
    return None


def resolve_theme_id(
    *,
    name: str | None,
    node_id: str | None,
    alias_index: dict[str, str],
    canonical_ids: frozenset[str],
) -> str | None:
    """Map extracted theme name/id to canonical seed Theme.id."""
    candidates: list[str] = []
    if node_id:
        candidates.append(node_id)
    if name:
        candidates.append(name)
        candidates.append(slugify(name))

    for raw in candidates:
        key = normalize_key(raw)
        if key in alias_index:
            return alias_index[key]
        if raw in canonical_ids:
            return raw
        slug = slugify(raw)
        if slug in canonical_ids:
            return slug
        if normalize_key(slug) in alias_index:
            return alias_index[normalize_key(slug)]
    return None
