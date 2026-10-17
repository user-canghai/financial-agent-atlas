from __future__ import annotations

import re
from pathlib import Path

import yaml
from mcp.server.fastmcp import FastMCP

from Financial_Agent.config import Config


def _parse_frontmatter(content: str) -> dict:
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not match:
        return {}
    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def list_skills() -> list[dict[str, str]]:
    skills: list[dict[str, str]] = []
    for skill_file in sorted(Config.get_skills_dir().glob("*/SKILL.md")):
        content = skill_file.read_text(encoding="utf-8")
        metadata = _parse_frontmatter(content)
        skills.append(
            {
                "name": str(metadata.get("name") or skill_file.parent.name),
                "description": str(metadata.get("description") or ""),
                "path": str(skill_file),
            }
        )
    return skills


def read_skill(name: str) -> str:
    safe_name = Path(name).name
    skill_file = Config.get_skills_dir() / safe_name / "SKILL.md"
    if not skill_file.is_file():
        return f"未找到技能: {name}"
    return skill_file.read_text(encoding="utf-8")


def create_skills_server() -> FastMCP:
    server = FastMCP("Financial Skills")
    server.tool(name="list_skills", description="列出所有可用技能")(list_skills)
    server.tool(name="read_skill", description="读取指定技能的 SKILL.md")(read_skill)
    return server


if __name__ == "__main__":
    create_skills_server().run()
