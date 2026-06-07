import httpx
from deepalpha.infrastructure.providers.minimax.theme_extractor import ThemeExtractor
from deepalpha.domain.signal_radar.models import SignalCategory

_API_URL = "https://api.minimax.chat/v1/chat/completions"


async def test_extract_themes(httpx_mock):
    httpx_mock.add_response(
        url=_API_URL,
        json={
            "choices": [{
                "message": {
                    "content": '{"themes":[{"name":"HBM3e","category":"infra_component","confidence":0.92},{"name":"MCP","category":"tech_concept","confidence":0.85}]}'
                }
            }]
        },
    )
    async with httpx.AsyncClient() as client:
        extractor = ThemeExtractor(client, api_key="test-key")
        themes = await extractor.extract("We are building HBM3e memory systems with MCP protocol.", "earnings_call")
    assert len(themes) == 2
    assert themes[0].name == "HBM3e"
    assert themes[0].category == SignalCategory.infra_component
    assert themes[1].name == "MCP"


async def test_extract_returns_empty_on_api_error(httpx_mock):
    httpx_mock.add_response(url=_API_URL, status_code=500)
    async with httpx.AsyncClient() as client:
        extractor = ThemeExtractor(client, api_key="test-key")
        themes = await extractor.extract("some text", "capex")
    assert themes == []


async def test_extract_filters_low_confidence(httpx_mock):
    httpx_mock.add_response(
        url=_API_URL,
        json={
            "choices": [{
                "message": {
                    "content": '{"themes":[{"name":"HBM3e","category":"infra_component","confidence":0.92},{"name":"vague","category":"tech_concept","confidence":0.3}]}'
                }
            }]
        },
    )
    async with httpx.AsyncClient() as client:
        extractor = ThemeExtractor(client, api_key="test-key")
        themes = await extractor.extract("text", "earnings_call")
    assert len(themes) == 1
    assert themes[0].name == "HBM3e"
