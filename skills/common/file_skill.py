from __future__ import annotations

from pathlib import Path

from Financial_Agent.config import Config
from Financial_Agent.skills.base_skill import BaseSkill, SkillResult


class FileSkill(BaseSkill):
    name = "file"
    description = "在工作区内读写文本文件"
    keywords = ("文件", "保存", "读取", "markdown", "file")

    def _resolve(self, path: str) -> Path:
        workspace = Config.get_workspace_dir().resolve()
        relative = path.strip()
        if relative.startswith("/workspace/"):
            relative = relative[len("/workspace/") :]
        elif relative.startswith("workspace/"):
            relative = relative[len("workspace/") :]
        candidate = (workspace / relative.lstrip("/")).resolve()
        if workspace not in candidate.parents and candidate != workspace:
            raise ValueError("只允许访问工作区文件")
        return candidate

    def execute(self, **kwargs) -> SkillResult:
        action = str(kwargs.get("action", "read"))
        path = str(kwargs.get("path", ""))
        if not path:
            return SkillResult(False, "缺少 path 参数")

        try:
            target = self._resolve(path)
            if action == "read":
                if not target.is_file():
                    return SkillResult(False, f"文件不存在: {path}")
                return SkillResult(True, target.read_text(encoding="utf-8"))
            if action == "write":
                content = str(kwargs.get("content", ""))
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
                return SkillResult(True, f"已写入 {target}", artifacts=[str(target)])
            return SkillResult(False, f"不支持的操作: {action}")
        except Exception as exc:
            return SkillResult(False, f"文件操作失败: {exc}")


__all__ = ["FileSkill"]
