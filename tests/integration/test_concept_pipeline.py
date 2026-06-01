"""
概念股池 Pipeline 集成测试

覆盖整个 pipeline 的端到端流程：
1. Models 层 - 数据模型验证
2. Config 层 - 配置加载与环境变量
3. ETFdb Scraper - HTML 解析与抓取流程
4. Finnhub Loader - AUM 过滤、持仓聚合、CSV 兜底
5. Database 层 - DB 读写、upsert、查询
6. Cache 层 - Valkey 读写
7. Tasks - build_concept_map（月度）、update_holdings（日度）
8. API Router - FastAPI 端点集成

所有测试使用 mock，避免真实 API 调用。
"""

import asyncio
import datetime
import json
from collections.abc import AsyncGenerator
from functools import lru_cache
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from deepalpha.models.concept import ConceptEtfMap, ConceptStock, ConceptSummary
from deepalpha.pipeline.concept.api.router import router, get_cache, get_config
from deepalpha.pipeline.concept.cache import ConceptCache
from deepalpha.pipeline.concept.config import ConceptPipelineConfig
from deepalpha.pipeline.concept.db import ConceptDb, _CREATE_TABLES_SQL
from deepalpha.pipeline.concept.etfdb_scraper import (
    ConceptEtfCandidate,
    _parse_etf_symbols,
    _parse_theme_slugs,
    scrape_concept_etf_candidates,
)
from deepalpha.pipeline.concept.finnhub_loader import (
    aggregate_holdings,
    fetch_holdings_with_fallback,
    filter_etfs_by_aum,
)
from deepalpha.pipeline.concept.tasks.build_concept_map import run as build_concept_map_run
from deepalpha.pipeline.concept.tasks.update_holdings import run as update_holdings_run


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def test_config() -> ConceptPipelineConfig:
    """测试用配置"""
    return ConceptPipelineConfig(
        postgres_host="localhost",
        postgres_port=5432,
        postgres_db="test_db",
        postgres_user="test_user",
        postgres_password="test_pass",
        postgres_ssl=False,
        valkey_host="localhost",
        valkey_port=6379,
        valkey_password="",
        valkey_ssl=False,
        finnhub_api_key="test_finnhub_key",
        concept_cache_ttl=172800,
        concept_aum_threshold_million=100.0,
    )


@pytest.fixture
def mock_valkey() -> AsyncMock:
    """模拟 Valkey 客户端"""
    client = AsyncMock()
    client.get = AsyncMock(return_value=None)
    client.set = AsyncMock()
    client.aclose = AsyncMock()
    return client


@pytest.fixture
def mock_cache(mock_valkey: AsyncMock) -> ConceptCache:
    """使用 mock valkey 的 ConceptCache 实例"""
    with patch("deepalpha.infrastructure.cache.concept_cache.valkey_asyncio.Valkey", return_value=mock_valkey):
        return ConceptCache(host="localhost", port=6379, password="", ssl=False)


def _make_mock_pool(mock_conn: AsyncMock) -> MagicMock:
    """构造模拟 asyncpg Pool"""
    pool = MagicMock()
    pool.close = AsyncMock()
    acm = MagicMock()
    acm.__aenter__ = AsyncMock(return_value=mock_conn)
    acm.__aexit__ = AsyncMock(return_value=False)
    pool.acquire.return_value = acm
    return pool


@pytest.fixture
def mock_db_conn() -> AsyncMock:
    """模拟数据库连接"""
    conn = AsyncMock()
    conn.execute = AsyncMock()
    conn.executemany = AsyncMock()
    conn.fetch = AsyncMock(return_value=[])
    return conn


@pytest.fixture
def mock_db_pool(mock_db_conn: AsyncMock) -> MagicMock:
    """模拟数据库连接池"""
    return _make_mock_pool(mock_db_conn)


@pytest.fixture
def sample_etf_maps() -> list[ConceptEtfMap]:
    """样例 ETF 映射数据"""
    today = datetime.date(2026, 5, 31)
    return [
        ConceptEtfMap(
            concept="Artificial Intelligence",
            etf_symbol="BOTZ",
            etf_name="Global X Robotics & AI",
            aum_million=2500.0,
            etfdb_slug="artificial-intelligence-etfs",
            updated_at=today,
        ),
        ConceptEtfMap(
            concept="Artificial Intelligence",
            etf_symbol="AIQ",
            etf_name="Global X AI & Technology",
            aum_million=1800.0,
            etfdb_slug="artificial-intelligence-etfs",
            updated_at=today,
        ),
        ConceptEtfMap(
            concept="Robotics",
            etf_symbol="BOTZ",
            etf_name="Global X Robotics & AI",
            aum_million=2500.0,
            etfdb_slug="robotics-etfs",
            updated_at=today,
        ),
    ]


@pytest.fixture
def sample_holdings() -> dict[str, list[dict[str, Any]]]:
    """样例 ETF 持仓数据"""
    return {
        "BOTZ": [
            {"symbol": "NVDA", "name": "NVIDIA Corp", "percent": 8.5},
            {"symbol": "ISRG", "name": "Intuitive Surgical", "percent": 5.2},
            {"symbol": "ABB", "name": "ABB Ltd", "percent": 4.8},
        ],
        "AIQ": [
            {"symbol": "NVDA", "name": "NVIDIA Corp", "percent": 6.0},
            {"symbol": "AMD", "name": "AMD Inc", "percent": 4.0},
            {"symbol": "MSFT", "name": "Microsoft", "percent": 3.5},
        ],
    }


