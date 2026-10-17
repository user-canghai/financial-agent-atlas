from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from Financial_Agent.mcp.mcp import get_enabled_servers


@dataclass
class MCPServerStatus:
    name: str
    command: str
    args: list[str]
    available: bool
    reason: str = ""


class MCPHost:
    def __init__(self, config: dict[str, dict[str, Any]] | None = None) -> None:
        self.config = config or get_enabled_servers()
        self._processes: dict[str, subprocess.Popen[bytes]] = {}

    def status(self) -> list[MCPServerStatus]:
        statuses: list[MCPServerStatus] = []
        for name, server_config in self.config.items():
            command = str(server_config.get("command", ""))
            args = [str(arg) for arg in server_config.get("args", [])]
            if not command:
                statuses.append(MCPServerStatus(name, command, args, False, "未配置 command"))
                continue
            if Path(command).exists():
                statuses.append(MCPServerStatus(name, command, args, True))
                continue
            resolved = shutil.which(command)
            statuses.append(
                MCPServerStatus(
                    name,
                    command,
                    args,
                    resolved is not None,
                    "" if resolved else "命令不在 PATH 中",
                )
            )
        return statuses

    def start(self, server_name: str) -> subprocess.Popen[bytes]:
        if server_name in self._processes and self._processes[server_name].poll() is None:
            return self._processes[server_name]
        server_config = self.config[server_name]
        process = subprocess.Popen(
            [str(server_config["command"]), *[str(arg) for arg in server_config.get("args", [])]],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self._processes[server_name] = process
        return process

    def stop(self, server_name: str) -> None:
        process = self._processes.pop(server_name, None)
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

    def stop_all(self) -> None:
        for name in list(self._processes):
            self.stop(name)


__all__ = ["MCPHost", "MCPServerStatus"]
