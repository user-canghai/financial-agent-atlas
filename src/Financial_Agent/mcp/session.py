from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from langchain_mcp_adapters.client import MultiServerMCPClient

from Financial_Agent.mcp.mcp import get_enabled_servers


@asynccontextmanager
async def open_session(server_name: str) -> AsyncIterator[Any]:
    servers = get_enabled_servers()
    if server_name not in servers:
        raise ValueError(f"未启用 MCP 服务器: {server_name}")
    client = MultiServerMCPClient(servers)
    async with client.session(server_name) as session:
        yield session


__all__ = ["open_session"]
