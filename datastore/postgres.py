"""
PostgresDataStore — 基于 asyncpg 的 PostgreSQL 实现。

使用连接池管理数据库连接，SQL 语法适配 PostgreSQL。
需要安装: pip install asyncpg
"""
import json
import uuid
import time
import os

import asyncpg

from .base import AbstractDataStore
from .interfaces import Record, AgentOutput, Confirmation


class PostgresDataStore(AbstractDataStore):
    """PostgreSQL DataStore，使用 asyncpg 连接池。"""

    def __init__(self, dsn: str | None = None):
        self.dsn = dsn or os.getenv(
            "DATABASE_URL", "postgresql://localhost:5432/transparent_sheet"
        )
        self._pool: asyncpg.Pool | None = None

    async def _get_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            self._pool = await asyncpg.create_pool(self.dsn, min_size=2, max_size=10)
        return self._pool

    async def close(self):
        """关闭连接池。"""
        if self._pool:
            await self._pool.close()
            self._pool = None

    async def init_schema(self):
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS records (
                    record_id TEXT PRIMARY KEY,
                    task_id   TEXT NOT NULL,
                    data      JSONB NOT NULL,
                    created_at DOUBLE PRECISION NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_records_task_id ON records (task_id);

                CREATE TABLE IF NOT EXISTS agent_outputs (
                    id             SERIAL PRIMARY KEY,
                    task_id        TEXT NOT NULL,
                    agent_name     TEXT NOT NULL,
                    output_summary TEXT NOT NULL,
                    full_output    TEXT NOT NULL,
                    status         TEXT NOT NULL,
                    timestamp      DOUBLE PRECISION NOT NULL,
                    UNIQUE(task_id, agent_name)
                );

                CREATE TABLE IF NOT EXISTS confirmations (
                    task_id                  TEXT PRIMARY KEY,
                    report_content           TEXT NOT NULL,
                    pending_confirmations    JSONB NOT NULL DEFAULT '[]'::jsonb,
                    confirmed                BOOLEAN NOT NULL DEFAULT FALSE,
                    confirmed_modifications  JSONB NOT NULL DEFAULT '[]'::jsonb,
                    timestamp                DOUBLE PRECISION NOT NULL
                );
            """)

    async def save_records(self, task_id: str, records: list[dict]) -> list[str]:
        pool = await self._get_pool()
        record_ids = [str(uuid.uuid4()) for _ in records]
        ts = time.time()
        async with pool.acquire() as conn:
            await conn.executemany(
                """
                INSERT INTO records (record_id, task_id, data, created_at)
                VALUES ($1, $2, $3::jsonb, $4)
                """,
                [
                    (rid, task_id, json.dumps(r, ensure_ascii=False), ts)
                    for rid, r in zip(record_ids, records)
                ],
            )
        return record_ids

    async def get_records(self, task_id: str, record_ids: list[str]) -> list[Record]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT record_id, data, created_at
                FROM records
                WHERE task_id = $1 AND record_id = ANY($2::text[])
                """,
                task_id,
                record_ids,
            )
        return [
            Record(
                record_id=r["record_id"],
                data=json.loads(r["data"]) if isinstance(r["data"], str) else r["data"],
                created_at=r["created_at"],
            )
            for r in rows
        ]

    async def save_agent_output(self, output: AgentOutput) -> None:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO agent_outputs
                    (task_id, agent_name, output_summary, full_output, status, timestamp)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (task_id, agent_name) DO UPDATE SET
                    output_summary = EXCLUDED.output_summary,
                    full_output    = EXCLUDED.full_output,
                    status         = EXCLUDED.status,
                    timestamp      = EXCLUDED.timestamp
                """,
                output.task_id,
                output.agent_name,
                output.output_summary,
                output.full_output,
                output.status,
                output.timestamp,
            )

    async def get_agent_output(
        self, task_id: str, agent_name: str
    ) -> AgentOutput | None:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT task_id, agent_name, output_summary, full_output, status, timestamp
                FROM agent_outputs
                WHERE task_id = $1 AND agent_name = $2
                """,
                task_id,
                agent_name,
            )
        if not row:
            return None
        return AgentOutput(
            task_id=row["task_id"],
            agent_name=row["agent_name"],
            output_summary=row["output_summary"],
            full_output=row["full_output"],
            status=row["status"],
            timestamp=row["timestamp"],
        )

    async def save_confirmation(self, confirmation: Confirmation) -> None:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO confirmations
                    (task_id, report_content, pending_confirmations,
                     confirmed, confirmed_modifications, timestamp)
                VALUES ($1, $2, $3::jsonb, $4, $5::jsonb, $6)
                ON CONFLICT (task_id) DO UPDATE SET
                    report_content          = EXCLUDED.report_content,
                    pending_confirmations   = EXCLUDED.pending_confirmations,
                        confirmed               = EXCLUDED.confirmed,
                    confirmed_modifications = EXCLUDED.confirmed_modifications,
                    timestamp               = EXCLUDED.timestamp
                """,
                confirmation.task_id,
                confirmation.report_content,
                json.dumps(confirmation.pending_confirmations, ensure_ascii=False),
                confirmation.confirmed,
                json.dumps(confirmation.confirmed_modifications, ensure_ascii=False),
                confirmation.timestamp,
            )

    async def get_confirmation(self, task_id: str) -> Confirmation | None:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT task_id, report_content, pending_confirmations,
                       confirmed, confirmed_modifications, timestamp
                FROM confirmations
                WHERE task_id = $1
                """,
                task_id,
            )
        if not row:
            return None
        return Confirmation(
            task_id=row["task_id"],
            report_content=row["report_content"],
            pending_confirmations=json.loads(row["pending_confirmations"])
            if isinstance(row["pending_confirmations"], str)
            else row["pending_confirmations"],
            confirmed=bool(row["confirmed"]),
            confirmed_modifications=json.loads(row["confirmed_modifications"])
            if isinstance(row["confirmed_modifications"], str)
            else row["confirmed_modifications"],
            timestamp=row["timestamp"],
        )
