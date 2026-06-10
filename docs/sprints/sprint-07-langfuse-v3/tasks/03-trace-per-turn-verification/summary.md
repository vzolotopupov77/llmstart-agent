# Summary: Task 03 — trace-per-turn-verification

- `backend/README.md`: E2E runbook trace за turn
- `test_chat_returns_200_when_langfuse_disabled` — регрессия
- `test_langfuse_live.py`: health, OTLP ≠ 404, SDK trace.list (`@pytest.mark.live`)
- `observability/langfuse.py` без изменений — SDK v3 совместим с server v3
