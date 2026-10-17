from __future__ import annotations

import importlib
import shutil
import sys
from pathlib import Path

from Financial_Agent.config import Config
from Financial_Agent.mcp.mcp import MCP_SERVERS_CONFIG

DEPENDENCIES = (
    "langchain",
    "deepagents",
    "langchain_openai",
    "langchain_mcp_adapters",
    "mcp",
    "dotenv",
    "dashscope",
    "pandas",
    "numpy",
    "rich",
)


def _check_dependencies() -> list[tuple[str, bool, str]]:
    results = []
    for name in DEPENDENCIES:
        try:
            module = importlib.import_module(name)
            version = getattr(module, "__version__", "installed")
            results.append((name, True, str(version)))
        except Exception as exc:
            results.append((name, False, str(exc)))
    return results


def run_self_check() -> int:
    print("=" * 72)
    print("Financial-Agent-AtlasServer 环境自检")
    print("=" * 72)
    print(f"Python      : {sys.version.split()[0]} ({sys.executable})")
    print(f"项目根目录  : {Config.get_root_dir()}")
    print(f"记忆目录    : {Config.get_memory_dir()}")
    print(f"技能目录    : {Config.get_skills_dir()}")
    print(f"工作区目录  : {Config.get_workspace_dir()}")

    Config.ensure_directories()

    print("\n[依赖]")
    for name, ok, detail in _check_dependencies():
        mark = "✓" if ok else "✗"
        print(f"  {mark} {name:<24} {detail}")

    print("\n[外部命令]")
    for command in ("uv", "uvx", "node", "npx"):
        path = shutil.which(command)
        print(
            f"  {'✓' if path else '-'} {command:<8} {path or '未安装（对应 MCP 服务器会被跳过）'}"
        )

    print("\n[凭证]")
    result = Config.validate_credentials()
    for name in Config.REQUIRED_CREDENTIALS:
        mark = "✓" if name not in result["missing"] else "✗"
        print(f"  {mark} {name}")
    for name in Config.OPTIONAL_CREDENTIALS:
        mark = "✓" if any(name in info for info in result["info"]) else "-"
        print(f"  {mark} {name}")

    print("\n[MCP 服务器]")
    for name, server_config in MCP_SERVERS_CONFIG.items():
        command = server_config.get("command", "")
        available = bool(shutil.which(command)) or Path(command).exists()
        print(f"  {'✓' if available else '-'} {name:<14} {command}")

    print("\n[Skills]")
    skills_dir = Config.get_skills_dir()
    skill_files = sorted(skills_dir.glob("*/SKILL.md")) if skills_dir.is_dir() else []
    if not skill_files:
        print("  - 未发现 SKILL.md")
    for skill_file in skill_files:
        print(f"  ✓ {skill_file.parent.name}")

    print(
        "\n结论:",
        "凭证齐全，可以运行 Agent。" if result["valid"] else "缺少必需凭证，请编辑 .env。",
    )
    print("=" * 72)
    return 0 if result["valid"] else 1


def print_mcp_status() -> int:
    print("=" * 72)
    print("MCP 服务器状态")
    print("=" * 72)
    for name, server_config in MCP_SERVERS_CONFIG.items():
        command = server_config.get("command", "")
        args = " ".join(server_config.get("args", []))
        available = bool(shutil.which(command)) or Path(command).exists()
        print(f"[{name}] {'可用' if available else '不可用'}")
        print(f"  command : {command}")
        print(f"  args    : {args}")
        print(f"  transport: {server_config.get('transport', 'stdio')}")
    print("=" * 72)
    return 0


__all__ = ["run_self_check", "print_mcp_status"]
