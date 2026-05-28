"""Price data endpoint"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Query
import polars as pl

from deepalpha.api.api_schemas import PriceResponse

router = APIRouter()


@router.get("/price")
async def get_price(
    symbols: str = Query(..., description="Comma-separated symbols"),
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    fields: Optional[str] = Query(None, description="Fields to return"),
    format: str = Query("arrow", description="Response format"),
) -> PriceResponse:
    """Query historical price data."""
    df = pl.DataFrame({
        "date": [start_date],
        "symbol": ["AAPL"],
        "open": [185.0],
        "high": [186.0],
        "low": [184.0],
        "close": [185.5],
        "volume": [50000000],
    })

    return PriceResponse(
        count=df.shape[0],
        data=df.to_dicts(),
        format=format,
    )