@pytest.fixture
def sample_stocks() -> list[ConceptStock]:
    """样例成分股数据"""
    today = datetime.date(2026, 5, 31)
    return [
        ConceptStock(
            date=today,
            concept="Artificial Intelligence",
            symbol="NVDA",
            name="NVIDIA Corp",
            etf_count=2,
            total_weight=14.5,
            etfs=["BOTZ", "AIQ"],
        ),
        ConceptStock(
            date=today,
            concept="Artificial Intelligence",
            symbol="AMD",
            name="AMD Inc",
            etf_count=1,
            total_weight=4.0,
            etfs=["AIQ"],
        ),
        ConceptStock(
            date=today,
            concept="Robotics",
            symbol="ISRG",
            name="Intuitive Surgical",
            etf_count=1,
            total_weight=5.2,
            etfs=["BOTZ"],
        ),
    ]


@pytest.fixture
def sample_summaries() -> list[ConceptSummary]:
    """样例概念摘要数据"""
    today = datetime.date(2026, 5, 31)
    return [
        ConceptSummary(
            concept="Artificial Intelligence",
            etf_count=2,
            stock_count=2,
            top_symbols=["NVDA", "AMD"],
            last_updated=today,
        ),
        ConceptSummary(
            concept="Robotics",
            etf_count=1,
            stock_count=1,
            top_symbols=["ISRG"],
            last_updated=today,
        ),
    ]


@pytest.fixture
def mock_finnhub_client() -> AsyncMock:
    """模拟 Finnhub 客户端"""
    client = AsyncMock()
    client.get_etf_profile = AsyncMock(return_value={"name": "Test ETF", "mktCap": 2_500_000_000.0})
    client.get_etf_holdings = AsyncMock(return_value=[
        {"symbol": "NVDA", "name": "NVIDIA", "percent": 8.5},
    ])
    return client


# =============================================================================
# 1. Models 层测试
# =============================================================================


class TestModels:
    """数据模型验证测试"""

    def test_concept_etf_map_full_creation(self):
        """完整创建 ConceptEtfMap"""
        today = datetime.date(2026, 5, 31)
        m = ConceptEtfMap(
            concept="AI",
            etf_symbol="BOTZ",
            etf_name="Global X Robotics",
            aum_million=2500.0,
            etfdb_slug="ai-etfs",
            updated_at=today,
        )
        assert m.concept == "AI"
        assert m.etf_symbol == "BOTZ"
        assert m.aum_million == 2500.0
        assert m.updated_at == today

    def test_concept_etf_map_partial_creation(self):
        """部分字段创建 ConceptEtfMap"""
        today = datetime.date(2026, 5, 31)
        m = ConceptEtfMap(concept="AI", etf_symbol="BOTZ", updated_at=today)
        assert m.etf_name is None
        assert m.aum_million is None
        assert m.etfdb_slug is None

    def test_concept_stock_etfs_list(self):
        """ConceptStock 的 etfs 字段"""
        today = datetime.date(2026, 5, 31)
        s = ConceptStock(
            date=today,
            concept="AI",
            symbol="NVDA",
            etf_count=3,
            total_weight=15.5,
            etfs=["BOTZ", "AIQ", "IRBO"],
        )
        assert len(s.etfs) == 3
        assert "BOTZ" in s.etfs

    def test_concept_stock_json_serialization(self):
        """ConceptStock JSON 序列化"""
        today = datetime.date(2026, 5, 31)
        s = ConceptStock(
            date=today,
            concept="AI",
            symbol="NVDA",
            etf_count=2,
            total_weight=14.5,
            etfs=["BOTZ", "AIQ"],
        )
        data = s.model_dump(mode="json")
        assert data["symbol"] == "NVDA"
        assert data["etfs"] == ["BOTZ", "AIQ"]

    def test_concept_summary_top_symbols(self):
        """ConceptSummary 的 top_symbols 限制为 5"""
        today = datetime.date(2026, 5, 31)
        s = ConceptSummary(
            concept="AI",
            etf_count=4,
            stock_count=100,
            top_symbols=["NVDA", "AMD", "MSFT", "GOOGL", "META"],
            last_updated=today,
        )
        assert len(s.top_symbols) == 5

    def test_concept_summary_partial_creation(self):
        """部分字段创建 ConceptSummary"""
        today = datetime.date(2026, 5, 31)
        s = ConceptSummary(
            concept="AI",
            etf_count=10,
            stock_count=50,
            top_symbols=["A", "B"],
            last_updated=today,
        )
        assert s.concept == "AI"


# =============================================================================
# 2. Config 层测试
# =============================================================================


class TestConfig:
    """配置加载测试"""

    def test_asyncpg_dsn_without_ssl(self, test_config: ConceptPipelineConfig):
        """DSN 拼接（无 SSL）"""
        dsn = test_config.asyncpg_dsn()
        assert "postgresql://" in dsn
        assert "localhost:5432" in dsn
        assert "test_db" in dsn
        assert "sslmode=require" not in dsn

    def test_asyncpg_dsn_with_ssl(self):
        """DSN 拼接（带 SSL）"""
        config = ConceptPipelineConfig(
            postgres_host="pg.example.com",
            postgres_db="mydb",
            postgres_user="user",
            postgres_password="pass",
            postgres_ssl=True,
        )
        dsn = config.asyncpg_dsn()
        assert "sslmode=require" in dsn

    def test_config_defaults(self):
        """配置默认值"""
        config = ConceptPipelineConfig()
        assert config.valkey_port == 6379
        assert config.postgres_port == 5432
        assert config.concept_cache_ttl == 172800
        assert config.concept_aum_threshold_million == 100.0


# =============================================================================
# 3. ETFdb Scraper 测试
# =============================================================================


