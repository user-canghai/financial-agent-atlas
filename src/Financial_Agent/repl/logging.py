from __future__ import annotations

import logging
import sys

from Financial_Agent.repl.colors import Colors

_CONFIGURED = False


def configure_logging(level: int = logging.INFO) -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )
    for noisy in (
        "httpx",
        "urllib3",
        "dashscope",
        "deepagents.middleware.skills",
        "mcp.client.stdio",
    ):
        logging.getLogger(noisy).setLevel(logging.CRITICAL)
    _CONFIGURED = True


def header(title: str) -> None:
    print("─" * 79)
    print(Colors.bright_white(title))
    print("─" * 79)


def info(message: str) -> None:
    print(f"{Colors.bright_cyan(message)}")


def warning(message: str) -> None:
    print(f"{Colors.bright_yellow('[WARN] ' + message)}")


def error(message: str) -> None:
    print(f"{Colors.bright_red('[ERROR] ' + message)}")


__all__ = ["configure_logging", "header", "info", "warning", "error"]
