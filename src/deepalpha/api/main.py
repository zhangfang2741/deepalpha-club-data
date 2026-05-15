"""DeepAlpha Data API Service"""
from fastapi import FastAPI

from deepalpha.api.routes import price, financials, sentiment, universe

app = FastAPI(
    title="DeepAlpha Data API",
    description="L3 Storage Data Query Interface",
    version="0.1.0",
)

app.include_router(price.router, prefix="/v1", tags=["price"])
app.include_router(financials.router, prefix="/v1", tags=["financials"])
app.include_router(sentiment.router, prefix="/v1", tags=["sentiment"])
app.include_router(universe.router, prefix="/v1", tags=["universe"])


@app.get("/health")
async def health_check():
    return {"status": "healthy"}