class TestEtfdbScraper:
    """ETFdb 抓取器测试"""

    THEMES_HTML = """
    <html><body>
      <a href="/type/artificial-intelligence-etfs/">Artificial Intelligence</a>
      <a href="/type/robotics-etfs/">Robotics</a>
      <a href="/type/cybersecurity-etfs/">Cybersecurity</a>
      <a href="/other-page/">Ignore This</a>
    </body></html>
    """

    ETF_LIST_HTML = """
    <html><body>
      <a href="/etf/BOTZ/">BOTZ</a>
      <a href="/etf/AIQ/">AIQ</a>
      <a href="/etf/IRBO/">IRBO</a>
      <a href="/other-link/">Ignore</a>
    </body></html>
    """

    def test_parse_theme_slugs(self):
        """解析主题 slug"""
        result = _parse_theme_slugs(self.THEMES_HTML)
        assert "Artificial Intelligence" in result
        assert result["Artificial Intelligence"] == "artificial-intelligence-etfs"
        assert "Robotics" in result
        assert result["Robotics"] == "robotics-etfs"
        assert "Cybersecurity" in result
        assert "Ignore This" not in result

    def test_parse_etf_symbols(self):
        """解析 ETF 代码列表"""
        result = _parse_etf_symbols(self.ETF_LIST_HTML)
        assert "BOTZ" in result
        assert "AIQ" in result
        assert "IRBO" in result
        assert len(result) == 3

    def test_parse_etf_symbols_uppercase(self):
        """ETF 代码自动转大写"""
        html = '<html><body><a href="/etf/botz/">botz</a></body></html>'
        result = _parse_etf_symbols(html)
        assert "BOTZ" in result

    def test_parse_etf_symbols_deduplicates(self):
        """ETF 代码去重"""
        html = """
        <html><body>
          <a href="/etf/BOTZ/">BOTZ</a>
          <a href="/etf/BOTZ/">BOTZ</a>
        </body></html>
        """
        result = _parse_etf_symbols(html)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_scrape_concept_etf_candidates_flow(self):
        """端到端抓取流程（mock HTTP）"""
        # 主题列表响应
        mock_list_response = AsyncMock()
        mock_list_response.text = self.THEMES_HTML
        mock_list_response.raise_for_status = MagicMock()

        # 主题详情响应（每个主题返回 ETF 列表）
        mock_etf_response = AsyncMock()
        mock_etf_response.text = self.ETF_LIST_HTML
        mock_etf_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        
        async def mock_get(url, **kwargs):
            if "/etfs/themes/" in url:
                return mock_list_response
            return mock_etf_response
        mock_client.get = mock_get
        mock_client.aclose = AsyncMock()

        with patch("deepalpha.infrastructure.providers.etfdb.scraper.httpx.AsyncClient", return_value=mock_client):
            with patch("asyncio.sleep", AsyncMock()):
                candidates = await scrape_concept_etf_candidates(delay=0.0)

        assert len(candidates) == 9  # 3 个主题，每个主题 3 个 ETF


# =============================================================================
# 4. Finnhub Loader 测试
# =============================================================================


class TestFinnhubLoader:
    """Finnhub 加载器测试"""

    @pytest.mark.asyncio
    async def test_filter_etfs_by_aum_passes_large(self, mock_finnhub_client: AsyncMock):
        """AUM 过滤 - 通过大市值 ETF"""
        candidates = [
            ConceptEtfCandidate(concept="AI", etf_symbol="BOTZ", etfdb_slug="ai-etfs")
        ]
        result = await filter_etfs_by_aum(candidates, mock_finnhub_client, aum_threshold_million=100.0)
        assert len(result) == 1
        assert result[0].etf_symbol == "BOTZ"
        assert result[0].aum_million == pytest.approx(2500.0)

    @pytest.mark.asyncio
    async def test_filter_etfs_by_aum_blocks_small(self, mock_finnhub_client: AsyncMock):
        """AUM 过滤 - 过滤小市值 ETF"""
        mock_finnhub_client.get_etf_profile = AsyncMock(
            return_value={"name": "Small ETF", "mktCap": 50_000_000.0}
        )
        candidates = [
            ConceptEtfCandidate(concept="AI", etf_symbol="SMALL", etfdb_slug="ai-etfs")
        ]
        result = await filter_etfs_by_aum(candidates, mock_finnhub_client, aum_threshold_million=100.0)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_filter_etfs_by_aum_handles_missing_mktcap(self, mock_finnhub_client: AsyncMock):
        """AUM 过滤 - 处理缺失 mktCap"""
        mock_finnhub_client.get_etf_profile = AsyncMock(
            return_value={"name": "Unknown ETF"}
        )
        candidates = [
            ConceptEtfCandidate(concept="AI", etf_symbol="UNKNOWN", etfdb_slug="ai-etfs")
        ]
        result = await filter_etfs_by_aum(candidates, mock_finnhub_client, aum_threshold_million=100.0)
        assert len(result) == 1  # 无 mktCap 也通过

    @pytest.mark.asyncio
    async def test_filter_etfs_by_aum_handles_error(self, mock_finnhub_client: AsyncMock):
        """AUM 过滤 - 异常处理"""
        mock_finnhub_client.get_etf_profile = AsyncMock(side_effect=Exception("API Error"))
        candidates = [
            ConceptEtfCandidate(concept="AI", etf_symbol="ERR", etfdb_slug="ai-etfs")
        ]
        result = await filter_etfs_by_aum(candidates, mock_finnhub_client)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_filter_etfs_by_aum_deduplicates(self, mock_finnhub_client: AsyncMock):
        """AUM 过滤 - 同一 ETF 去重"""
        candidates = [
            ConceptEtfCandidate(concept="AI", etf_symbol="BOTZ", etfdb_slug="ai-etfs"),
            ConceptEtfCandidate(concept="Robotics", etf_symbol="BOTZ", etfdb_slug="robotics-etfs"),
        ]
        result = await filter_etfs_by_aum(candidates, mock_finnhub_client)
        assert len(result) == 1  # BOTZ 只出现一次

    @pytest.mark.asyncio
    async def test_aggregate_holdings_basic(self, sample_etf_maps, sample_holdings):
        """持仓聚合 - 基本功能"""
        today = datetime.date(2026, 5, 31)
        result = await aggregate_holdings(sample_etf_maps, sample_holdings, date=today)

        nvda = next((s for s in result if s.symbol == "NVDA"), None)
        assert nvda is not None
        assert nvda.etf_count == 2  # BOTZ + AIQ
        assert nvda.total_weight == pytest.approx(14.5)  # 8.5 + 6.0
        assert set(nvda.etfs) == {"BOTZ", "AIQ"}

    @pytest.mark.asyncio
    async def test_aggregate_holdings_single_etf(self, sample_etf_maps, sample_holdings):
        """持仓聚合 - 单个 ETF"""
        today = datetime.date(2026, 5, 31)
        holdings = {"BOTZ": sample_holdings["BOTZ"]}
        result = await aggregate_holdings(sample_etf_maps[:1], holdings, date=today)

        assert len(result) == 3
        nvda = next((s for s in result if s.symbol == "NVDA"), None)
        assert nvda.etf_count == 1

    @pytest.mark.asyncio
    async def test_aggregate_holdings_empty_holdings(self):
        """持仓聚合 - 空持仓"""
        today = datetime.date(2026, 5, 31)
        etf_maps = [ConceptEtfMap(concept="AI", etf_symbol="BOTZ", updated_at=today)]
        holdings = {"BOTZ": []}
        result = await aggregate_holdings(etf_maps, holdings, date=today)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_fetch_holdings_with_fallback_success(self):
        """Finnhub 成功时返回持仓"""
        mock_client = AsyncMock()
        mock_client.get_etf_holdings = AsyncMock(return_value=[
            {"symbol": "NVDA", "name": "NVIDIA", "percent": 8.5}
        ])
        result = await fetch_holdings_with_fallback("BOTZ", mock_client)
        assert len(result) == 1
        assert result[0]["symbol"] == "NVDA"

    @pytest.mark.asyncio
    async def test_fetch_holdings_with_fallback_csv_fallback(self):
        """Finnhub 失败时使用 CSV 兜底"""
        mock_client = AsyncMock()
        mock_client.get_etf_holdings = AsyncMock(side_effect=Exception("Finnhub Error"))

        mock_csv_response = AsyncMock()
        mock_csv_response.text = "Ticker,Name,Weight (%)\nNVDA,NVIDIA,8.5\n"
        mock_csv_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient", return_value=mock_client):
            with patch("httpx.AsyncClient.get", AsyncMock(return_value=mock_csv_response)):
                result = await fetch_holdings_with_fallback("BOTZ", mock_client)

        assert len(result) == 1
        assert result[0]["symbol"] == "NVDA"

    @pytest.mark.asyncio
    async def test_fetch_holdings_with_fallback_no_fallback(self):
        """Finnhub 失败且无 CSV 兜底"""
        mock_client = AsyncMock()
        mock_client.get_etf_holdings = AsyncMock(side_effect=Exception("Finnhub Error"))
        result = await fetch_holdings_with_fallback("UNKNOWN_ETF", mock_client)
        assert result == []


