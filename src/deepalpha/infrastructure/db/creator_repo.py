"""
创作者视频处理记录 PostgreSQL 数据层（infrastructure 适配器）

实现 ICreatorRepo 协议，追踪已推送到 Telegram 的视频，防止重复推送。
"""

import datetime
from typing import Any

import asyncpg

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS creator_processed_videos (
    video_id        VARCHAR(20)  NOT NULL PRIMARY KEY,
    channel_id      VARCHAR(30)  NOT NULL,
    channel_name    VARCHAR(100),
    title           VARCHAR(500),
    url             TEXT,
    published_at    TIMESTAMPTZ,
    content         TEXT,
    thumbnail_url   TEXT,
    processed_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    telegram_msg_id BIGINT
);
CREATE INDEX IF NOT EXISTS idx_creator_processed_channel
    ON creator_processed_videos (channel_id, processed_at DESC);
"""


class CreatorRepo:
    """asyncpg-based PostgreSQL 数据层，追踪已处理的 YouTube 视频。"""

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn
        self._pool: asyncpg.Pool | None = None  # type: ignore[type-arg]

    async def initialize(self) -> None:
        """创建所需数据表（幂等），并自动迁移新字段。"""
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            await conn.execute(_CREATE_TABLE_SQL)
            # 迁移：添加新字段（如果不存在）
            await conn.execute("""
                ALTER TABLE creator_processed_videos 
                ADD COLUMN IF NOT EXISTS channel_name VARCHAR(100),
                ADD COLUMN IF NOT EXISTS title VARCHAR(500),
                ADD COLUMN IF NOT EXISTS url TEXT,
                ADD COLUMN IF NOT EXISTS published_at TIMESTAMPTZ,
                ADD COLUMN IF NOT EXISTS content TEXT,
                ADD COLUMN IF NOT EXISTS thumbnail_url TEXT
            """)

    async def __aenter__(self) -> "CreatorRepo":
        self._pool = await asyncpg.create_pool(self._dsn)
        await self.initialize()
        return self

    async def __aexit__(self, *_: Any) -> None:
        if self._pool:
            await self._pool.close()

    async def is_processed(self, video_id: str) -> bool:
        """检查视频是否已处理过。"""
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT 1 FROM creator_processed_videos WHERE video_id = $1", video_id
            )
        return row is not None

    async def mark_processed(
        self,
        video_id: str,
        channel_id: str,
        message_id: int | None,
        channel_name: str | None = None,
        title: str | None = None,
        url: str | None = None,
        published_at: datetime.datetime | None = None,
        content: str | None = None,
        thumbnail_url: str | None = None,
    ) -> None:
        """将视频标记为已处理并保存完整内容。ON CONFLICT 更新，保证幂等。"""
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO creator_processed_videos 
                    (video_id, channel_id, channel_name, title, url, published_at, content, thumbnail_url, processed_at, telegram_msg_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (video_id) DO UPDATE SET
                    channel_name = EXCLUDED.channel_name,
                    title = EXCLUDED.title,
                    url = EXCLUDED.url,
                    published_at = EXCLUDED.published_at,
                    content = EXCLUDED.content,
                    thumbnail_url = EXCLUDED.thumbnail_url,
                    telegram_msg_id = EXCLUDED.telegram_msg_id,
                    processed_at = EXCLUDED.processed_at
                """,
                video_id,
                channel_id,
                channel_name,
                title,
                url,
                published_at,
                content,
                thumbnail_url,
                datetime.datetime.now(datetime.timezone.utc),
                message_id,
            )
