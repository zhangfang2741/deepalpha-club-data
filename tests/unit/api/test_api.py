"""Tests for Data API endpoints"""
import pytest
from fastapi.testclient import TestClient
from deepalpha.api.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_health_check(self):
        """Health endpoint returns healthy status"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestPriceEndpoint:
    """Test /v1/price endpoint"""

    def test_price_query_params(self):
        """Price endpoint validates query parameters"""
        response = client.get(
            "/v1/price",
            params={
                "symbols": "AAPL,TSLA",
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1


class TestUniverseEndpoint:
    """Test /v1/universe endpoint"""

    def test_get_universe(self):
        """Universe endpoint returns symbol list"""
        response = client.get(
            "/v1/universe",
            params={"market": "US"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["market"] == "US"
        assert len(data["symbols"]) == 3