# =============================================================================
# 5. Database 层测试
# =============================================================================


class TestDatabase:
    """数据库操作测试"""

    @pytest.mark.asyncio
    async def test_db_creates_tables_on_init(self, mock_db_conn: AsyncMock, mock_db_pool: MagicMock):
        """__aenter__ 时创建表"""
        with patch("asyncpg.create_pool", AsyncMock(return_value=mock_db_pool)):
            async with ConceptDb("postgresql://test") as db:
                pass
        mock_db_conn.execute.assert_called()

    @pytest.mark.asyncio
    async def test_upsert_etf_map(self, mock_db_conn: AsyncMock, mock_db_pool: MagicMock):
        """upsert_etf_map 操作"""
        records = [
            ConceptEtfMap(
                concept="AI",
                etf_symbol="BOTZ",
                etf_name="Global X",
                aum_million=2500.0,
                etfdb_slug="ai-etfs",
                updated_at=datetime.date(2026, 5, 31),
            )
        ]
        with patch("asyncpg.create_pool", AsyncMock(return_value=mock_db_pool)):
            async with ConceptDb("postgresql://test") as db:
                await db.upsert_etf_map(records)
        mock_db_conn.executemany.assert_called()

    @pytest.mark.asyncio
    async def test_upsert_stocks_serializes_etfs(self, mock_db_conn: AsyncMock, mock_db_pool: MagicMock):
        """upsert_stocks 序列化 etfs 为逗号分隔"""
        records = [
            ConceptStock(
                date=datetime.date(2026, 5, 31),
                concept="AI",
                symbol="NVDA",
                etf_count=2,
                total_weight=14.5,
                etfs=["BOTZ", "AIQ"],
            )
        ]
        with patch("asyncpg.create_pool", AsyncMock(return_value=mock_db_pool)):
            async with ConceptDb("postgresql://test") as db:
                await db.upsert_stocks(records)

        call_args = mock_db_conn.executemany.call_args
        rows = call_args[0][1]
        assert rows[0][6] == "BOTZ,AIQ"

    @pytest.mark.asyncio
    async def test_load_etf_map(self, mock_db_conn: AsyncMock, mock_db_pool: MagicMock):
        """load_etf_map 读取"""
        mock_db_conn.fetch = AsyncMock(return_value=[
            {
                "concept": "AI",
                "etf_symbol": "BOTZ",
                "etf_name": "Global X",
                "aum_million": 2500.0,
                "etfdb_slug": "ai-etfs",
                "updated_at": datetime.date(2026, 5, 31),
            }
        ])
        with patch("asyncpg.create_pool", AsyncMock(return_value=mock_db_pool)):
            async with ConceptDb("postgresql://test") as db:
                result = await db.load_etf_map()

        assert len(result) == 1
        assert result[0].concept == "AI"

    @pytest.mark.asyncio
    async def test_get_all_concept_summaries(self, mock_db_conn: AsyncMock, mock_db_pool: MagicMock):
        """get_all_concept_summaries 聚合查询"""
        mock_db_conn.fetch = AsyncMock(side_effect=[
            [{"concept": "AI", "cnt": 2}],  # etf_map counts
            [  # latest stocks
                {"concept": "AI", "date": datetime.date(2026, 5, 31), "symbol": "NVDA", "etf_count": 2},
                {"concept": "AI", "date": datetime.date(2026, 5, 31), "symbol": "AMD", "etf_count": 1},
            ],
        ])
        with patch("asyncpg.create_pool", AsyncMock(return_value=mock_db_pool)):
            async with ConceptDb("postgresql://test") as db:
                result = await db.get_all_concept_summaries()

        assert len(result) == 1
        assert result[0].concept == "AI"
        assert result[0].etf_count == 2
        assert result[0].stock_count == 2

    @pytest.mark.asyncio
    async def test_get_latest_stocks(self, mock_db_conn: AsyncMock, mock_db_pool: MagicMock):
        """get_latest_stocks 查询最新日期"""
        mock_db_conn.fetch = AsyncMock(return_value=[
            {
                "date": datetime.date(2026, 5, 31),
                "concept": "AI",
                "symbol": "NVDA",
                "name": "NVIDIA",
                "etf_count": 2,
                "total_weight": 14.5,
                "etfs": "BOTZ,AIQ",
            }
        ])
        with patch("asyncpg.create_pool", AsyncMock(return_value=mock_db_pool)):
            async with ConceptDb("postgresql://test") as db:
                result = await db.get_latest_stocks("AI")

        assert len(result) == 1
        assert result[0].symbol == "NVDA"
        assert result[0].etfs == ["BOTZ", "AIQ"]

    @pytest.mark.asyncio
    async def test_get_stocks_history(self, mock_db_conn: AsyncMock, mock_db_pool: MagicMock):
        """get_stocks_history 日期范围查询"""
        mock_db_conn.fetch = AsyncMock(return_value=[
            {
                "date": datetime.date(2026, 5, 31),
                "concept": "AI",
                "symbol": "NVDA",
                "name": "NVIDIA",
                "etf_count": 2,
                "total_weight": 14.5,
                "etfs": "BOTZ",
            },
            {
                "date": datetime.date(2026, 5, 30),
                "concept": "AI",
                "symbol": "NVDA",
                "name": "NVIDIA",
                "etf_count": 1,
                "total_weight": 8.5,
                "etfs": "BOTZ",
            },
        ])
        with patch("asyncpg.create_pool", AsyncMock(return_value=mock_db_pool)):
            async with ConceptDb("postgresql://test") as db:
                result = await db.get_stocks_history(
                    "AI",
                    datetime.date(2026, 5, 30),
                    datetime.date(2026, 5, 31),
                )

        assert len(result) == 2


