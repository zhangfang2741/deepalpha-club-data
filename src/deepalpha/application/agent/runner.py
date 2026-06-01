"""Claude API Agent 主循环"""
from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

import anthropic

from deepalpha.application.agent.prompts import SYSTEM_PROMPT
from deepalpha.application.agent.tools import TOOLS, Services, dispatch_tool


class AgentRunner:
    def __init__(self, services: Services) -> None:
        self._services = services
        self._client = anthropic.AsyncAnthropic()

    async def run(self, messages: list[dict[str, Any]]) -> AsyncGenerator[str, None]:
        while True:
            async with self._client.messages.stream(
                model="claude-sonnet-4-6",
                max_tokens=8096,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            ) as stream:
                async for text in stream.text_stream:
                    yield text
                final = await stream.get_final_message()

            if final.stop_reason == "end_turn":
                break

            tool_results: list[dict[str, Any]] = []
            for block in final.content:
                if block.type == "tool_use":
                    result = await dispatch_tool(block.name, block.input, self._services)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            messages = messages + [
                {"role": "assistant", "content": final.content},
                {"role": "user", "content": tool_results},
            ]
