"""MCP stdio client for mcp_server subprocess."""

import asyncio
import json
import logging
from contextlib import AsyncExitStack
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import Tool

from app.core.config import Settings
from app.core.exceptions import McpUnavailableError

logger = logging.getLogger(__name__)

EXPECTED_TOOL_COUNT = 5


def _extract_text(content: list[Any]) -> str:
    texts: list[str] = []
    for block in content:
        text = getattr(block, "text", None)
        if text:
            texts.append(text)
    return "\n".join(texts)


class McpClient:
    """Async MCP client over stdio transport."""

    def __init__(self) -> None:
        self._stack: AsyncExitStack | None = None
        self._session: ClientSession | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    @property
    def is_connected(self) -> bool:
        return self._session is not None

    async def connect(self, settings: Settings) -> None:
        """Start mcp_server subprocess and initialize MCP session."""
        if self.is_connected:
            return

        server_params = StdioServerParameters(
            command="uv",
            args=["run", "python", "-m", "mcp_server"],
            cwd=str(settings.mcp_server_cwd),
            env=settings.mcp_subprocess_env(),
        )

        stack = AsyncExitStack()
        try:
            read, write = await stack.enter_async_context(stdio_client(server_params))
            session = await stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
        except Exception as exc:
            await stack.aclose()
            logger.exception("Failed to connect MCP subprocess")
            raise McpUnavailableError(str(exc)) from exc

        self._stack = stack
        self._session = session
        self._loop = asyncio.get_running_loop()
        logger.info("MCP client connected")

    async def close(self) -> None:
        """Shutdown MCP session and subprocess."""
        if self._stack is not None:
            await self._stack.aclose()
        self._stack = None
        self._session = None
        self._loop = None
        logger.info("MCP client disconnected")

    def call_tool_sync(self, name: str, arguments: dict[str, Any], *, timeout: float = 60.0) -> Any:
        """Call MCP tool from a worker thread (LangGraph sync tool node)."""
        if self._loop is None:
            raise McpUnavailableError("MCP client event loop is not available")
        future = asyncio.run_coroutine_threadsafe(
            self.call_tool(name, arguments),
            self._loop,
        )
        try:
            return future.result(timeout=timeout)
        except TimeoutError as exc:
            msg = f"Tool {name} timed out"
            raise McpUnavailableError(msg) from exc

    async def list_tools(self) -> list[Tool]:
        """Return tools exposed by MCP server."""
        session = self._require_session()
        result = await session.list_tools()
        return list(result.tools)

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        """Call MCP tool and parse JSON result."""
        session = self._require_session()
        try:
            result = await session.call_tool(name, arguments)
        except Exception as exc:
            logger.exception("MCP tool call failed: %s", name)
            msg = f"Tool {name} failed"
            raise McpUnavailableError(msg) from exc

        if result.isError:
            detail = _extract_text(result.content)
            raise McpUnavailableError(detail or f"Tool {name} returned error")

        text = _extract_text(result.content)
        if not text:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text

    def _require_session(self) -> ClientSession:
        if self._session is None:
            raise McpUnavailableError("MCP client is not connected")
        return self._session

    async def health_check(self) -> int:
        """Return number of available tools (0 if unavailable)."""
        try:
            tools = await self.list_tools()
        except McpUnavailableError:
            return 0
        return len(tools)