# =============================================================================
# 6. Cache 层测试
# =============================================================================


class TestCache:
    """Valkey 缓存测试"""

    @pytest.mark.asyncio
    async def test_get_concept_cache_miss(self, mock_cache: ConceptCache, mock_valkey: AsyncMock):
        """缓存未命中返回 None"""
        mock_valkey.get.return_value = None
        result = await mock_cache.get_concept("AI")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_concept_cache_hit(self, mock_cache: ConceptCache, mock_valkey: AsyncMock):
        """缓存命中返回数据"""
        stock = ConceptStock(
            date=datetime.date(2026, 5, 31),
            concept="AI",
            symbol="NVDA",
            etf_count=2,
            total_weight=14.5,
            etfs=["BOTZ", "AIQ"],
        )
        mock_valkey.get.return_value = json.dumps([stock.model_dump(mode="json")])

        result = await mock_cache.get_concept("AI")
        assert result is not None
        assert len(result) == 1
        assert result[0].symbol == "NVDA"

    @pytest.mark.asyncio
    async def test_set_concept(self, mock_cache: ConceptCache, mock_valkey: AsyncMock):
        """写入缓存"""
        stocks = [
            ConceptStock(
                date=datetime.date(2026, 5, 31),
                concept="AI",
                symbol="NVDA",
                etf_count=2,
                total_weight=14.5,
                etfs=["BOTZ"],
            )
        ]
        await mock_cache.set_concept("AI", stocks)
        mock_valkey.set.assert_called_once()
        call_args = mock_valkey.set.call_args
        assert call_args[0][0] == "concept:AI"
        assert call_args[1]["ex"] == 172800

    @pytest.mark.asyncio
    async def test_get_list_cache_miss(self, mock_cache: ConceptCache, mock_valkey: AsyncMock):
        """列表缓存未命中"""
        mock_valkey.get.return_value = None
        result = await mock_cache.get_list()
        assert result is None

    @pytest.mark.asyncio
    async def test_set_list(self, mock_cache: ConceptCache, mock_valkey: AsyncMock):
        """写入列表缓存"""
        summaries = [
            ConceptSummary(
                concept="AI",
                etf_count=2,
                stock_count=50,
                top_symbols=["NVDA"],
                last_updated=datetime.date(2026, 5, 31),
            )
        ]
        await mock_cache.set_list(summaries)
        call_args = mock_valkey.set.call_args
        assert call_args[0][0] == "concept:__list__"

    @pytest.mark.asyncio
    async def test_close(self, mock_cache: ConceptCache, mock_valkey: AsyncMock):
        """关闭缓存连接"""
        await mock_cache.close()
        mock_valkey.aclose.assert_called_once()


# =============================================================================
# 7. Tasks 测试
# =============================================================================


