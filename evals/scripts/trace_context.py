"""Fetch agent trace context from Langfuse for faithfulness / segment (E-3)."""

from __future__ import annotations

import json
import time
from typing import Any


def _text_from_observation(obs: Any) -> str | None:
    output = getattr(obs, "output", None)
    if output is None:
        return None
    if isinstance(output, str):
        return output.strip() or None
    if isinstance(output, dict):
        for key in ("content", "text", "result", "output"):
            value = output.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return json.dumps(output, ensure_ascii=False)
    return str(output)


def _audience_from_observation(obs: Any) -> str | None:
    input_data = getattr(obs, "input", None)
    if isinstance(input_data, dict):
        audience = input_data.get("audience") or input_data.get("args", {}).get("audience")
        if isinstance(audience, str):
            return audience
    if isinstance(input_data, str):
        try:
            parsed = json.loads(input_data)
        except json.JSONDecodeError:
            return None
        if isinstance(parsed, dict):
            audience = parsed.get("audience")
            if isinstance(audience, str):
                return audience
    return None


def fetch_agent_context(
    langfuse_client: Any,
    session_id: str,
    *,
    retries: int = 5,
    delay_s: float = 0.5,
) -> tuple[list[str], str | None]:
    """Return retrieval contexts and inferred segment from agent trace."""
    last_error: Exception | None = None
    for _ in range(retries):
        try:
            langfuse_client.flush()
            session = langfuse_client.api.sessions.get(session_id=session_id)
            traces = getattr(session, "traces", []) or []
            if not traces:
                time.sleep(delay_s)
                continue
            trace_id = traces[-1].id
            observations = langfuse_client.api.observations.get_many(
                trace_id=trace_id,
                limit=100,
            )
            contexts: list[str] = []
            segment: str | None = None
            for obs in observations.data:
                name = getattr(obs, "name", "") or ""
                obs_type = getattr(obs, "type", "") or ""
                if obs_type == "TOOL" or "search_knowledge_base" in name:
                    text = _text_from_observation(obs)
                    if text:
                        contexts.append(text)
                    audience = _audience_from_observation(obs)
                    if audience in ("b2c", "b2b"):
                        segment = audience
            if contexts or segment:
                return contexts, segment
        except Exception as exc:  # noqa: BLE001
            last_error = exc
        time.sleep(delay_s)
    if last_error is not None:
        return [], None
    return [], None
