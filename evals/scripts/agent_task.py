"""HTTP task runner: Agent Core API for eval experiments (E-3/E-6)."""

from __future__ import annotations

import time
import uuid
from typing import Any
from urllib.parse import urlparse

import httpx
from app.agent.run_config import RunConfig

DEFAULT_TIMEOUT_S = 120.0


def extract_user_messages(item_input: str | list[dict[str, str]]) -> list[str]:
    """Replay only user turns from manifest input."""
    if isinstance(item_input, str):
        return [item_input.strip()]
    messages: list[str] = []
    for turn in item_input:
        if turn.get("role") == "user":
            content = turn.get("content", "").strip()
            if content:
                messages.append(content)
    return messages


def format_input_for_eval(item_input: str | list[dict[str, str]]) -> str:
    """Human-readable input string for judges."""
    if isinstance(item_input, str):
        return item_input
    parts: list[str] = []
    for turn in item_input:
        role = turn.get("role", "user")
        content = turn.get("content", "")
        parts.append(f"{role}: {content}")
    return "\n".join(parts)


def format_judge_input(item_input: str | list[dict[str, str]]) -> str:
    """Judge-facing input: emphasize the last user turn in multi-turn dialogs."""
    if isinstance(item_input, str):
        return item_input.strip()

    last_user_idx: int | None = None
    for idx, turn in enumerate(item_input):
        if turn.get("role") == "user":
            last_user_idx = idx

    if last_user_idx is None:
        return format_input_for_eval(item_input)

    prior = item_input[:last_user_idx]
    last_user = item_input[last_user_idx].get("content", "").strip()
    parts: list[str] = []
    if prior:
        parts.append("Контекст диалога (не оценивай ответ на старые реплики):")
        for turn in prior:
            role = turn.get("role", "user")
            content = turn.get("content", "")
            parts.append(f"{role}: {content}")
        parts.append("")
    parts.append("Последний запрос пользователя (оценивай ответ ТОЛЬКО на него):")
    parts.append(f"user: {last_user}")
    return "\n".join(parts)


class AgentTaskRunner:
    """Calls POST /api/v1/chat with config_id from run config."""

    def __init__(
        self,
        config: RunConfig,
        *,
        langfuse_client: Any | None = None,
        timeout_s: float = DEFAULT_TIMEOUT_S,
    ) -> None:
        self._config = config
        self._api_url = config.agent.api_url.rstrip("/")
        self._config_id = config.config_id
        self._langfuse = langfuse_client
        self._timeout = timeout_s

    def __call__(self, *, item: Any, **_: Any) -> dict[str, Any] | None:
        item_input = item.input if hasattr(item, "input") else item["input"]
        user_messages = extract_user_messages(item_input)
        if not user_messages:
            return None

        session_id: uuid.UUID | None = None
        last_response: dict[str, Any] | None = None

        for message in user_messages:
            last_response = self._post_chat(message=message, session_id=session_id)
            if last_response is None:
                return None
            session_id = uuid.UUID(str(last_response["session_id"]))

        if last_response is None:
            return None

        retrieval_context: list[str] = []
        segment: str | None = None
        if self._langfuse is not None and session_id is not None:
            from scripts.trace_context import fetch_agent_context

            retrieval_context, segment = fetch_agent_context(
                self._langfuse,
                str(session_id),
            )

        tool_names = {t.get("name") for t in last_response.get("tools", []) if isinstance(t, dict)}
        if segment is None and tool_names.intersection(
            {"create_payment_link", "list_b2c_products", "search_knowledge_base"}
        ):
            segment = "b2c"

        return {
            "message": last_response.get("message", ""),
            "message_html": last_response.get("message_html", ""),
            "reasoning": last_response.get("reasoning", ""),
            "session_id": str(session_id) if session_id else None,
            "tools": last_response.get("tools", []),
            "segment": segment,
            "retrieval_context": retrieval_context,
            "input_text": format_input_for_eval(item_input),
        }

    def _post_chat(
        self,
        *,
        message: str,
        session_id: uuid.UUID | None,
    ) -> dict[str, Any] | None:
        payload: dict[str, Any] = {
            "message": message,
            "channel": "web",
            "config_id": self._config_id,
        }
        if session_id is not None:
            payload["session_id"] = str(session_id)

        for attempt in range(2):
            try:
                with httpx.Client(timeout=self._timeout) as client:
                    response = client.post(
                        self._api_url,
                        json=payload,
                        headers={"Accept": "application/json"},
                    )
                if response.status_code == 503 and attempt == 0:
                    time.sleep(2.0)
                    continue
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError:
                if attempt == 1:
                    return None
                time.sleep(2.0)
        return None


def check_backend_health(api_url: str) -> None:
    """Fail-fast if Agent Core is unreachable."""
    parsed = urlparse(api_url)
    health_url = f"{parsed.scheme}://{parsed.netloc}/health"
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(health_url)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        msg = f"Backend not reachable at {health_url}: {exc}"
        raise RuntimeError(msg) from exc
