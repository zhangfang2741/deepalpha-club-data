"""Financial data endpoint"""
from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter()


@router.get("/financials")
async def get_financials(
    symbols: str = Query(...),
    as_of_date: str = Query(...),
    fields: Optional[str] = Query(None),
):
    """Query financial data with PIT correction"""
    return {"message": "Not implemented"}
