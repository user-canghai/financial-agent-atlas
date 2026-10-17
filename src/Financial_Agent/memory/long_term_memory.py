from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from Financial_Agent.config import Config

MAX_MESSAGES = 400


def _now_iso() -> str:
    return datetime.now(UTC).astimezone().isoformat(timespec="seconds")


class ConversationMemory:
    def __init__(self, history_file: Path | str | None = None) -> None:
        self.history_file = Path(history_file) if history_file else None
        self.messages: list[dict[str, Any]] = []
        if self.history_file is not None:
            self.load()

    def load(self) -> list[dict[str, Any]]:
        if self.history_file is None or not self.history_file.is_file():
            self.messages = []
            return self.messages
        try:
            data = json.loads(self.history_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self.messages = []
            return self.messages
        if isinstance(data, dict):
            data = data.get("messages", [])
        if not isinstance(data, list):
            data = []
        self.messages = [item for item in data if isinstance(item, dict)]
        return self.messages

    def add(self, role: str, content: str) -> None:
        if not content:
            return
        self.messages.append({"role": role, "content": content, "timestamp": _now_iso()})
        if len(self.messages) > MAX_MESSAGES:
            self.messages = self.messages[-MAX_MESSAGES:]

    def save(self) -> Path | None:
        if self.history_file is None:
            return None
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 1,
            "updated_at": _now_iso(),
            "messages": self.messages,
        }
        tmp_file = self.history_file.with_suffix(".json.tmp")
        tmp_file.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        os.replace(tmp_file, self.history_file)
        return self.history_file

    def clear(self) -> None:
        self.messages = []
        if self.history_file is not None and self.history_file.exists():
            self.history_file.unlink()

    def to_markdown(self) -> str:
        lines = ["# 对话记录", ""]
        for message in self.messages:
            role = "用户" if message.get("role") == "user" else "助手"
            lines.append(f"## {role}")
            lines.append("")
            lines.append(str(message.get("content", "")))
            lines.append("")
        return "\n".join(lines).strip() + "\n"


def load_conversation_history(conversation_name: str | None = None) -> list[dict[str, Any]]:
    path = Config.get_conversation_history_file(conversation_name)
    return ConversationMemory(path).messages


def save_conversation_history(
    messages: list[dict[str, Any]],
    conversation_name: str | None = None,
) -> Path:
    path = Config.get_conversation_history_file(conversation_name)
    memory = ConversationMemory(path)
    memory.messages = messages[-(MAX_MESSAGES):]
    saved = memory.save()
    assert saved is not None
    return saved


def add_to_history(
    messages: list[dict[str, Any]],
    role: str,
    content: str,
) -> list[dict[str, Any]]:
    updated = list(messages)
    if content:
        updated.append({"role": role, "content": content, "timestamp": _now_iso()})
    return updated[-MAX_MESSAGES:]


__all__ = [
    "ConversationMemory",
    "load_conversation_history",
    "save_conversation_history",
    "add_to_history",
]
