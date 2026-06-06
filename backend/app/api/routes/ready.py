"""GET /ready readiness endpoint."""

from fastapi import APIRouter, HTTPException, Request, status

from app.api.schemas.ready import ReadyResponse
from app.core.config import get_settings
from app.mcp_client.tool_registry import EXPECTED_TOOL_COUNT

router = APIRouter(tags=["health"])


@router.get("/ready", response_model=ReadyResponse)
async def ready(request: Request) -> ReadyResponse:
    """Readiness probe: tools layer and LLM config present."""
    settings = get_settings()
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM configuration missing",
        )

    tools_ready = getattr(request.app.state, "tools_ready", False)
    mcp_client = getattr(request.app.state, "mcp_client", None)

    if mcp_client is not None:
        tool_count = await mcp_client.health_check()
    elif tools_ready:
        tool_count = EXPECTED_TOOL_COUNT
    else:
        tool_count = 0

    if tool_count < EXPECTED_TOOL_COUNT:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MCP tools unavailable",
        )

    return ReadyResponse(status="ready", mcp_tools=tool_count)
