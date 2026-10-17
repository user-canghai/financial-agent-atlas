from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SkillResult:
    success: bool
    content: str
    artifacts: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseSkill(ABC):
    name: str = ""
    description: str = ""
    keywords: tuple[str, ...] = ()

    def match(self, query: str) -> int:
        lowered = query.lower()
        return sum(1 for keyword in self.keywords if keyword.lower() in lowered)

    @abstractmethod
    def execute(self, **kwargs: Any) -> SkillResult:
        raise NotImplementedError


__all__ = ["BaseSkill", "SkillResult"]
