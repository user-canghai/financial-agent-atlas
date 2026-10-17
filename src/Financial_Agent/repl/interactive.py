from __future__ import annotations

import os
import sys
import threading
import time
import uuid

from langchain_core.runnables.config import RunnableConfig

from Financial_Agent.config import Config
from Financial_Agent.core.agent import setup_agent, shutdown_agent
from Financial_Agent.memory import load_conversation_history, save_conversation_history
from Financial_Agent.repl.colors import Colors
from Financial_Agent.repl.logging import configure_logging, header, warning
from Financial_Agent.repl.processor import process_stream


class Spinner:
    def __init__(self, message: str = "正在思考") -> None:
        self.message = message
        self.enabled = sys.stdout.isatty()
        self._running = False
        self._paused = False
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def _run(self) -> None:
        frames = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        tip = "长时间无响应建议回车↩︎刷新状态或 Ctrl+C 退出重连"
        index = 0
        while self._running:
            with self._lock:
                paused = self._paused
            if not paused:
                frame = frames[index % len(frames)]
                sys.stdout.write(
                    f"\r{Colors.bright_cyan(frame)} {self.message}... "
                    f"{Colors.bright_yellow('[' + tip + ']')}"
                )
                sys.stdout.flush()
                index += 1
            time.sleep(0.08)
        sys.stdout.write("\r" + " " * 110 + "\r")
        sys.stdout.flush()

    def start(self) -> None:
        if not self.enabled:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if not self.enabled:
            return
        self._running = False
        if self._thread:
            self._thread.join(timeout=1)
            self._thread = None

    def pause(self) -> None:
        with self._lock:
            self._paused = True

    def resume(self) -> None:
        with self._lock:
            self._paused = False


def run_single_chat(
    prompt: str,
    debug: bool = False,
    conversation_name: str | None = None,
) -> None:
    configure_logging()
    header("Agent 单次交互")
    print(f"提示词: {prompt}")
    if conversation_name:
        print(f"对话名称: {conversation_name}")
    print()

    agent = setup_agent(conversation_name=conversation_name)
    config: RunnableConfig = {
        "configurable": {
            "thread_id": f"single-chat-{conversation_name or 'default'}-{uuid.uuid4().hex[:8]}"
        }
    }

    try:
        process_stream(
            agent,
            {"messages": [("user", prompt)]},
            config,
            debug=debug,
            conversation_name=conversation_name,
            auto_save=True,
        )
    finally:
        shutdown_agent()


def run_interactive_mode(
    debug: bool = False,
    conversation_name: str | None = None,
) -> None:
    configure_logging()
    agent = setup_agent(conversation_name=conversation_name)

    header("Agent 交互模式" + (" (DEBUG)" if debug else ""))
    history_file = Config.get_conversation_history_file(conversation_name)
    try:
        display_path = os.path.relpath(history_file, start=Config.get_root_dir())
    except ValueError:
        display_path = str(history_file)
    print(f"{Colors.bright_white('对话记录:')} {display_path}")
    print()
    print(
        f"{Colors.bright_yellow('提示:')} 输入 "
        f"{Colors.bright_white('exit/quit')} 退出，"
        f"{Colors.bright_white('help')} 查看帮助"
    )
    print()

    config: RunnableConfig = {
        "configurable": {"thread_id": f"interactive-{conversation_name or 'default'}"}
    }
    show_debug = debug
    history = load_conversation_history(conversation_name)

    while True:
        try:
            user_input = input(f"{Colors.bright_yellow('You:')} ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            user_input = "exit"

        lowered = user_input.lower()
        if lowered in {"exit", "quit", "q"}:
            if history:
                try:
                    saved = save_conversation_history(history, conversation_name)
                    print(f"{Colors.bright_green('✓')} 对话历史已保存: {saved}")
                except Exception as exc:
                    warning(f"保存对话历史失败: {exc}")
            shutdown_agent()
            print("再见！")
            break

        if lowered == "help":
            print()
            print(Colors.bright_cyan("可用命令:"))
            print(f"  {Colors.bright_white('help')}          - 显示此帮助信息")
            print(f"  {Colors.bright_white('exit/quit/q')}   - 退出交互模式")
            print(f"  {Colors.bright_white('node')}          - 切换节点显示 (debug 模式)")
            print()
            print(Colors.bright_cyan("快捷键:"))
            print("  上下箭头 - 浏览历史输入")
            print("  Ctrl+C   - 取消当前输入")
            print()
            continue

        if lowered == "node":
            show_debug = not show_debug
            print(f"节点显示: {'开启' if show_debug else '关闭'}")
            continue

        if not user_input:
            continue

        print()
        spinner = Spinner("正在思考")
        spinner.start()
        try:
            _, history = process_stream(
                agent,
                {"messages": [("user", user_input)]},
                config,
                debug=show_debug,
                conversation_history=history,
                conversation_name=conversation_name,
                auto_save=False,
                spinner=spinner,
            )
        finally:
            spinner.stop()

    print()


__all__ = ["run_single_chat", "run_interactive_mode", "Spinner"]