class TestTasks:
    """Pipeline 任务测试"""

    @pytest.mark.asyncio
    async def test_build_concept_map_flow(
        self,
        test_config: ConceptPipelineConfig,
        mock_finnhub_client: AsyncMock,
        mock_db_conn: AsyncMock,
        mock_db_pool: MagicMock,
        mock_valkey: AsyncMock,
    ):
        """build_concept_map 月度任务流程"""
        candidates = [
            ConceptEtfCandidate(concept="AI", etf_symbol="BOTZ", etfdb_slug="ai-etfs"),
            ConceptEtfCandidate(concept="AI", etf_symbol="AIQ", etfdb_slug="ai-etfs"),
        ]

        with patch(
            "deepalpha.pipeline.concept.tasks.build_concept_map.scrape_concept_etf_candidates",
            AsyncMock(return_value=candidates),
        ):
            with patch("deepalpha.providers.finnhub.client.FinnhubClient.__aenter__", AsyncMock(return_value=mock_finnhub_client)):
                with patch("deepalpha.providers.finnhub.client.FinnhubClient.__aexit__", AsyncMock()):
                    with patch("asyncpg.create_pool", AsyncMock(return_value=mock_db_pool)):
                        with patch("httpx.AsyncClient", return_value=AsyncMock()):
                            await build_concept_map_run(test_config)

        mock_db_conn.executemany.assert_called()

    @pytest.mark.asyncio
    async def test_update_holdings_flow(
        self,
        test_config: ConceptPipelineConfig,
        sample_etf_maps: list[ConceptEtfMap],
        sample_holdings: dict,
        sample_stocks: list[ConceptStock],
        sample_summaries: list[ConceptSummary],
        mock_finnhub_client: AsyncMock,
        mock_db_conn: AsyncMock,
        mock_db_pool: MagicMock,
        mock_valkey: AsyncMock,
    ):
        """update_holdings 日度任务流程"""
        # 配置 mock 行为
        fetch_count = [0]

        async def mock_get_etf_holdings(symbol: str) -> list[dict]:
            result = sample_holdings.get(symbol, [])
            fetch_count[0] += 1
            return result

        mock_finnhub_client.get_etf_holdings = mock_get_etf_holdings

        # 模拟 DB 查询返回
        call_count = [0]

        async def mock_fetch(query: str, *args):
            call_count[0] += 1
            if "concept_etf_map" in query:
                return [
                    {"concept": m.concept, "etf_symbol": m.etf_symbol, "etf_name": m.etf_name,
                     "aum_million": m.aum_million, "etfdb_slug": m.etfdb_slug, "updated_at": m.updated_at}
                    for m in sample_etf_maps
                ]
            elif "latest" in query:
                return [
                    {"date": s.date, "concept": s.concept, "symbol": s.symbol, "name": s.name,
                     "etf_count": s.etf_count, "total_weight": s.total_weight, "etfs": ",".join(s.etfs)}
                    for s in sample_stocks
                ]
            elif "GROUP BY concept" in query:
                return [{"concept": "AI", "cnt": 2}, {"concept": "Robotics", "cnt": 1}]
            return []

        mock_db_conn.fetch = mock_fetch

        with patch(
            "deepalpha.providers.finnhub.client.FinnhubClient.__aenter__",
            AsyncMock(return_value=mock_finnhub_client),
        ):
            with patch("deepalpha.providers.finnhub.client.FinnhubClient.__aexit__", AsyncMock()):
                with patch("asyncpg.create_pool", AsyncMock(return_value=mock_db_pool)):
                    with patch("deepalpha.infrastructure.cache.concept_cache.valkey_asyncio.Valkey", return_value=mock_valkey):
                        with patch("deepalpha.infrastructure.cache.concept_cache.ConceptCache") as MockCache:
                            mock_cache_instance = AsyncMock()
                            MockCache.return_value = mock_cache_instance

                            await update_holdings_run(test_config)

        # 验证 upsert_stocks 被调用
        assert mock_db_conn.executemany.called


# =============================================================================
# 8. API Router 集成测试
# =============================================================================


