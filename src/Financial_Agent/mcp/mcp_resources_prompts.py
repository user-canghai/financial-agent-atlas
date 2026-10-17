from __future__ import annotations

from collections import defaultdict

from Financial_Agent.mcp.adapter import parse_tool_name
from Financial_Agent.mcp.manager import get_manager
from Financial_Agent.mcp.mcp import get_enabled_servers


def get_mcp_tools_info_for_prompt() -> str:
    tools = get_manager().get_tools_sync()
    if not tools:
        return "### 可用的 MCP 工具\n\n暂无可用 MCP 工具。"

    servers = set(get_enabled_servers())
    grouped: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for tool_obj in tools:
        server, actual_name = parse_tool_name(tool_obj.name, servers)
        grouped[server].append((actual_name, tool_obj.description or ""))

    lines = ["### 可用的 MCP 工具", "", "调用时使用完整工具名（包含服务器前缀）。", ""]
    for server in sorted(grouped):
        lines.append(f"#### {server}")
        for actual_name, description in sorted(grouped[server]):
            suffix = f": {description}" if description else ""
            lines.append(f"- **{actual_name}**{suffix}")
        lines.append("")
    return "\n".join(lines).strip()


def get_mcp_resources_info_for_prompt() -> str:
    resources = get_manager().get_resources_info_sync()
    if not resources:
        return "### 可用的 MCP Resources\n\n暂无可用资源。"
    lines = ["### 可用的 MCP Resources", ""]
    for resource in resources:
        description = resource.description or resource.name or "只读资源"
        lines.append(f"- **{resource.uri}** ({resource.server}): {description}")
    return "\n".join(lines)


def get_mcp_prompts_info_for_prompt() -> str:
    prompts = get_manager().get_prompts_info_sync()
    if not prompts:
        return "### 可用的 MCP Prompts\n\n暂无可用提示词模板。"
    lines = ["### 可用的 MCP Prompts", ""]
    for prompt in prompts:
        lines.append(f"#### {prompt.name}")
        if prompt.description:
            lines.append(prompt.description)
        if prompt.arguments:
            names = ", ".join(str(arg.get("name", "")) for arg in prompt.arguments)
            lines.append(f"参数: {names}")
        if prompt.content:
            lines.extend(["", "```text", prompt.content.strip(), "```"])
        lines.append("")
    return "\n".join(lines).strip()


def get_mcp_all_info_for_prompt() -> str:
    servers = get_enabled_servers()
    lines = ["## MCP 服务器", "", "### 已配置的服务器", ""]
    if not servers:
        lines.append("未启用任何 MCP 服务器（请检查 `MCP_ENABLED_SERVERS`）。")
        return "\n".join(lines)

    for name, server_config in servers.items():
        command = server_config.get("command", "")
        args = " ".join(str(arg) for arg in server_config.get("args", []))
        lines.append(f"- **{name}**: `{command} {args}`".rstrip())

    lines.extend(["", get_mcp_tools_info_for_prompt(), ""])
    lines.extend([get_mcp_resources_info_for_prompt(), ""])
    lines.extend([get_mcp_prompts_info_for_prompt()])
    return "\n".join(lines).strip()


__all__ = [
    "get_mcp_tools_info_for_prompt",
    "get_mcp_resources_info_for_prompt",
    "get_mcp_prompts_info_for_prompt",
    "get_mcp_all_info_for_prompt",
]
