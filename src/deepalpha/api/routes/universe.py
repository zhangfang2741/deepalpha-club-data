"""Universe endpoint"""
from fastapi import APIRouter, Query

router = APIRouter()


@router.get("/universe")
async def get_universe(
    market: str = Query("US"),
):
    """Get list of available symbols"""
    return {
        "market": market,
        "symbols": ["AAPL", "TSLA", "MSFT"],
        "count": 3,
        "last_updated": "2024-01-02",
    }
