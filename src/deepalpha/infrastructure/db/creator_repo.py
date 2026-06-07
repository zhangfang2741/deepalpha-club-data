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
        """创建所需数据表（幂等）。"""
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            await conn.execute(_CREATE_TABLE_SQL)

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
        self, video_id: str, channel_id: str, message_id: int | None
    ) -> None:
        """将视频标记为已处理。ON CONFLICT 跳过，保证幂等。"""
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO creator_processed_videos (video_id, channel_id, processed_at, telegram_msg_id)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (video_id) DO NOTHING
                """,
                video_id,
                channel_id,
                datetime.datetime.now(datetime.timezone.utc),
                message_id,
            )
