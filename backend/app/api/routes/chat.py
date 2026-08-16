"""POST /api/v1/chat endpoint."""

from fastapi import APIRouter, Header, HTTPException, Request, status
from fastapi.responses import StreamingResponse

from app.api.schemas.chat import ChatRequest, ChatResponse
from app.core.exceptions import (
    ConfigNotFoundError,
    LlmUnavailableError,
    McpUnavailableError,
    SessionNotFoundError,
)
from app.security.config_gate import config_id_is_authorized
from app.security.constants import EVAL_ACCESS_KEY_HEADER
from app.security.input_guard import input_should_block
from app.services.agent_service import AgentService

router = APIRouter(prefix="/api/v1", tags=["chat"])

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
}


@router.post(
    "/chat",
    response_model=None,
    responses={
        200: {
            "description": "JSON chat response or SSE event stream depending on Accept header.",
            "content": {
                "application/json": {},
                "text/event-stream": {
                    "example": (
                        'event: reasoning\ndata: {"text": "..."}\n\n'
                        'event: done\ndata: {"session_id": "...", "message": "..."}\n\n'
                    ),
                },
            },
        },
    },
)
def chat(
    body: ChatRequest,
    request: Request,
    accept: str = Header(default="application/json"),
    eval_access_key: str | None = Header(default=None, alias=EVAL_ACCESS_KEY_HEADER),
) -> ChatResponse | StreamingResponse:
    """Process one chat turn as JSON or SSE depending on Accept."""
    normalized_accept = accept.split(",", maxsplit=1)[0].strip().lower()
    agent_service: AgentService = request.app.state.agent_service
    settings = agent_service.settings
    wants_sse = normalized_accept == "text/event-stream"

    if normalized_accept not in {"application/json", "text/event-stream"}:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="Only application/json or text/event-stream is supported",
        )

    if input_should_block(body.message, security_enabled=settings.security_enabled):
        return _blocked_response(agent_service, body, wants_sse=wants_sse)

    if not config_id_is_authorized(body.config_id, eval_access_key, settings):
        return _blocked_response(agent_service, body, wants_sse=wants_sse)

    if wants_sse:
        return _chat_sse(agent_service, body)

    return _chat_json(agent_service, body)


def _blocked_response(
    agent_service: AgentService,
    body: ChatRequest,
    *,
    wants_sse: bool,
) -> ChatResponse | StreamingResponse:
    try:
        if wants_sse:
            stream = agent_service.iter_blocked_stream(
                session_id=body.session_id,
                channel=body.channel,
            )
            return StreamingResponse(
                stream,
                media_type="text/event-stream",
                headers=SSE_HEADERS,
            )
        return agent_service.blocked_chat_response(
            session_id=body.session_id,
            channel=body.channel,
        )
    except SessionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session not found or expired",
        ) from exc


def _chat_json(agent_service: AgentService, body: ChatRequest) -> ChatResponse:
    try:
        return agent_service.run_chat_turn(
            message=body.message,
            session_id=body.session_id,
            channel=body.channel,
            config_id=body.config_id,
        )
    except ConfigNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except SessionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session not found or expired",
        ) from exc
    except McpUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Tools service unavailable",
        ) from exc
    except LlmUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM service unavailable",
        ) from exc


def _chat_sse(agent_service: AgentService, body: ChatRequest) -> StreamingResponse:
    try:
        stream = agent_service.iter_chat_turn_stream(
            message=body.message,
            session_id=body.session_id,
            channel=body.channel,
            config_id=body.config_id,
        )
    except ConfigNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except SessionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session not found or expired",
        ) from exc
    except McpUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Tools service unavailable",
        ) from exc
    except LlmUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM service unavailable",
        ) from exc

    return StreamingResponse(
        stream,
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )
