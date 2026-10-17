from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

logger = logging.getLogger(__name__)


class Config:
    REQUIRED_CREDENTIALS = ("QWEN_MODEL", "QWEN_API", "QWEN_URL", "BOCHA_API_KEY")
    OPTIONAL_CREDENTIALS = ("IMAGE_MODEL", "IMAGE_SIZE_DEFAULT")

    @staticmethod
    def get_root_dir() -> Path:
        return PROJECT_ROOT

    @classmethod
    def _get_dir(cls, env_name: str, default: str) -> Path:
        raw = os.getenv(env_name, default)
        path = Path(raw).expanduser()
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        return path.resolve()

    @classmethod
    def get_memory_dir(cls) -> Path:
        return cls._get_dir("MEMORY_DIR", "./memories")

    @classmethod
    def get_skills_dir(cls) -> Path:
        return cls._get_dir("SKILLS_DIR", "./skills")

    @classmethod
    def get_workspace_dir(cls) -> Path:
        return cls._get_dir("WORKSPACE_DIR", "./workspaces")

    @classmethod
    def get_pic_dir(cls) -> Path:
        return cls.get_workspace_dir() / "pic"

    @classmethod
    def get_conversation_history_file(cls, conversation_name: str | None = None) -> Path:
        if conversation_name:
            safe_name = "".join(
                char for char in conversation_name if char.isalnum() or char in "-_"
            )
            if not safe_name:
                raise ValueError("conversation_name 不能只包含非法字符")
            filename = f"conversation_history_{safe_name}.json"
        else:
            filename = "conversation_history.json"
        return cls.get_memory_dir() / filename

    @classmethod
    def get_memory_files(cls) -> list[Path]:
        memory_file = cls.get_memory_dir() / "AGENTS.md"
        return [memory_file] if memory_file.is_file() else []

    @classmethod
    def ensure_directories(cls) -> None:
        for directory in (
            cls.get_memory_dir(),
            cls.get_skills_dir(),
            cls.get_workspace_dir(),
            cls.get_pic_dir(),
        ):
            directory.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def get_agent_name() -> str:
        return os.getenv("AGENT_NAME", "Financial Agent Atlas")

    @staticmethod
    def get_agent_role() -> str:
        return os.getenv("AGENT_ROLE", "金融领域智能助手")

    @staticmethod
    def get_agent_description() -> str:
        return os.getenv(
            "AGENT_DESCRIPTION",
            "基于 LangChain、MCP 与 Skills 的金融领域专用 Agent。",
        )

    @staticmethod
    def get_custom_system_prompt() -> str:
        return os.getenv("CUSTOM_SYSTEM_PROMPT", "") or ""

    @staticmethod
    def get_qwen_model() -> str | None:
        return os.getenv("QWEN_MODEL")

    @staticmethod
    def get_qwen_api() -> str | None:
        return os.getenv("QWEN_API")

    @staticmethod
    def get_qwen_url() -> str | None:
        return os.getenv("QWEN_URL")

    @staticmethod
    def get_bocha_api_key() -> str:
        return os.getenv("BOCHA_API_KEY", "") or ""

    @staticmethod
    def get_image_model() -> str:
        return os.getenv("IMAGE_MODEL", "qwen-image-plus")

    @staticmethod
    def get_image_size() -> str:
        return os.getenv("IMAGE_SIZE_DEFAULT") or os.getenv("IMAGE_SIZE") or "1664*928"

    @staticmethod
    def get_image_timeout() -> int:
        try:
            return max(10, int(os.getenv("IMAGE_TIMEOUT", "120")))
        except ValueError:
            return 120

    @staticmethod
    def get_interrupt_timeout() -> int:
        try:
            return max(1, int(os.getenv("TOOL_INTERRUPT_TIMEOUT", "30")))
        except ValueError:
            return 30

    @staticmethod
    def auto_approve_tools() -> bool:
        return os.getenv("AUTO_APPROVE_TOOLS", "false").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

    @staticmethod
    def get_enabled_mcp_servers() -> list[str] | None:
        raw = os.getenv("MCP_ENABLED_SERVERS", "").strip()
        if not raw:
            return None
        return [item.strip() for item in raw.split(",") if item.strip()]

    @staticmethod
    def _is_placeholder(value: str) -> bool:
        lowered = value.strip().lower()
        return (
            not lowered
            or lowered.startswith("sk-your-")
            or "your-api-key" in lowered
            or "your-qwen" in lowered
            or lowered in {"changeme", "placeholder", "replace-me"}
        )

    @classmethod
    def validate_credentials(cls) -> dict[str, Any]:
        result: dict[str, Any] = {"valid": True, "missing": [], "warnings": [], "info": []}

        for name in cls.REQUIRED_CREDENTIALS:
            value = os.getenv(name, "").strip()
            if cls._is_placeholder(value):
                result["missing"].append(name)
                result["valid"] = False
                logger.error("❌ 缺少必需凭证: %s", name)
            else:
                result["info"].append(name)
                logger.info("✓ %s 已配置", name)

        for name in cls.OPTIONAL_CREDENTIALS:
            value = os.getenv(name, "").strip()
            if not value:
                result["warnings"].append(f"{name} 未配置 (可选)")
                logger.warning("⚠ %s 未配置 (可选)", name)
            else:
                result["info"].append(name)
                logger.info("✓ %s 已配置", name)

        if result["valid"]:
            logger.info("✅ 所有必需凭证已正确配置")
        else:
            logger.error("❌ 缺少必需凭证: %s", ", ".join(result["missing"]))
        return result

    @classmethod
    def generate_system_prompt(cls, *, include_mcp: bool = True) -> str:
        prompt = f"""# {cls.get_agent_name()} - {cls.get_agent_role()}

{cls.get_agent_description()}

{cls.get_custom_system_prompt()}
"""

        if include_mcp:
            try:
                from Financial_Agent.mcp.mcp_resources_prompts import (
                    get_mcp_all_info_for_prompt,
                )

                prompt += "\n" + get_mcp_all_info_for_prompt()
            except Exception as exc:
                logger.warning("加载 MCP 信息失败: %s", exc)
                prompt += "\n## MCP 服务器\n\n（当前不可用）\n"

        return prompt.strip() + "\n"


__all__ = ["Config", "PROJECT_ROOT"]
