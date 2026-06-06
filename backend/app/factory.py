"""FastAPI application factory."""

import asyncio
import logging
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.tools import BaseTool

from app.agent.react_runner import ReactRunner
from app.api.routes.chat import router as chat_router
from app.api.routes.health import router as health_router
from app.api.routes.products import router as products_router
from app.api.routes.ready import router as ready_router
from app.core.config import get_settings
from app.mcp_client.client import McpClient
from app.mcp_client.runtime import apply_mcp_server_env, ensure_rag_index
from app.mcp_client.tool_adapter import build_langchain_tools
from app.mcp_client.tool_registry import get_tool_definitions
from app.observability.langfuse import init_langfuse, shutdown_langfuse
from app.services.agent_service import AgentService
from app.services.catalog_service import CatalogService
from app.services.session_store import SessionStore

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup: RAG index + agent; shutdown: cleanup."""
    settings = get_settings()
    if not settings.openai_api_key:
        msg = "OPENAI_API_KEY is required"
        raise RuntimeError(msg)

    init_langfuse(settings)

    mcp_client: McpClient | None = app.state.injected_mcp_client
    tools_ready = False

    if mcp_client is None:
        apply_mcp_server_env(settings)
        await asyncio.to_thread(ensure_rag_index)
        tool_defs = get_tool_definitions()
        tools_ready = True
        logger.info("MCP tools ready (in-process handlers)")
    else:
        logger.info("Using injected MCP client (test mode)")
        tool_defs = await mcp_client.list_tools()
        tools_ready = mcp_client.is_connected

    langchain_tools = build_langchain_tools(tool_defs)
    langchain_tool_list: Sequence[BaseTool] = langchain_tools
    react_runner = app.state.injected_react_runner or ReactRunner(
        settings,
        list(langchain_tool_list),
    )
    session_store = SessionStore(ttl_hours=settings.session_ttl_hours)
    agent_service = AgentService(
        session_store=session_store,
        react_runner=react_runner,
        tools_ready=tools_ready,
        settings=settings,
    )

    catalog_service = CatalogService()

    app.state.mcp_client = mcp_client
    app.state.tools_ready = tools_ready
    app.state.agent_service = agent_service
    app.state.session_store = session_store
    app.state.catalog_service = catalog_service

    yield

    shutdown_langfuse()

    if mcp_client is not None and app.state.injected_mcp_client is None:
        await mcp_client.close()


def create_app(
    *,
    mcp_client: McpClient | None = None,
    react_runner: ReactRunner | None = None,
) -> FastAPI:
    """Build FastAPI app; optional injections for tests."""
    app = FastAPI(
        title="LLMStart Agent Core",
        version=get_settings().app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.state.injected_mcp_client = mcp_client
    app.state.injected_react_runner = react_runner

    settings = get_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Accept"],
    )

    app.include_router(health_router)
    app.include_router(ready_router)
    app.include_router(chat_router)
    app.include_router(products_router)

    return app
