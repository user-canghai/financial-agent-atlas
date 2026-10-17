from __future__ import annotations

import asyncio
import base64
import logging
import shutil
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from langchain_mcp_adapters.client import MultiServerMCPClient

from Financial_Agent.mcp.mcp import get_enabled_servers

logger = logging.getLogger(__name__)


@dataclass
class MCPResourceInfo:
    server: str
    uri: str
    name: str
    description: str = ""


@dataclass
class MCPPromptInfo:
    server: str
    name: str
    description: str = ""
    arguments: list[dict[str, Any]] = field(default_factory=list)
    content: str = ""


def _run_sync(coro: Any) -> Any:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    result: dict[str, Any] = {}

    def runner() -> None:
        try:
            result["value"] = asyncio.run(coro)
        except BaseException as exc:
            result["error"] = exc

    thread = threading.Thread(target=runner, daemon=True)
    thread.start()
    thread.join()
    if "error" in result:
        raise result["error"]
    return result.get("value")


def _command_available(server_config: dict[str, Any]) -> bool:
    command = str(server_config.get("command", ""))
    if not command:
        return False
    if Path(command).exists():
        return True
    return bool(shutil.which(command))


def _content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        return str(content.get("text", content))
    if isinstance(content, (list, tuple)):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                parts.append(str(item.get("text", item)))
            else:
                parts.append(str(item))
        return "\n".join(parts)
    return str(content)


def _normalize_tool_result(result: Any) -> Any:
    if isinstance(result, tuple) and len(result) == 2:
        content, artifact = result
        return _content_to_text(content), artifact
    return _content_to_text(result)


def _make_sync_tool(tool: Any) -> Any:
    if getattr(tool, "func", None) is not None or getattr(tool, "coroutine", None) is None:
        return tool

    coroutine = tool.coroutine

    def sync_func(**kwargs: Any) -> Any:
        return _normalize_tool_result(_run_sync(coroutine(**kwargs)))

    async def async_func(**kwargs: Any) -> Any:
        return _normalize_tool_result(await coroutine(**kwargs))

    try:
        return tool.model_copy(update={"func": sync_func, "coroutine": async_func})
    except Exception:
        return tool


