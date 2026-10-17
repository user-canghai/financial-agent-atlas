from __future__ import annotations

from functools import lru_cache
from typing import Any

from langchain_core.tools import BaseTool


@lru_cache(maxsize=1)
def _collect_native_tools() -> tuple[BaseTool, ...]:
    from Financial_Agent.tools import tools as tools_module

    collected: list[BaseTool] = []
    for name in tools_module.__all__:
        obj = getattr(tools_module, name, None)
        if isinstance(obj, BaseTool):
            collected.append(obj)
    return tuple(collected)


class _NativeToolsSequence:
    def __iter__(self):
        return iter(_collect_native_tools())

    def __len__(self) -> int:
        return len(_collect_native_tools())

    def __getitem__(self, index):
        return _collect_native_tools()[index]

    def __repr__(self) -> str:
        return repr(_collect_native_tools())

    def clear_cache(self) -> None:
        _collect_native_tools.cache_clear()


NATIVE_TOOLS = _NativeToolsSequence()

TOOL_INTERRUPT_CONFIG: dict[str, bool | dict[str, Any]] = {
    "web_search": {"allowed_decisions": ["approve", "edit", "reject"]},
    "database_search": {"allowed_decisions": ["approve", "reject"]},
    "get_company_profile": False,
    "get_weather": False,
    "read_mcp_resource": False,
    "generate_image": False,
    "write_file": False,
    "read_file": False,
    "edit_file": {"allowed_decisions": ["approve", "reject"]},
    "mkdir": {"allowed_decisions": ["approve", "reject"]},
    "ls": False,
    "glob": False,
    "grep": False,
    "write_todos": False,
}


def get_interrupt_config() -> dict[str, bool | dict[str, Any]]:
    config = dict(TOOL_INTERRUPT_CONFIG)
    for tool_obj in _collect_native_tools():
        config.setdefault(tool_obj.name, False)
    return config


def get_all_native_tools() -> list[BaseTool]:
    return list(_collect_native_tools())


def clear_native_tools_cache() -> None:
    _collect_native_tools.cache_clear()


__all__ = [
    "NATIVE_TOOLS",
    "TOOL_INTERRUPT_CONFIG",
    "get_interrupt_config",
    "get_all_native_tools",
    "clear_native_tools_cache",
]
