from __future__ import annotations

import os
import sys
from pathlib import Path

_SERVERS_DIR = Path(__file__).resolve().parent / "servers"

MCP_SERVERS_CONFIG: dict[str, dict[str, object]] = {
    "fetch": {
        "command": "uvx",
        "args": ["mcp-server-fetch"],
        "transport": "stdio",
    },
    "gold_server": {
        "command": sys.executable,
        "args": [str(_SERVERS_DIR / "gold_server.py")],
        "transport": "stdio",
    },
    "stock_server": {
        "command": sys.executable,
        "args": [str(_SERVERS_DIR / "stock_server.py")],
        "transport": "stdio",
    },
    "worldbank": {
        "command": "npx",
        "args": ["-y", "worldbank-mcp"],
        "transport": "stdio",
    },
}


def get_enabled_servers() -> dict[str, dict[str, object]]:
    raw = os.getenv("MCP_ENABLED_SERVERS", "").strip()
    if not raw:
        return dict(MCP_SERVERS_CONFIG)
    enabled = {item.strip() for item in raw.split(",") if item.strip()}
    return {name: config for name, config in MCP_SERVERS_CONFIG.items() if name in enabled}


__all__ = ["MCP_SERVERS_CONFIG", "get_enabled_servers"]
