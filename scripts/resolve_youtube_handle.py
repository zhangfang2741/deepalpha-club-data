#!/usr/bin/env python3
"""
解析 YouTube @handle → channel_id 小工具

用法：
    uv run python scripts/resolve_youtube_handle.py @catstocktrading
    uv run python scripts/resolve_youtube_handle.py catstocktrading

输出 channel_id（UC... 格式），直接填入 config/youtube_channels.yaml
"""

import asyncio
import re
import sys

import httpx

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


async def resolve_handle(handle: str) -> str | None:
    handle = handle.lstrip("@")
    url = f"https://www.youtube.com/@{handle}"
    async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
        resp = await client.get(url, headers=_HEADERS)
        if resp.status_code != 200:
            print(f"[错误] HTTP {resp.status_code}", file=sys.stderr)
            return None
        # 先找精确 channelId 字段
        m = re.search(r'"channelId"\s*:\s*"(UC[\w-]{22})"', resp.text)
        if m:
            return m.group(1)
        # 回退：任意 UC... 串（去重取首个）
        ids = list(dict.fromkeys(re.findall(r"UC[\w-]{22}", resp.text)))
        return ids[0] if ids else None


async def main() -> None:
    if len(sys.argv) < 2:
        print("用法: python scripts/resolve_youtube_handle.py @handle")
        sys.exit(1)

    handle = sys.argv[1]
    print(f"正在解析 {handle} ...", file=sys.stderr)
    channel_id = await resolve_handle(handle)

    if channel_id:
        print(f"\nchannel_id: {channel_id}")
        print(f"\n请将以下内容添加到 config/youtube_channels.yaml:")
        print(f"  - channel_id: {channel_id}")
        print(f"    channel_name: \"{handle.lstrip('@')}\"")
        print(f"    enabled: true")
    else:
        print("❌ 未能获取 channel_id，请手动查看页面源码", file=sys.stderr)
        print("\n手动方法：")
        print(f"  1. 打开 https://www.youtube.com/{handle}")
        print("  2. 右键 → 查看页面源代码（Ctrl+U）")
        print('  3. Ctrl+F 搜索 "channelId"')
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
