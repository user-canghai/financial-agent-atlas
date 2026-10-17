from __future__ import annotations

from pathlib import Path

from Financial_Agent.config import Config


def _resolve(path: str) -> Path:
    workspace = Config.get_workspace_dir().resolve()
    relative = path.lstrip("/")
    if relative.startswith("workspace/"):
        relative = relative[len("workspace/") :]
    target = (workspace / relative).resolve()
    if workspace not in target.parents and target != workspace:
        raise ValueError("只允许访问工作区文件")
    return target


def read_workspace_file(path: str) -> str:
    target = _resolve(path)
    if not target.is_file():
        raise FileNotFoundError(path)
    return target.read_text(encoding="utf-8")


def write_workspace_file(path: str, content: str) -> Path:
    target = _resolve(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target


__all__ = ["read_workspace_file", "write_workspace_file"]
