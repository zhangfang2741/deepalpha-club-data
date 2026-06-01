"""MiniMax Agent 主循环（LangGraph ReAct）"""
from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from deepalpha.application.agent.prompts import SYSTEM_PROMPT
from deepalpha.application.agent.tools import Services, build_tools

_MINIMAX_BASE_URL = "https://api.minimax.io/v1"
_MODEL = "MiniMax-Text-01"


class AgentRunner:
    def __init__(self, services: Services) -> None:
        model = ChatOpenAI(
            model=_MODEL,
            api_key=os.environ["MINIMAX_API_KEY"],
            base_url=_MINIMAX_BASE_URL,
            streaming=True,
        )
        self._graph = create_react_agent(
            model,
            tools=build_tools(services),
            state_modifier=SYSTEM_PROMPT,
        )

    async def run(self, messages: list[dict[str, Any]]) -> AsyncGenerator[str, None]:
        lc_messages = _to_lc_messages(messages)
        async for event in self._graph.astream_events(
            {"messages": lc_messages},
            version="v2",
        ):
            if event["event"] == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                content = getattr(chunk, "content", "")
                if isinstance(content, str) and content:
                    yield content


def _to_lc_messages(messages: list[dict[str, Any]]) -> list:
    result = []
    for m in messages:
        role = m.get("role", "")
        content = m.get("content", "")
        if not isinstance(content, str):
            content = ""
        if role == "user":
            result.append(HumanMessage(content=content))
        elif role == "assistant" and content:
            result.append(AIMessage(content=content))
    return result
