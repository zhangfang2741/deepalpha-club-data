"""
YouTube 创作者新闻流 pipeline 单元测试

覆盖：RSS 解析、Telegram 消息格式化、频道 YAML 加载。
"""

import datetime
import textwrap

import pytest

from deepalpha.domain.creator.models import ChannelConfig, CreatorPost, YouTubeVideo
from deepalpha.infrastructure.providers.youtube.feed_loader import _parse_feed
from deepalpha.infrastructure.telegram.sender import _format_message, _esc


# ── 测试数据 ──────────────────────────────────────────────────────────────────

_SAMPLE_RSS = textwrap.dedent("""\
<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015"
      xmlns:media="http://search.yahoo.com/mrss/"
      xmlns="http://www.w3.org/2005/Atom">
  <title>Test Channel</title>
  <entry>
    <id>yt:video:abc123def45</id>
    <yt:videoId>abc123def45</yt:videoId>
    <yt:channelId>UCtest123</yt:channelId>
    <title>Test Video Title</title>
    <link rel="alternate" href="https://www.youtube.com/watch?v=abc123def45"/>
    <published>2024-01-15T10:00:00+00:00</published>
    <updated>2024-01-15T12:00:00+00:00</updated>
    <media:group>
      <media:thumbnail url="https://i.ytimg.com/vi/abc123def45/hqdefault.jpg"
                       width="480" height="360"/>
      <media:description>A test video about investing.</media:description>
    </media:group>
  </entry>
  <entry>
    <id>yt:video:xyz789uvw12</id>
    <yt:videoId>xyz789uvw12</yt:videoId>
    <yt:channelId>UCtest123</yt:channelId>
    <title>Another Video</title>
    <link rel="alternate" href="https://www.youtube.com/watch?v=xyz789uvw12"/>
    <published>2024-01-16T08:00:00+00:00</published>
    <updated>2024-01-16T09:00:00+00:00</updated>
    <media:group>
      <media:thumbnail url="https://i.ytimg.com/vi/xyz789uvw12/hqdefault.jpg"
                       width="480" height="360"/>
    </media:group>
  </entry>
</feed>
""")

_CHANNEL = ChannelConfig(channel_id="UCtest123", channel_name="Test Channel")


# ── RSS 解析 ──────────────────────────────────────────────────────────────────

class TestParseFeed:
    def test_parses_two_entries(self) -> None:
        videos = _parse_feed(_SAMPLE_RSS, _CHANNEL)
        assert len(videos) == 2

    def test_first_video_fields(self) -> None:
        videos = _parse_feed(_SAMPLE_RSS, _CHANNEL)
        v = videos[0]
        assert v.video_id == "abc123def45"
        assert v.title == "Test Video Title"
        assert v.channel_id == "UCtest123"
        assert v.channel_name == "Test Channel"
        assert v.url == "https://www.youtube.com/watch?v=abc123def45"
        assert v.thumbnail_url == "https://i.ytimg.com/vi/abc123def45/hqdefault.jpg"
        assert v.description == "A test video about investing."
        assert v.published_at == datetime.datetime(2024, 1, 15, 10, 0, 0, tzinfo=datetime.timezone.utc)

    def test_second_video_no_description(self) -> None:
        videos = _parse_feed(_SAMPLE_RSS, _CHANNEL)
        v = videos[1]
        assert v.video_id == "xyz789uvw12"
        assert v.description is None

    def test_invalid_xml_returns_empty(self) -> None:
        videos = _parse_feed("<not valid xml>>>", _CHANNEL)
        assert videos == []

    def test_empty_feed_returns_empty(self) -> None:
        empty_xml = '<feed xmlns="http://www.w3.org/2005/Atom"></feed>'
        videos = _parse_feed(empty_xml, _CHANNEL)
        assert videos == []


# ── Telegram 消息格式化 ───────────────────────────────────────────────────────

class TestFormatMessage:
    def _make_post(self, **kwargs) -> CreatorPost:  # type: ignore[no-untyped-def]
        defaults = dict(
            video_id="abc123def45",
            channel_id="UCtest123",
            channel_name="Test Channel",
            title="Test Video",
            url="https://www.youtube.com/watch?v=abc123def45",
            published_at=datetime.datetime(2024, 1, 15, 10, 0, 0, tzinfo=datetime.timezone.utc),
            content_zh="这是一段测试中文摘要。",
        )
        defaults.update(kwargs)
        return CreatorPost(**defaults)

    def test_contains_channel_name(self) -> None:
        msg = _format_message(self._make_post())
        assert "Test Channel" in msg

    def test_contains_title(self) -> None:
        msg = _format_message(self._make_post())
        assert "Test Video" in msg

    def test_contains_article_content(self) -> None:
        msg = _format_message(self._make_post())
        assert "这是一段测试中文摘要" in msg

    def test_contains_url(self) -> None:
        msg = _format_message(self._make_post())
        assert "https://www.youtube.com/watch?v=abc123def45" in msg

    def test_contains_pub_time(self) -> None:
        msg = _format_message(self._make_post())
        assert "2024-01-15" in msg

    def test_html_escaping_in_title(self) -> None:
        msg = _format_message(self._make_post(title="A & B <test>"))
        assert "&amp;" in msg
        assert "&lt;test&gt;" in msg
        assert "<test>" not in msg


# ── HTML 转义 ─────────────────────────────────────────────────────────────────

class TestEsc:
    def test_ampersand(self) -> None:
        assert _esc("a & b") == "a &amp; b"

    def test_angle_brackets(self) -> None:
        assert _esc("<div>") == "&lt;div&gt;"

    def test_quote(self) -> None:
        assert _esc('"hello"') == "&quot;hello&quot;"

    def test_plain_text_unchanged(self) -> None:
        assert _esc("hello world 你好") == "hello world 你好"


# ── YAML 频道加载 ─────────────────────────────────────────────────────────────

class TestLoadChannels:
    def test_loads_enabled_channels(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        yaml_file = tmp_path / "channels.yaml"
        yaml_file.write_text(
            "channels:\n"
            "  - channel_id: UCaaa\n"
            "    channel_name: Chan A\n"
            "    enabled: true\n"
            "  - channel_id: UCbbb\n"
            "    channel_name: Chan B\n"
            "    enabled: false\n",
            encoding="utf-8",
        )
        from deepalpha.interface.pipeline.creator_news.run import load_channels

        channels = load_channels(str(yaml_file))
        assert len(channels) == 1
        assert channels[0].channel_id == "UCaaa"

    def test_missing_file_returns_empty(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        from deepalpha.interface.pipeline.creator_news.run import load_channels

        channels = load_channels(str(tmp_path / "nonexistent.yaml"))
        assert channels == []
