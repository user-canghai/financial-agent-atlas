from __future__ import annotations

from pathlib import Path

from Financial_Agent.config import Config
from Financial_Agent.skills.base_skill import BaseSkill, SkillResult


class ReportGenerationSkill(BaseSkill):
    name = "report"
    description = "将章节内容与图片组装为 Markdown 报告"
    keywords = ("报告", "markdown", "配图", "report")

    def execute(self, **kwargs) -> SkillResult:
        title = str(kwargs.get("title", "行业研究报告"))
        sections = kwargs.get("sections", [])
        image = str(kwargs.get("image", "")).strip()
        output = str(kwargs.get("output", "final_report.md"))

        if not isinstance(sections, list) or not sections:
            return SkillResult(False, "sections 必须是非空列表")

        lines = [f"# {title}", ""]
        if image:
            image_path = Config.get_pic_dir() / Path(image).name
            if not image_path.is_file():
                return SkillResult(False, f"配图不存在: {image_path}")
            lines.extend([f"![{title}配图](./pic/{image_path.name})", ""])

        for section in sections:
            if isinstance(section, dict):
                heading = str(section.get("heading", "")).strip()
                body = str(section.get("content", "")).strip()
            else:
                heading, body = "", str(section)
            if heading:
                lines.extend([f"## {heading}", ""])
            if body:
                lines.extend([body, ""])

        workspace = Config.get_workspace_dir()
        relative = output.strip()
        if relative.startswith("/workspace/"):
            relative = relative[len("/workspace/") :]
        elif relative.startswith("workspace/"):
            relative = relative[len("workspace/") :]
        target = (workspace / relative.lstrip("/")).resolve()
        if workspace not in target.parents and target != workspace:
            return SkillResult(False, "输出路径越界")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
        return SkillResult(True, f"报告已生成: {target}", artifacts=[str(target)])


__all__ = ["ReportGenerationSkill"]
