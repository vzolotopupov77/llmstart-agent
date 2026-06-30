"""MCP server configuration."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_data_dir() -> Path:
    """Resolve repo `data/` from package location unless overridden."""
    repo_root = Path(__file__).resolve().parents[2]
    return repo_root / "data"


class Settings(BaseSettings):
    """Runtime settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    data_dir: Path = Field(default_factory=_default_data_dir, alias="DATA_DIR")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        alias="OPENAI_BASE_URL",
    )
    openai_timeout_seconds: float = Field(default=120.0, alias="OPENAI_TIMEOUT_SECONDS")
    embedding_model: str = Field(
        default="openai/text-embedding-3-small",
        alias="EMBEDDING_MODEL",
    )
    rag_top_k: int = Field(default=4, alias="RAG_TOP_K")
    chunk_size: int = Field(default=800, alias="RAG_CHUNK_SIZE")
    chunk_overlap: int = Field(default=100, alias="RAG_CHUNK_OVERLAP")
    qdrant_url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")
    qdrant_collection: str = Field(default="knowledge_base", alias="QDRANT_COLLECTION")
    qdrant_api_key: str | None = Field(default=None, alias="QDRANT_API_KEY")
    embedding_dim: int = Field(default=1536, alias="EMBEDDING_DIM")
    retriever_backend: str = Field(default="qdrant", alias="RETRIEVER_BACKEND")
    retriever_branch: str = Field(default="vector", alias="RETRIEVER_BRANCH")
    neo4j_uri: str = Field(default="bolt://localhost:7687", alias="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", alias="NEO4J_USER")
    neo4j_password: str = Field(default="", alias="NEO4J_PASSWORD")
    neo4j_ro_user: str = Field(default="text2cypher_ro", alias="NEO4J_RO_USER")
    neo4j_ro_password: str = Field(default="", alias="NEO4J_RO_PASSWORD")
    text2cypher_model: str = Field(default="openai/gpt-4o-mini", alias="TEXT2CYPHER_MODEL")
    text2cypher_result_limit: int = Field(default=25, alias="TEXT2CYPHER_RESULT_LIMIT")
    text2cypher_query_timeout_seconds: float = Field(
        default=5.0,
        alias="TEXT2CYPHER_QUERY_TIMEOUT_SECONDS",
    )
    reranker_model: str = Field(
        default="BAAI/bge-reranker-v2-m3",
        alias="RERANKER_MODEL",
    )
    reranker_enabled: bool = Field(default=True, alias="RERANKER_ENABLED")
    rrf_k: int = Field(default=60, alias="RRF_K")
    graph_expand_hops: int = Field(default=2, alias="GRAPH_EXPAND_HOPS")
    pgvector_host: str = Field(default="localhost", alias="PGVECTOR_HOST")
    pgvector_port: int = Field(default=5434, alias="PGVECTOR_PORT")
    pgvector_db: str = Field(default="knowledge_base", alias="PGVECTOR_DB")
    pgvector_user: str = Field(default="pgvector", alias="PGVECTOR_USER")
    pgvector_password: str = Field(default="pgvector", alias="PGVECTOR_PASSWORD")
    pgvector_table: str = Field(default="knowledge_chunks", alias="PGVECTOR_TABLE")

    @property
    def pgvector_conninfo(self) -> str:
        """PostgreSQL connection string for pgvector."""
        return (
            f"host={self.pgvector_host} port={self.pgvector_port} "
            f"dbname={self.pgvector_db} user={self.pgvector_user} "
            f"password={self.pgvector_password}"
        )

    @field_validator("data_dir", mode="before")
    @classmethod
    def normalize_data_dir(cls, value: object) -> Path:
        """Treat empty DATA_DIR as repo default."""
        if value in ("", None):
            return _default_data_dir()
        return Path(str(value))


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()


settings = get_settings()
