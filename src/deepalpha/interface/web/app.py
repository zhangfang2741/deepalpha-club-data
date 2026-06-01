"""FastAPI 应用入口"""
from fastapi import FastAPI

from deepalpha.interface.web.deps import lifespan
from deepalpha.interface.web.routers import agent, concept, market

app = FastAPI(title="DeepAlpha API", version="0.1.0", lifespan=lifespan)

app.include_router(concept.router, prefix="/api/v1")
app.include_router(market.router, prefix="/api/v1")
app.include_router(agent.router, prefix="/api/v1")
