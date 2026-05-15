"""Sentiment data endpoint"""
from fastapi import APIRouter, Header, Query
from typing import Optional

router = APIRouter()


@router.get("/sentiment")
async def get_sentiment(
    symbols: str = Query(...),
    data_type: str = Query("all"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    x_api_token: str = Header(...),
):
    """Query sentiment data from Elasticsearch"""
    return {"message": "Not implemented"}