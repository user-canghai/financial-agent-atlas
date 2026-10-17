from __future__ import annotations

from collections.abc import Callable

from deepagents.middleware.subagents import SubAgent
from langchain_core.language_models import BaseChatModel

from Financial_Agent.subagents.templates import IMAGE_AGENT_PROMPT, WRITER_AGENT_PROMPT
from Financial_Agent.tools.tools import generate_image

ModelFactory = Callable[[float], BaseChatModel]


def build_subagents(model_factory: ModelFactory) -> list[SubAgent]:
    return [
        {
            "name": "writer-agent",
            "description": (
                "专业财经/行业报告写作代理。仅在 Skill 明确要求或用户明确要求时使用；"
                "它只根据已有素材写作，不进行搜索、研究或图片生成。"
            ),
            "system_prompt": WRITER_AGENT_PROMPT,
            "model": model_factory(0.7),
            "tools": [],
        },
        {
            "name": "image-generator-agent",
            "description": (
                "AI 图像生成代理。仅在 Skill 明确要求或用户明确要求时使用；"
                "根据文字描述调用 generate_image 生成研报配图。"
            ),
            "system_prompt": IMAGE_AGENT_PROMPT,
            "model": model_factory(0.5),
            "tools": [generate_image],
        },
    ]


__all__ = ["build_subagents"]