class TestRouter:
    """API Router 集成测试"""

    @pytest.fixture
    def router_app(self, test_config: ConceptPipelineConfig, mock_valkey: AsyncMock):
        """带 mock 的 FastAPI 应用"""
        app = FastAPI()
        app.include_router(router)

        # Mock config
        @lru_cache(maxsize=1)
        def override_config():
            return test_config

        # Mock cache
        async def override_cache():
            with patch("deepalpha.infrastructure.cache.concept_cache.valkey_asyncio.Valkey", return_value=mock_valkey):
                cache = ConceptCache(
                    host=test_config.valkey_host,
                    port=test_config.valkey_port,
                    password=test_config.valkey_password,
                    ssl=test_config.valkey_ssl,
                    ttl=test_config.concept_cache_ttl,
                )
                try:
                    yield cache
                finally:
                    await cache.close()

        app.dependency_overrides[get_config] = override_config

        return TestClient(app)

    def test_list_concepts_cache_hit(
        self,
        test_config: ConceptPipelineConfig,
        sample_summaries: list[ConceptSummary],
        mock_valkey: AsyncMock,
    ):
        """list 端点 - 缓存命中"""
        mock_valkey.get.return_value = json.dumps([s.model_dump(mode="json") for s in sample_summaries])

        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_config] = lambda: test_config

        with patch("deepalpha.infrastructure.cache.concept_cache.valkey_asyncio.Valkey", return_value=mock_valkey):
            client = TestClient(app)
            resp = client.get("/concept/list")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    def test_list_concepts_cache_miss_db_hit(
        self,
        test_config: ConceptPipelineConfig,
        mock_db_conn: AsyncMock,
        mock_db_pool: MagicMock,
        mock_valkey: AsyncMock,
    ):
        """list 端点 - 缓存未命中，DB 返回"""
        mock_valkey.get.return_value = None  # 缓存未命中
        mock_db_conn.fetch = AsyncMock(side_effect=[
            [{"concept": "AI", "cnt": 2}],
            [
                {"concept": "AI", "date": datetime.date(2026, 5, 31), "symbol": "NVDA", "etf_count": 2},
            ],
        ])

        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_config] = lambda: test_config

        with patch("deepalpha.infrastructure.cache.concept_cache.valkey_asyncio.Valkey", return_value=mock_valkey):
            with patch("asyncpg.create_pool", AsyncMock(return_value=mock_db_pool)):
                client = TestClient(app)
                resp = client.get("/concept/list")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1

    def test_get_concept_cache_hit(
        self,
        test_config: ConceptPipelineConfig,
        sample_stocks: list[ConceptStock],
        mock_valkey: AsyncMock,
    ):
        """get_concept 端点 - 缓存命中"""
        mock_valkey.get.return_value = json.dumps([s.model_dump(mode="json") for s in sample_stocks])

        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_config] = lambda: test_config

        with patch("deepalpha.infrastructure.cache.concept_cache.valkey_asyncio.Valkey", return_value=mock_valkey):
            client = TestClient(app)
            resp = client.get("/concept/Artificial%20Intelligence")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3

    def test_get_concept_with_min_etf_count_filter(
        self,
        test_config: ConceptPipelineConfig,
        sample_stocks: list[ConceptStock],
        mock_valkey: AsyncMock,
    ):
        """get_concept 端点 - min_etf_count 过滤"""
        mock_valkey.get.return_value = json.dumps([s.model_dump(mode="json") for s in sample_stocks])

        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_config] = lambda: test_config

        with patch("deepalpha.infrastructure.cache.concept_cache.valkey_asyncio.Valkey", return_value=mock_valkey):
            client = TestClient(app)
            resp = client.get("/concept/Artificial%20Intelligence?min_etf_count=2")

        assert resp.status_code == 200
        data = resp.json()
        # 只有 NVDA etf_count=2，其他为 1
        assert all(s["etf_count"] >= 2 for s in data)

    def test_get_concept_not_found(
        self,
        test_config: ConceptPipelineConfig,
        mock_db_conn: AsyncMock,
        mock_db_pool: MagicMock,
        mock_valkey: AsyncMock,
    ):
        """get_concept 端点 - 不存在的概念"""
        mock_valkey.get.return_value = None
        mock_db_conn.fetch = AsyncMock(return_value=[])

        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_config] = lambda: test_config

        with patch("deepalpha.infrastructure.cache.concept_cache.valkey_asyncio.Valkey", return_value=mock_valkey):
            with patch("asyncpg.create_pool", AsyncMock(return_value=mock_db_pool)):
                client = TestClient(app)
                resp = client.get("/concept/UnknownConcept")

        assert resp.status_code == 404

    def test_get_concept_history(
        self,
        test_config: ConceptPipelineConfig,
        mock_db_conn: AsyncMock,
        mock_db_pool: MagicMock,
    ):
        """get_concept_history 端点"""
        mock_db_conn.fetch = AsyncMock(return_value=[
            {
                "date": datetime.date(2026, 5, 31),
                "concept": "AI",
                "symbol": "NVDA",
                "name": "NVIDIA",
                "etf_count": 2,
                "total_weight": 14.5,
                "etfs": "BOTZ,AIQ",
            },
            {
                "date": datetime.date(2026, 5, 30),
                "concept": "AI",
                "symbol": "NVDA",
                "name": "NVIDIA",
                "etf_count": 1,
                "total_weight": 8.5,
                "etfs": "BOTZ",
            },
        ])

        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_config] = lambda: test_config

        with patch("asyncpg.create_pool", AsyncMock(return_value=mock_db_pool)):
            client = TestClient(app)
            resp = client.get("/concept/AI/history?start=2026-05-30&end=2026-05-31")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2


# =============================================================================
# 9. 端到端集成测试
# =============================================================================


