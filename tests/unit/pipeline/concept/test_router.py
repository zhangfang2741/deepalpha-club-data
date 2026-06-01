import datetime
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from deepalpha.models.concept import ConceptStock, ConceptSummary
from deepalpha.pipeline.concept.api.router import router, get_cache, get_config
from deepalpha.pipeline.concept.config import ConceptPipelineConfig


@pytest.fixture
def test_config():
    return ConceptPipelineConfig(
        postgres_host="localhost", postgres_db="test", postgres_user="u", postgres_password="p",
        valkey_host="localhost", finnhub_api_key="test",
    )


@pytest.fixture
def sample_summaries():
    return [
        ConceptSummary(concept="Artificial Intelligence", etf_count=4, stock_count=120,
                       top_symbols=["NVDA", "AMD"], last_updated=datetime.date(2026, 5, 31)),
        ConceptSummary(concept="Robotics", etf_count=2, stock_count=60,
                       top_symbols=["ISRG", "ABB"], last_updated=datetime.date(2026, 5, 31)),
    ]


@pytest.fixture
def sample_stocks():
    return [
        ConceptStock(date=datetime.date(2026, 5, 31), concept="Artificial Intelligence",
                     symbol="NVDA", name="NVIDIA", etf_count=4, total_weight=20.0, etfs=["BOTZ","AIQ","IRBO","ROBT"]),
        ConceptStock(date=datetime.date(2026, 5, 31), concept="Artificial Intelligence",
                     symbol="AMD", name="AMD", etf_count=2, total_weight=8.0, etfs=["AIQ","IRBO"]),
    ]


@pytest.fixture
def mock_cache(sample_summaries, sample_stocks):
    cache = AsyncMock()
    cache.get_list = AsyncMock(return_value=sample_summaries)
    cache.get_concept = AsyncMock(return_value=sample_stocks)
    cache.set_list = AsyncMock()
    cache.set_concept = AsyncMock()
    cache.close = AsyncMock()
    return cache


@pytest.fixture
def client(test_config, mock_cache):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_config] = lambda: test_config
    app.dependency_overrides[get_cache] = lambda: mock_cache
    return TestClient(app)


def test_list_concepts_returns_all(client, sample_summaries):
    resp = client.get("/concept/list")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    concepts = [d["concept"] for d in data]
    assert "Artificial Intelligence" in concepts
    assert "Robotics" in concepts


def test_get_concept_returns_stocks(client, sample_stocks):
    resp = client.get("/concept/Artificial Intelligence")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["symbol"] == "NVDA"


def test_get_concept_filters_by_min_etf_count(client, sample_stocks):
    resp = client.get("/concept/Artificial Intelligence?min_etf_count=3")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["symbol"] == "NVDA"  # etf_count=4 passes; AMD etf_count=2 filtered out
