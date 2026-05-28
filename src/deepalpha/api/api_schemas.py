# src/deepalpha/api/api_schemas.py
"""Pydantic schemas for API request validation and response serialization."""
from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class PriceQuery(BaseModel):
    """Query parameters for price data requests."""
    symbols: str = Field(..., description="Comma-separated stock symbols")
    start_date: date = Field(..., description="Start date YYYY-MM-DD")
    end_date: date = Field(..., description="End date YYYY-MM-DD")
    fields: Optional[str] = Field(None, description="Comma-separated fields to return")
    format: str = Field("arrow", description="Response format: arrow or json")


class PriceResponse(BaseModel):
    """Response body for price data endpoints."""
    count: int
    data: list[dict]
    format: str
