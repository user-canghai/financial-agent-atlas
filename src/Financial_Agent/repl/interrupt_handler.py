from __future__ import annotations

import json
import select
import sys
from typing import Any

from Financial_Agent.config import Config
from Financial_Agent.repl.colors import Colors
from Financial_Agent.repl.tool_display import format_json


def _read_line(prompt: str, timeout: int) -> str | None:
    print(prompt, end="", flush=True)

    if not sys.stdin.isatty():
        return None

    try:
        readable, _, _ = select.select([sys.stdin], [], [], timeout)
    except (OSError, ValueError):
        return None

    if not readable:
        print()
        return None

    line = sys.stdin.readline()
    if line == "":
        print()
        return None
    return line.strip()


def get_user_decision(
    action_name: str,
    action_args: dict[str, Any],
    allowed_decisions: list[str],
    spinner: Any = None,
) -> dict[str, Any]:
    timeout = Config.get_interrupt_timeout()

    if spinner is not None:
        spinner.pause()

    try:
        if Config.auto_approve_tools() or not sys.stdin.isatty():
            print(
                "\n"
                + Colors.bright_yellow(
                    f"[自动批准] {action_name}（非交互环境或 AUTO_APPROVE_TOOLS=true）"
                )
            )
            return {"type": "approve"}

        print()
        print(f"工具: {action_name}")
        print(f"参数: {format_json(action_args)}")
        print()
        print(f"请选择一个决定 ({timeout} 秒后自动批准):")
        labels = {
            "approve": "批准此工具调用",
            "edit": "编辑工具参数后执行",
            "reject": "拒绝此工具调用",
        }
        for index, decision in enumerate(allowed_decisions, start=1):
            print(f"  [{index}] {decision} - {labels.get(decision, decision)}")

        choice = _read_line("请输入你的决定 (输入序号或决定名称): ", timeout)
        if choice is None:
            print("[超时] 等待超时，自动批准工具调用")
            return {"type": "approve"}

        decision_type = ""
        if choice.isdigit():
            index = int(choice) - 1
            if 0 <= index < len(allowed_decisions):
                decision_type = allowed_decisions[index]
        elif choice in allowed_decisions:
            decision_type = choice

        if not decision_type:
            print("无效的选择，自动批准。")
            return {"type": "approve"}

        if decision_type == "approve":
            return {"type": "approve"}
        if decision_type == "reject":
            message = _read_line("请输入拒绝原因（可留空）: ", timeout)
            decision: dict[str, Any] = {"type": "reject"}
            if message:
                decision["message"] = message
            return decision

        print()
        print("请输入编辑后的参数（JSON 格式）:")
        print(f"当前: {json.dumps(action_args, ensure_ascii=False)}")
        edited = _read_line("编辑后的参数: ", timeout)
        if not edited:
            print("[超时] 未提供参数，自动批准原调用。")
            return {"type": "approve"}
        try:
            edited_args = json.loads(edited)
        except json.JSONDecodeError:
            print("JSON 格式错误，自动批准原调用。")
            return {"type": "approve"}
        return {
            "type": "edit",
            "edited_action": {"name": action_name, "args": edited_args},
        }
    finally:
        if spinner is not None:
            spinner.resume()


__all__ = ["get_user_decision"]
