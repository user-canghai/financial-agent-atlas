from __future__ import annotations

from typing import Any

from Financial_Agent.core.agent import setup_agent, shutdown_agent


class FinancialAgent:
    def __init__(self, conversation_name: str | None = None) -> None:
        self.conversation_name = conversation_name
        self._agent = setup_agent(conversation_name=conversation_name)

    @property
    def graph(self) -> Any:
        return self._agent

    def invoke(self, prompt: str, thread_id: str | None = None) -> Any:
        config = {
            "configurable": {
                "thread_id": thread_id or f"financial-agent-{self.conversation_name or 'default'}"
            }
        }
        return self._agent.invoke({"messages": [("user", prompt)]}, config=config)

    def close(self) -> None:
        shutdown_agent()


__all__ = ["FinancialAgent"]