class TestEndToEnd:
    """端到端流程测试"""

    @pytest.mark.asyncio
    async def test_full_pipeline_flow(
        self,
        test_config: ConceptPipelineConfig,
        mock_finnhub_client: AsyncMock,
        mock_db_conn: AsyncMock,
        mock_db_pool: MagicMock,
        mock_valkey: AsyncMock,
    ):
        """完整流程：抓取 → 过滤 → 聚合 → 缓存"""
        # 1. ETFdb 抓取
        candidates = [
            ConceptEtfCandidate(concept="AI", etf_symbol="BOTZ", etfdb_slug="ai-etfs"),
            ConceptEtfCandidate(concept="AI", etf_symbol="AIQ", etfdb_slug="ai-etfs"),
        ]

        # 2. Finnhub AUM 过滤（配置返回值）
        mock_finnhub_client.get_etf_profile = AsyncMock(side_effect=[
            {"name": "BOTZ", "mktCap": 2_500_000_000.0},
            {"name": "AIQ", "mktCap": 1_800_000_000.0},
        ])
        mock_finnhub_client.get_etf_holdings = AsyncMock(side_effect=[
            [{"symbol": "NVDA", "name": "NVIDIA", "percent": 8.5}],
            [{"symbol": "NVDA", "name": "NVIDIA", "percent": 6.0}],
        ])

        # 3. DB 操作计数
        db_calls = {"upsert_etf_map": 0, "upsert_stocks": 0}

        async def mock_executemany(query: str, records: list):
            if "concept_etf_map" in query:
                db_calls["upsert_etf_map"] += 1
            elif "concept_stocks" in query:
                db_calls["upsert_stocks"] += 1

        mock_db_conn.executemany = mock_executemany
        mock_db_conn.fetch = AsyncMock(side_effect=[
            [{"concept": "AI", "cnt": 2}],
            [
                {"concept": "AI", "date": datetime.date(2026, 5, 31), "symbol": "NVDA", "etf_count": 2},
            ],
        ])

        # 执行月度任务
        with patch(
            "deepalpha.pipeline.concept.tasks.build_concept_map.scrape_concept_etf_candidates",
            AsyncMock(return_value=candidates),
        ):
            with patch("deepalpha.providers.finnhub.client.FinnhubClient.__aenter__", AsyncMock(return_value=mock_finnhub_client)):
                with patch("deepalpha.providers.finnhub.client.FinnhubClient.__aexit__", AsyncMock()):
                    with patch("asyncpg.create_pool", AsyncMock(return_value=mock_db_pool)):
                        with patch("httpx.AsyncClient", return_value=AsyncMock()):
                            await build_concept_map_run(test_config)

        assert db_calls["upsert_etf_map"] > 0

        # 执行日度任务
        with patch("deepalpha.infrastructure.cache.concept_cache.valkey_asyncio.Valkey", return_value=mock_valkey):
            with patch("deepalpha.providers.finnhub.client.FinnhubClient.__aenter__", AsyncMock(return_value=mock_finnhub_client)):
                with patch("deepalpha.providers.finnhub.client.FinnhubClient.__aexit__", AsyncMock()):
                    with patch("asyncpg.create_pool", AsyncMock(return_value=mock_db_pool)):
                        with patch("deepalpha.infrastructure.cache.concept_cache.ConceptCache") as MockCache:
                            mock_cache_instance = AsyncMock()
                            MockCache.return_value = mock_cache_instance
                            await update_holdings_run(test_config)

        # 验证缓存写入
        assert mock_valkey.set.called or mock_cache_instance.set_list.called

    @pytest.mark.asyncio
    async def test_cache_db_consistency(
        self,
        mock_cache: ConceptCache,
        mock_valkey: AsyncMock,
        mock_db_conn: AsyncMock,
        mock_db_pool: MagicMock,
        sample_stocks: list[ConceptStock],
        sample_summaries: list[ConceptSummary],
    ):
        """缓存与 DB 数据一致性"""
        # 1. 写入 DB
        mock_db_conn.fetch = AsyncMock(return_value=[
            {
                "date": s.date,
                "concept": s.concept,
                "symbol": s.symbol,
                "name": s.name,
                "etf_count": s.etf_count,
                "total_weight": s.total_weight,
                "etfs": ",".join(s.etfs),
            }
            for s in sample_stocks
        ])

        with patch("asyncpg.create_pool", AsyncMock(return_value=mock_db_pool)):
            async with ConceptDb("postgresql://test") as db:
                db_stocks = await db.get_latest_stocks("Artificial Intelligence")

        # 2. 写入缓存
        await mock_cache.set_concept("Artificial Intelligence", db_stocks)

        # 3. 从缓存读取
        stored_json = mock_valkey.set.call_args[0][1]
        mock_valkey.get.return_value = stored_json
        cached_stocks = await mock_cache.get_concept("Artificial Intelligence")

        # 4. 验证一致性
        assert len(cached_stocks) == len(db_stocks)
        for cached, original in zip(cached_stocks, db_stocks):
            assert cached.symbol == original.symbol
            assert cached.etf_count == original.etf_count


# =============================================================================
# 10. 边界情况测试
# =============================================================================


class TestEdgeCases:
    """边界情况测试"""

    def test_empty_concept_name(self):
        """空概念名"""
        today = datetime.date(2026, 5, 31)
        s = ConceptStock(
            date=today,
            concept="",
            symbol="NVDA",
            etf_count=1,
            total_weight=8.5,
            etfs=["BOTZ"],
        )
        assert s.concept == ""

    def test_empty_etfs_list(self):
        """空 ETF 列表"""
        today = datetime.date(2026, 5, 31)
        s = ConceptStock(
            date=today,
            concept="AI",
            symbol="NVDA",
            etf_count=0,
            total_weight=0,
            etfs=[],
        )
        assert s.etfs == []

    def test_special_characters_in_concept_name(self):
        """概念名含特殊字符"""
        today = datetime.date(2026, 5, 31)
        s = ConceptStock(
            date=today,
            concept="Artificial Intelligence & Machine Learning",
            symbol="NVDA",
            etf_count=1,
            total_weight=8.5,
            etfs=["BOTZ"],
        )
        assert "&" in s.concept

    @pytest.mark.asyncio
    async def test_cache_set_empty_list(self, mock_cache: ConceptCache, mock_valkey: AsyncMock):
        """缓存空列表"""
        await mock_cache.set_concept("EmptyConcept", [])
        mock_valkey.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_db_upsert_empty_list(self, mock_db_conn: AsyncMock, mock_db_pool: MagicMock):
        """DB upsert 空列表"""
        with patch("asyncpg.create_pool", AsyncMock(return_value=mock_db_pool)):
            async with ConceptDb("postgresql://test") as db:
                await db.upsert_etf_map([])  # 不应抛出异常
                await db.upsert_stocks([])

    @pytest.mark.asyncio
    async def test_aggregate_holdings_handles_missing_name(self):
        """聚合持仓 - 缺失 name 字段"""
        today = datetime.date(2026, 5, 31)
        etf_maps = [ConceptEtfMap(concept="AI", etf_symbol="BOTZ", updated_at=today)]
        holdings = {"BOTZ": [{"symbol": "NVDA", "percent": 8.5}]}  # 无 name
        result = await aggregate_holdings(etf_maps, holdings, date=today)

        assert len(result) == 1
        assert result[0].name is None

    @pytest.mark.asyncio
    async def test_aggregate_holdings_handles_empty_weight(self):
        """聚合持仓 - 空权重"""
        today = datetime.date(2026, 5, 31)
        etf_maps = [ConceptEtfMap(concept="AI", etf_symbol="BOTZ", updated_at=today)]
        holdings = {"BOTZ": [{"symbol": "NVDA", "name": "NVIDIA"}]}  # 无 percent
        result = await aggregate_holdings(etf_maps, holdings, date=today)

        assert len(result) == 1
        assert result[0].total_weight == 0.0