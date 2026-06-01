"""AI Agent SSE 流式端点"""
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from deepalpha.application.agent.runner import AgentRunner
from deepalpha.interface.web.deps import get_runner

router = APIRouter(prefix="/agent", tags=["agent"])


class ChatRequest(BaseModel):
    messages: list[dict]


@router.post("/stream")
async def agent_stream(
    req: ChatRequest,
    runner: Annotated[AgentRunner, Depends(get_runner)],
) -> EventSourceResponse:
    async def event_generator():
        async for text in runner.run(req.messages):
            yield {"data": text}

    return EventSourceResponse(event_generator())
