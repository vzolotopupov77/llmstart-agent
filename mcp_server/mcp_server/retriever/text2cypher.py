"""Text2Cypher retrieval with application-layer guardrails."""

from __future__ import annotations

from datetime import timedelta
from functools import lru_cache
from typing import Any

import neo4j
from neo4j.exceptions import CypherSyntaxError, Neo4jError
from neo4j_graphrag.exceptions import SearchValidationError, Text2CypherRetrievalError
from neo4j_graphrag.generation.prompts import Text2CypherTemplate
from neo4j_graphrag.llm import LLMInterface, OpenAILLM
from neo4j_graphrag.retrievers import Text2CypherRetriever
from neo4j_graphrag.retrievers.text2cypher import READ_ONLY_QUERY_TYPE, extract_cypher
from neo4j_graphrag.types import RawSearchResult, Text2CypherSearchModel
from pydantic import ValidationError

from mcp_server.config import Settings, get_settings
from mcp_server.retriever.base import GraphNotReadyError, KnowledgeChunk, Segment
from mcp_server.retriever.neo4j_driver import ensure_graph_ready, get_neo4j_ro_driver
from mcp_server.text2cypher.guardrails import (
    Text2CypherGuardrailError,
    ensure_limit,
    validate_read_only_cypher,
)
from mcp_server.text2cypher.schema import load_enhanced_schema, load_few_shot_examples

_RO_CONFIG_MSG = "NEO4J_RO_PASSWORD is not set; run make graph-init-ro"
_TIMEOUT_MSG = "text2cypher query timed out"


class GuardedText2CypherRetriever(Text2CypherRetriever):
    """Text2CypherRetriever with regex, LIMIT, and query timeout guardrails."""

    def __init__(
        self,
        *,
        driver: neo4j.Driver,
        llm: LLMInterface,
        neo4j_schema: str | None,
        examples: list[str] | None,
        result_limit: int,
        query_timeout_seconds: float,
        neo4j_database: str | None = None,
    ) -> None:
        super().__init__(
            driver=driver,
            llm=llm,
            neo4j_schema=neo4j_schema,
            examples=examples,
            neo4j_database=neo4j_database,
        )
        self._result_limit = result_limit
        self._query_timeout = timedelta(seconds=query_timeout_seconds)

    def get_search_results(
        self,
        query_text: str,
        prompt_params: dict[str, Any] | None = None,
    ) -> RawSearchResult:
        try:
            validated_data = Text2CypherSearchModel(query_text=query_text)
        except ValidationError as exc:
            raise SearchValidationError(exc.errors()) from exc

        prompt_template = Text2CypherTemplate(template=self.custom_prompt)
        params = dict(prompt_params or {})
        examples_to_use = params.pop("examples", None) or (
            "\n".join(self.examples) if self.examples else ""
        )
        schema_to_use = params.pop("schema", None) or self.neo4j_schema

        prompt = prompt_template.format(
            schema=schema_to_use,
            examples=examples_to_use,
            query_text=validated_data.query_text,
            **params,
        )

        try:
            llm_result = self.llm.invoke(prompt)
            t2c_query = extract_cypher(llm_result.content)
            validate_read_only_cypher(t2c_query)
            t2c_query = ensure_limit(t2c_query, default=self._result_limit)

            _, explain_summary, _ = self.driver.execute_query(
                query_=f"EXPLAIN {t2c_query}",
                database_=self.neo4j_database,
                routing_=neo4j.RoutingControl.READ,
                timeout=self._query_timeout,
            )
            if explain_summary.query_type != READ_ONLY_QUERY_TYPE:
                msg = (
                    "Refusing to execute non-read-only Cypher "
                    f"(query_type={explain_summary.query_type!r}): {t2c_query}"
                )
                raise Text2CypherRetrievalError(msg)

            records, _, _ = self.driver.execute_query(
                query_=t2c_query,
                database_=self.neo4j_database,
                routing_=neo4j.RoutingControl.READ,
                timeout=self._query_timeout,
            )
        except Text2CypherGuardrailError:
            raise
        except CypherSyntaxError as exc:
            syntax_msg = f"Failed to get search result: {exc.message}"
            raise Text2CypherRetrievalError(syntax_msg) from exc
        except Neo4jError as exc:
            if "timeout" in str(exc).lower():
                raise Text2CypherRetrievalError(_TIMEOUT_MSG) from exc
            raise

        return RawSearchResult(
            records=records,
            metadata={"cypher": t2c_query},
        )

    def search_catalog(
        self,
        query: str,
        segment: Segment,
        *,
        top_k: int,
    ) -> list[KnowledgeChunk]:
        result = self.search(query_text=query)
        metadata = result.metadata or {}
        cypher = str(metadata.get("cypher", ""))
        rows = result.items[:top_k]
        header = f"[text2cypher] segment={segment} | cypher={cypher} | rows={len(rows)}"
        if not rows:
            return [
                {
                    "text": f"{header}\n(no rows)",
                    "source": "neo4j/text2cypher",
                    "segment": segment,
                    "branch": "text2cypher",
                    "entity_id": "text2cypher-empty",
                },
            ]

        body = "\n".join(f"row: {item.content}" for item in rows)
        return [
            {
                "text": f"{header}\n{body}",
                "source": "neo4j/text2cypher",
                "segment": segment,
                "branch": "text2cypher",
                "entity_id": "text2cypher-result",
            },
        ]


def _build_llm(settings: Settings) -> OpenAILLM:
    return OpenAILLM(
        model_name=settings.text2cypher_model,
        model_params={"temperature": 0},
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
    )


@lru_cache
def get_text2cypher_retriever() -> GuardedText2CypherRetriever:
    """Return cached guarded Text2Cypher retriever using RO credentials."""
    settings = get_settings()
    if not settings.neo4j_ro_password:
        raise GraphNotReadyError(_RO_CONFIG_MSG)
    driver = get_neo4j_ro_driver()
    ensure_graph_ready(driver)
    return GuardedText2CypherRetriever(
        driver=driver,
        llm=_build_llm(settings),
        neo4j_schema=load_enhanced_schema(),
        examples=load_few_shot_examples(),
        result_limit=settings.text2cypher_result_limit,
        query_timeout_seconds=settings.text2cypher_query_timeout_seconds,
    )


def clear_text2cypher_retriever_cache() -> None:
    """Drop cached retriever (tests)."""
    get_text2cypher_retriever.cache_clear()
