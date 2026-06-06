"""POST /api/v1/chat endpoint."""

from fastapi import APIRouter, Header, HTTPException, Request, status
from fastapi.responses import StreamingResponse

from app.api.schemas.chat import ChatRequest, ChatResponse
from app.core.exceptions import (
    LlmUnavailableError,
    McpUnavailableError,
    SessionNotFoundError,
)
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
) -> ChatResponse | StreamingResponse:
    """Process one chat turn as JSON or SSE depending on Accept."""
    normalized_accept = accept.split(",", maxsplit=1)[0].strip().lower()
    agent_service: AgentService = request.app.state.agent_service

    if normalized_accept == "text/event-stream":
        return _chat_sse(agent_service, body)

    if normalized_accept != "application/json":
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="Only application/json or text/event-stream is supported",
        )

    return _chat_json(agent_service, body)


def _chat_json(agent_service: AgentService, body: ChatRequest) -> ChatResponse:
    try:
        return agent_service.run_chat_turn(
            message=body.message,
            session_id=body.session_id,
            channel=body.channel,
        )
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
        )
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
