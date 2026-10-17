from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from langchain_core.messages import AIMessage, ToolMessage

from Financial_Agent.repl.tool_display import format_tool_call, format_tool_result


def message_text(message: Any) -> str:
    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
            elif isinstance(block, str):
                parts.append(block)
        return "\n".join(part for part in parts if part)
    return str(content)


@dataclass
class StepLogger:
    tool_calls: list[str] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)

    def record(self, tool_name: str) -> None:
        self.tool_calls.append(tool_name)

    def print_summary(self) -> None:
        elapsed = time.time() - self.start_time
        print()
        print("─" * 79)
        print(f"执行摘要: {len(self.tool_calls)} 次工具调用, 耗时 {elapsed:.1f}s")
        if self.tool_calls:
            counts: dict[str, int] = {}
            for name in self.tool_calls:
                counts[name] = counts.get(name, 0) + 1
            detail = ", ".join(f"{name}×{count}" for name, count in counts.items())
            print(f"工具: {detail}")
        print("─" * 79)


class AgentDisplay:
    def __init__(self, logger: StepLogger, spinner: Any = None) -> None:
        self.logger = logger
        self.spinner = spinner
        self.agent_name = "DeepAgent"
        self._printed: set[int] = set()

    def _write(self, text: str) -> None:
        if not text:
            return
        if self.spinner is not None:
            self.spinner.pause()
        print(text)
        if self.spinner is not None:
            self.spinner.resume()

    def print_message(self, message: Any) -> None:
        message_id = id(message)
        if message_id in self._printed:
            return
        self._printed.add(message_id)

        if isinstance(message, AIMessage):
            self._print_ai(message)
        elif isinstance(message, ToolMessage):
            self._print_tool(message)

    def _print_ai(self, message: AIMessage) -> None:
        tool_calls = getattr(message, "tool_calls", None) or []
        for tool_call in tool_calls:
            name = str(tool_call.get("name", "unknown"))
            args = tool_call.get("args", {}) or {}
            if name == "task":
                subagent = str(args.get("subagent_type", "unknown"))
                self._write("\n" + "=" * 60)
                self._write(f"[SUBAGENT] 进入 SubAgent: {subagent}")
                self._write("=" * 60)
                self.agent_name = subagent
            self.logger.record(name)
            self._write("\n".join(format_tool_call(name, args)))

        text = message_text(message).strip()
        if text:
            self._write(f"\n  {self.agent_name}:")
            self._write("─" * 79)
            self._write(text)

    def _print_tool(self, message: ToolMessage) -> None:
        name = message.name or "tool"
        self._write("\n".join(format_tool_result(name, message_text(message))))


__all__ = ["AgentDisplay", "StepLogger", "message_text"]
