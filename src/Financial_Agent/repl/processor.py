from __future__ import annotations

import sys
from typing import Any

from langchain_core.messages import AIMessage
from langchain_core.runnables.config import RunnableConfig
from langgraph.types import Command

from Financial_Agent.memory import (
    add_to_history,
    load_conversation_history,
    save_conversation_history,
)
from Financial_Agent.repl.display import AgentDisplay, StepLogger, message_text
from Financial_Agent.repl.interrupt_handler import get_user_decision
from Financial_Agent.repl.logging import error, warning


def _extract_user_content(input_data: Any) -> str | None:
    if not isinstance(input_data, dict):
        return None
    messages = input_data.get("messages")
    if not messages:
        return None
    last = messages[-1]
    if isinstance(last, tuple) and len(last) >= 2:
        return str(last[1])
    if isinstance(last, dict) and "content" in last:
        return str(last["content"])
    return None


def _stream_once(
    agent: Any,
    payload: Any,
    config: RunnableConfig,
    debug: bool,
    display: AgentDisplay,
) -> Any:
    for event in agent.stream(payload, config=config, stream_mode="updates"):
        if isinstance(event, dict) and "__interrupt__" in event:
            return event["__interrupt__"]
        if not isinstance(event, dict):
            continue
        for node_name, state in event.items():
            if debug:
                print(f"  [NODE] {node_name}")
            if not isinstance(state, dict):
                continue
            messages = state.get("messages") or []
            try:
                iterable = list(messages)
            except TypeError:
                iterable = [messages]
            for message in iterable:
                display.print_message(message)
            sys.stdout.flush()

    try:
        state = agent.get_state(config)
        for task in getattr(state, "tasks", ()) or ():
            interrupts = getattr(task, "interrupts", None)
            if interrupts:
                return interrupts
    except Exception:
        pass
    return None


def _handle_interrupts(interrupts: Any, spinner: Any = None) -> Command:
    first = interrupts[0]
    payload = getattr(first, "value", first)
    action_requests = payload.get("action_requests", [])
    review_configs = {
        config.get("action_name"): config for config in payload.get("review_configs", [])
    }

    decisions: list[dict[str, Any]] = []
    for action in action_requests:
        name = str(action.get("name", "unknown"))
        args = action.get("args", {}) or {}
        review = review_configs.get(name, {})
        allowed = review.get("allowed_decisions", ["approve", "reject"])
        decisions.append(get_user_decision(name, args, allowed, spinner=spinner))

    return Command(resume={"decisions": decisions})


def _last_ai_text(agent: Any, config: RunnableConfig) -> str:
    try:
        state = agent.get_state(config)
        messages = state.values.get("messages", [])
        for message in reversed(messages):
            if isinstance(message, AIMessage):
                text = message_text(message).strip()
                if text:
                    return text
    except Exception:
        pass
    return ""


def process_stream(
    agent: Any,
    input_data: Any,
    config: RunnableConfig,
    debug: bool = False,
    conversation_history: list[dict[str, Any]] | None = None,
    conversation_name: str | None = None,
    auto_save: bool = True,
    spinner: Any = None,
) -> tuple[int, list[dict[str, Any]]]:
    history = (
        list(conversation_history)
        if conversation_history
        else load_conversation_history(conversation_name)
    )
    user_content = _extract_user_content(input_data)
    if user_content:
        history = add_to_history(history, "user", user_content)

    step_logger = StepLogger()
    display = AgentDisplay(step_logger, spinner=spinner)
    turn_count = 0
    payload: Any = input_data

    try:
        while True:
            interrupts = _stream_once(agent, payload, config, debug, display)
            if not interrupts:
                break

            print()
            warning("Agent 执行已中断，需要审核工具调用")
            payload = _handle_interrupts(interrupts, spinner=spinner)
            turn_count += 1
            if turn_count > 20:
                warning("达到最大交互轮数，停止执行")
                break

        assistant_text = _last_ai_text(agent, config)
        if assistant_text:
            history = add_to_history(history, "assistant", assistant_text)
    except KeyboardInterrupt:
        warning("已取消当前执行")
    except Exception as exc:
        error(f"执行出错: {exc}")
        if debug:
            import traceback

            traceback.print_exc()

    try:
        step_logger.print_summary()
    except Exception:
        pass

    if auto_save and history:
        try:
            saved = save_conversation_history(history, conversation_name)
            print(f"对话记录已保存: {saved}")
        except Exception as exc:
            warning(f"保存对话历史失败: {exc}")

    return turn_count, history


__all__ = ["process_stream"]
