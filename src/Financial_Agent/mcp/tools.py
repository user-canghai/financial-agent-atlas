from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from Financial_Agent.tools.registry import get_all_native_tools

EXCLUDED = {"read_mcp_resource"}


def create_tools_server() -> FastMCP:
    server = FastMCP("Financial Native Tools")

    for tool_obj in get_all_native_tools():
        if tool_obj.name in EXCLUDED or tool_obj.func is None:
            continue
        server.tool(name=tool_obj.name, description=tool_obj.description)(tool_obj.func)

    return server


if __name__ == "__main__":
    create_tools_server().run()
