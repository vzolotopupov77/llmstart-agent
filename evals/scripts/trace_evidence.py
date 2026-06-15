"""Fetch agent trace span summary for analyze report evidence."""

from __future__ import annotations

from typing import Any


def fetch_agent_trace_spans(langfuse_client: Any, session_id: str) -> list[str]:
    """Return human-readable span lines from agent session trace."""
    try:
        langfuse_client.flush()
        session = langfuse_client.api.sessions.get(session_id=session_id)
        traces = getattr(session, "traces", []) or []
        if not traces:
            return ["(agent trace не найден по session_id)"]
        trace_id = traces[-1].id
        observations = langfuse_client.api.observations.get_many(trace_id=trace_id, limit=50)
        lines: list[str] = []
        for obs in observations.data:
            name = getattr(obs, "name", "") or getattr(obs, "type", "obs")
            obs_type = getattr(obs, "type", "")
            lines.append(f"- `{obs_type}` **{name}**")
        if not lines:
            return [f"(trace `{trace_id}` без observations)"]
        return [f"Agent trace `{trace_id}`:"] + lines[:8]
    except Exception as exc:  # noqa: BLE001
        return [f"(Langfuse span fetch failed: {exc})"]


def trace_ui_url(host: str, project_id: str, trace_id: str) -> str:
    base = host.rstrip("/")
    return f"{base}/project/{project_id}/trace/{trace_id}"


def experiment_trace_ui_url(host: str, project_id: str, trace_id: str) -> str:
    return trace_ui_url(host, project_id, trace_id)
