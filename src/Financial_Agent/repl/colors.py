from __future__ import annotations

import os
import sys

_COLOR_ENABLED = sys.stdout.isatty() and os.getenv("NO_COLOR") is None


class Colors:
    RESET = "\033[0m" if _COLOR_ENABLED else ""
    BOLD = "\033[1m" if _COLOR_ENABLED else ""
    RED = "\033[31m" if _COLOR_ENABLED else ""
    GREEN = "\033[32m" if _COLOR_ENABLED else ""
    YELLOW = "\033[33m" if _COLOR_ENABLED else ""
    BLUE = "\033[34m" if _COLOR_ENABLED else ""
    CYAN = "\033[36m" if _COLOR_ENABLED else ""
    BRIGHT_CYAN = "\033[96m" if _COLOR_ENABLED else ""
    BRIGHT_WHITE = "\033[97m" if _COLOR_ENABLED else ""
    BRIGHT_YELLOW = "\033[93m" if _COLOR_ENABLED else ""
    BRIGHT_RED = "\033[91m" if _COLOR_ENABLED else ""
    BRIGHT_GREEN = "\033[92m" if _COLOR_ENABLED else ""

    @staticmethod
    def color(code: str, text: str) -> str:
        return f"{code}{text}{Colors.RESET}" if _COLOR_ENABLED else text

    @staticmethod
    def bright_cyan(text: str) -> str:
        return Colors.color(Colors.BRIGHT_CYAN, text)

    @staticmethod
    def bright_white(text: str) -> str:
        return Colors.color(Colors.BRIGHT_WHITE, text)

    @staticmethod
    def bright_yellow(text: str) -> str:
        return Colors.color(Colors.BRIGHT_YELLOW, text)

    @staticmethod
    def bright_red(text: str) -> str:
        return Colors.color(Colors.BRIGHT_RED, text)

    @staticmethod
    def bright_green(text: str) -> str:
        return Colors.color(Colors.BRIGHT_GREEN, text)


class Icons:
    INFO = "ℹ"
    OK = "✓"
    WARN = "⚠"
    ERROR = "✗"
    TOOL = "m"


__all__ = ["Colors", "Icons"]