class MCPToolsManager:
    def __init__(self, cache_ttl: int = 300) -> None:
        self.cache_ttl = cache_ttl
        self._client: MultiServerMCPClient | None = None
        self._cache: dict[str, tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def _get_client(self) -> MultiServerMCPClient:
        if self._client is None:
            self._client = MultiServerMCPClient(
                get_enabled_servers(),
                tool_name_prefix=True,
            )
            logger.info("MCP client 初始化中")
        return self._client

    def _cache_get(self, key: str) -> Any | None:
        item = self._cache.get(key)
        if item is None:
            return None
        timestamp, value = item
        if time.time() - timestamp >= self.cache_ttl:
            self._cache.pop(key, None)
            return None
        return value

    def _cache_set(self, key: str, value: Any) -> None:
        self._cache[key] = (time.time(), value)

    async def get_tools(self, server_name: str | None = None) -> list[Any]:
        cache_key = f"tools:{server_name or 'all'}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        client = self._get_client()
        servers = get_enabled_servers()
        names = [server_name] if server_name else list(servers)

        logger.info("从 MCP server 中加载 Tools ...")
        collected: list[Any] = []
        for name in names:
            if name not in servers:
                logger.warning("跳过未配置的 MCP 服务器: %s", name)
                continue
            if not _command_available(servers[name]):
                logger.warning(
                    "[MCP] %s 启动命令不可用，已跳过: %s",
                    name,
                    servers[name].get("command"),
                )
                continue
            try:
                tools = await client.get_tools(server_name=name)
                tools = [_make_sync_tool(tool) for tool in tools]
                collected.extend(tools)
                logger.debug("[MCP] %s: %d 个工具", name, len(tools))
            except BaseException as exc:
                logger.warning(
                    "[MCP] 加载 %s 工具失败: %s: %r",
                    name,
                    type(exc).__name__,
                    exc,
                )

        self._cache_set(cache_key, collected)
        logger.info("已解析 %d 个 Tools  %s", len(collected), server_name or "all")
        return collected

    async def get_resources_info(self, server_name: str | None = None) -> list[MCPResourceInfo]:
        cache_key = f"resources:{server_name or 'all'}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        client = self._get_client()
        servers = get_enabled_servers()
        names = [server_name] if server_name else list(servers)
        resources: list[MCPResourceInfo] = []

        for name in names:
            if name not in servers or not _command_available(servers[name]):
                continue
            try:
                async with client.session(name) as session:
                    result = await session.list_resources()
                    for resource in result.resources:
                        resources.append(
                            MCPResourceInfo(
                                server=name,
                                uri=str(resource.uri),
                                name=resource.name,
                                description=resource.description or "",
                            )
                        )
            except BaseException as exc:
                logger.debug("[MCP] %s 不提供 Resources 或读取失败: %s", name, exc)

        self._cache_set(cache_key, resources)
        logger.info("已解析 %d 个 Resources  %s", len(resources), cache_key)
        return resources

    async def get_prompts_info(self, server_name: str | None = None) -> list[MCPPromptInfo]:
        cache_key = f"prompts:{server_name or 'all'}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        client = self._get_client()
        servers = get_enabled_servers()
        names = [server_name] if server_name else list(servers)
        prompts: list[MCPPromptInfo] = []

        for name in names:
            if name not in servers or not _command_available(servers[name]):
                continue
            try:
                async with client.session(name) as session:
                    listing = await session.list_prompts()
                    for prompt in listing.prompts:
                        content = ""
                        try:
                            result = await session.get_prompt(prompt.name)
                            parts: list[str] = []
                            for message in result.messages:
                                text = getattr(message.content, "text", None)
                                if text:
                                    parts.append(text)
                                else:
                                    parts.append(str(message.content))
                            content = "\n".join(parts)
                        except BaseException as exc:
                            logger.debug("[MCP] 读取提示词 %s/%s 失败: %s", name, prompt.name, exc)
                        prompts.append(
                            MCPPromptInfo(
                                server=name,
                                name=f"{name}:{prompt.name}",
                                description=prompt.description or f"{name} 提示词模板",
                                arguments=[
                                    arg.model_dump() if hasattr(arg, "model_dump") else dict(arg)
                                    for arg in (prompt.arguments or [])
                                ],
                                content=content,
                            )
                        )
            except BaseException as exc:
                logger.debug("[MCP] %s 不提供 Prompts 或读取失败: %s", name, exc)

        self._cache_set(cache_key, prompts)
        logger.info("已解析 %d 个 Prompts  %s", len(prompts), cache_key)
        return prompts

    async def read_resource(self, server_name: str, resource_uri: str) -> str:
        servers = get_enabled_servers()
        if server_name not in servers:
            return f"读取 MCP 资源失败：未配置服务器 {server_name}。"
        if not _command_available(servers[server_name]):
            return f"读取 MCP 资源失败：服务器 {server_name} 的启动命令不可用。"

        client = self._get_client()
        try:
            async with client.session(server_name) as session:
                result = await session.read_resource(resource_uri)
                parts: list[str] = []
                for content in result.contents:
                    text = getattr(content, "text", None)
                    if text is not None:
                        parts.append(text)
                    else:
                        blob = getattr(content, "blob", None)
                        if blob is not None:
                            parts.append(base64.b64decode(blob).decode("utf-8", errors="replace"))
                return "\n".join(parts) if parts else f"资源 {resource_uri} 的内容为空。"
        except BaseException as exc:
            return f"读取 MCP 资源失败：{exc}"

    def get_tools_sync(self, server_name: str | None = None) -> list[Any]:
        with self._lock:
            return _run_sync(self.get_tools(server_name))

    def get_resources_info_sync(self, server_name: str | None = None) -> list[MCPResourceInfo]:
        with self._lock:
            return _run_sync(self.get_resources_info(server_name))

    def get_prompts_info_sync(self, server_name: str | None = None) -> list[MCPPromptInfo]:
        with self._lock:
            return _run_sync(self.get_prompts_info(server_name))

    def read_resource_sync(self, server_name: str, resource_uri: str) -> str:
        with self._lock:
            return _run_sync(self.read_resource(server_name, resource_uri))

    def clear_cache(self) -> None:
        with self._lock:
            self._cache.clear()

    def close(self) -> None:
        with self._lock:
            self._client = None
            self._cache.clear()

    def get_cache_info(self) -> dict[str, Any]:
        return {
            "ttl": self.cache_ttl,
            "entries": {
                key: {"age_seconds": round(time.time() - timestamp, 1)}
                for key, (timestamp, _) in self._cache.items()
            },
        }


_manager: MCPToolsManager | None = None


def get_manager() -> MCPToolsManager:
    global _manager
    if _manager is None:
        _manager = MCPToolsManager()
    return _manager


__all__ = [
    "MCPToolsManager",
    "MCPResourceInfo",
    "MCPPromptInfo",
    "get_manager",
]
