from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def get_mcp_tools() -> list[Any]:
    from Financial_Agent.mcp.manager import get_manager

    return get_manager().get_tools_sync()


def clear_mcp_tools_cache() -> None:
    from Financial_Agent.mcp.manager import get_manager

    get_manager().clear_cache()


class _MCPToolsSequence:
    def __iter__(self):
        return iter(get_mcp_tools())

    def __len__(self) -> int:
        return len(get_mcp_tools())

    def __getitem__(self, index):
        return get_mcp_tools()[index]

    def __repr__(self) -> str:
        return repr(get_mcp_tools())


MCP_TOOLS = _MCPToolsSequence()

__all__ = ["MCP_TOOLS", "get_mcp_tools", "clear_mcp_tools_cache"]
