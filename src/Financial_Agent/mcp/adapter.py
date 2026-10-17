from __future__ import annotations

from typing import Any

from Financial_Agent.mcp.manager import get_manager


def parse_tool_name(tool_name: str, server_names: set[str]) -> tuple[str, str]:
    if not tool_name:
        return "未知服务器", ""
    parts = tool_name.split("_")
    for index in range(len(parts) - 1, 0, -1):
        candidate = "_".join(parts[:index])
        if candidate in server_names:
            return candidate, "_".join(parts[index:])
    return "未知服务器", tool_name


def load_tools(server_name: str | None = None) -> list[Any]:
    return get_manager().get_tools_sync(server_name)


def read_resource(server_name: str, resource_uri: str) -> str:
    return get_manager().read_resource_sync(server_name, resource_uri)


__all__ = ["parse_tool_name", "load_tools", "read_resource"]
