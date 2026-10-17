from __future__ import annotations

from mcp.server.fastmcp import FastMCP


def build_server(name: str, instructions: str | None = None) -> FastMCP:
    return FastMCP(name, instructions=instructions)


__all__ = ["build_server"]
