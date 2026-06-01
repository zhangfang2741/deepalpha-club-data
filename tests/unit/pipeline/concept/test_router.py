import datetime
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock

from deepalpha.domain.concept.models import ConceptStock, ConceptSummary
from deepalpha.interface.web.routers.concept import router
from deepalpha.interface.web.deps import get_services
from deepalpha.application.agent.tools import Services


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
def mock_concept_svc(sample_summaries, sample_stocks):
    svc = AsyncMock()
    svc.list_summaries = AsyncMock(return_value=sample_summaries)
    svc.get_concept = AsyncMock(return_value=sample_stocks)
    svc.get_concept_history = AsyncMock(return_value=sample_stocks)
    return svc


@pytest.fixture
def mock_services(mock_concept_svc):
    services = AsyncMock(spec=Services)
    services.concept = mock_concept_svc
    return services


@pytest.fixture
def client(mock_services):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_services] = lambda: mock_services
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
    assert data[0]["symbol"] == "NVDA"  # etf_count=4 通过；AMD etf_count=2 被过滤
