from __future__ import annotations

import importlib.util
import inspect
from pathlib import Path

from Financial_Agent.config import Config
from Financial_Agent.skills.base_skill import BaseSkill

_CACHE: list[BaseSkill] | None = None


def _iter_skill_files() -> list[Path]:
    root = Config.get_skills_dir()
    if not root.is_dir():
        return []
    files: list[Path] = []
    for path in sorted(root.rglob("*.py")):
        if path.name in {"__init__.py", "base.py"}:
            continue
        if any(part.startswith(".") for part in path.relative_to(root).parts):
            continue
        files.append(path)
    return files


def _load_module(path: Path, index: int):
    module_name = f"_financial_agent_business_skill_{index}_{path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def discover_skills(*, refresh: bool = False) -> list[BaseSkill]:
    global _CACHE
    if _CACHE is not None and not refresh:
        return list(_CACHE)

    discovered: list[BaseSkill] = []
    for index, path in enumerate(_iter_skill_files()):
        try:
            module = _load_module(path, index)
        except Exception:
            continue
        if module is None:
            continue
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if (
                issubclass(obj, BaseSkill)
                and obj is not BaseSkill
                and not inspect.isabstract(obj)
                and obj.__module__ == module.__name__
            ):
                discovered.append(obj())

    _CACHE = discovered
    return list(discovered)


def get_skill(name: str) -> BaseSkill | None:
    for skill in discover_skills():
        if skill.name == name:
            return skill
    return None


def find_skills(query: str) -> list[tuple[int, BaseSkill]]:
    scored = [(skill.match(query), skill) for skill in discover_skills()]
    return sorted([item for item in scored if item[0] > 0], key=lambda item: -item[0])


__all__ = ["discover_skills", "get_skill", "find_skills"]
