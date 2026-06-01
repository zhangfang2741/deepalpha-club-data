import pytest
from pytest_httpx import HTTPXMock

from deepalpha.pipeline.concept.etfdb_scraper import (
    ConceptEtfCandidate,
    _parse_theme_slugs,
    _parse_etf_symbols,
)

# 模拟 ETFdb 主题页 HTML
THEMES_HTML = """
<html><body>
  <div class="etf-category-list">
    <a href="/type/artificial-intelligence-etfs/">Artificial Intelligence</a>
    <a href="/type/robotics-etfs/">Robotics</a>
    <a href="/other-link/">Ignore This</a>
  </div>
</body></html>
"""

# 模拟单个主题下的 ETF 列表页 HTML
ETF_LIST_HTML = """
<html><body>
  <table id="etfs-table">
    <tbody>
      <tr><td><a href="/etf/BOTZ/">BOTZ</a></td><td>Global X Robotics & AI ETF</td></tr>
      <tr><td><a href="/etf/AIQ/">AIQ</a></td><td>Global X AI & Technology ETF</td></tr>
    </tbody>
  </table>
</body></html>
"""


def test_parse_theme_slugs_extracts_concept_and_slug():
    result = _parse_theme_slugs(THEMES_HTML)
    assert "Artificial Intelligence" in result
    assert result["Artificial Intelligence"] == "artificial-intelligence-etfs"
    assert "Robotics" in result
    assert "Ignore This" not in result


def test_parse_etf_symbols_extracts_tickers():
    result = _parse_etf_symbols(ETF_LIST_HTML)
    assert "BOTZ" in result
    assert "AIQ" in result
    assert len(result) == 2
