from __future__ import annotations

import logging
from typing import Any

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, FilesystemBackend
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore

from Financial_Agent.config import Config
from Financial_Agent.mcp.manager import get_manager
from Financial_Agent.repl.logging import configure_logging
from Financial_Agent.subagents import build_subagents
from Financial_Agent.tools import NATIVE_TOOLS, get_interrupt_config, get_mcp_tools

logger = logging.getLogger(__name__)


def create_llm(temperature: float = 0.0) -> ChatOpenAI:
    model = Config.get_qwen_model()
    api_key = Config.get_qwen_api()
    base_url = Config.get_qwen_url()
    if not model or not api_key or not base_url:
        raise ValueError("缺少 QWEN_MODEL / QWEN_API / QWEN_URL，无法创建模型。")
    return ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url=base_url,
        temperature=temperature,
        timeout=120,
        max_retries=2,
    )


def _make_backend(_runtime: Any) -> CompositeBackend:
    project_root = str(Config.get_root_dir())
    routes = {
        "/skills/": FilesystemBackend(root_dir=str(Config.get_skills_dir()), virtual_mode=True),
        "/memories/": FilesystemBackend(root_dir=str(Config.get_memory_dir()), virtual_mode=True),
        "/workspace/": FilesystemBackend(
            root_dir=str(Config.get_workspace_dir()), virtual_mode=True
        ),
        "/tools/": FilesystemBackend(
            root_dir=str(Config.get_root_dir() / "src" / "Financial_Agent" / "tools"),
            virtual_mode=True,
        ),
        "/mcp_servers/": FilesystemBackend(
            root_dir=str(Config.get_root_dir() / "src" / "Financial_Agent" / "mcp" / "servers"),
            virtual_mode=True,
        ),
    }
    return CompositeBackend(default=FilesystemBackend(root_dir=project_root), routes=routes)


def setup_agent(conversation_name: str | None = None) -> Any:
    configure_logging()
    Config.ensure_directories()

    logger.info("=" * 80)
    logger.info("验证必需的凭证...")
    logger.info("=" * 80)
    result = Config.validate_credentials()
    if not result["valid"]:
        missing = ", ".join(result["missing"])
        raise ValueError(f"缺少必需凭证: {missing}。请复制 .env.example 为 .env 并填写。")

    logger.info("✓ IMAGE_MODEL: %s", Config.get_image_model())
    logger.info("✓ IMAGE_SIZE: %s", Config.get_image_size())
    logger.info("=" * 80)

    llm = create_llm(0.0)

    system_prompt = Config.generate_system_prompt(include_mcp=True)
    mcp_tools = get_mcp_tools()

    native_tools = list(NATIVE_TOOLS)
    logger.info("加载 Tools ...")
    logger.info("已加载 %d 个本地 Tools", len(native_tools))
    main_tools = [tool_obj for tool_obj in native_tools if tool_obj.name != "generate_image"]
    logger.info(
        "主 Agent 可用工具: %d 个（generate_image 由 SubAgent 专用）",
        len(main_tools),
    )

    memory_files = [f"/memories/{path.name}" for path in Config.get_memory_files()]

    agent = create_deep_agent(
        model=llm,
        tools=[*main_tools, *mcp_tools],
        system_prompt=system_prompt,
        subagents=build_subagents(create_llm),
        skills=["/skills/"],
        memory=memory_files or None,
        backend=_make_backend,
        store=InMemoryStore(),
        checkpointer=MemorySaver(),
        interrupt_on=get_interrupt_config(),
    )

    logger.info("已加载 %d 个 Memory 文件", len(memory_files))
    logger.info("=" * 80)
    return agent


def shutdown_agent() -> None:
    get_manager().close()


__all__ = ["setup_agent", "shutdown_agent", "create_llm"]
