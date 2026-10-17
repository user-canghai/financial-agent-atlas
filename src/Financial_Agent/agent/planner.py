from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Plan:
    goal: str
    steps: list[str] = field(default_factory=list)


PLANNING_KEYWORDS = (
    "步骤",
    "分步",
    "规划",
    "计划",
    "并且",
    "然后",
    "最后",
    "报告",
    "研究",
    "分析",
)


def should_plan(prompt: str) -> bool:
    if len(prompt) >= 120:
        return True
    keyword_hits = sum(1 for keyword in PLANNING_KEYWORDS if keyword in prompt)
    action_hits = sum(prompt.count(marker) for marker in ("1.", "2.", "3.", "；", ";"))
    return keyword_hits >= 2 or action_hits >= 3


def build_plan(prompt: str) -> Plan:
    steps = [
        "理解目标与约束",
        "匹配 Skill 并读取其工作流",
        "收集所需信息",
        "执行任务并生成产出",
        "验证产出与交付",
    ]
    return Plan(goal=prompt.strip(), steps=steps)


__all__ = ["Plan", "should_plan", "build_plan"]
