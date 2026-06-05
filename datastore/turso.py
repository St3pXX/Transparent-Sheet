"""
TursoDataStore — Turso/libSQL 实现，支持两种连接模式。

1. 远程 Turso（http/https URL）：使用 libsql_client（HTTP 协议）
2. 本地文件（file: URL）：使用 aiosqlite（SQLite 兼容）

需要安装:
  - 远程模式: pip install libsql-client
  - 本地模式: pip install aiosqlite（内置依赖）
"""
import json
import uuid
import time
import os

from .base import AbstractDataStore
from .interfaces import Record, AgentOutput, Confirmation


# 3 张表的 DDL（SQLite 语法，兼容 Turso）
_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS records (
    record_id TEXT PRIMARY KEY,
    task_id   TEXT NOT NULL,
    data      TEXT NOT NULL,
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_records_task_id ON records (task_id);

CREATE TABLE IF NOT EXISTS agent_outputs (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id        TEXT NOT NULL,
    agent_name     TEXT NOT NULL,
    output_summary TEXT NOT NULL,
    full_output    TEXT NOT NULL,
    status         TEXT NOT NULL,
    timestamp      REAL NOT NULL,
    UNIQUE(task_id, agent_name)
);

CREATE TABLE IF NOT EXISTS confirmations (
    task_id                  TEXT PRIMARY KEY,
    report_content           TEXT NOT NULL,
    pending_confirmations    TEXT NOT NULL DEFAULT '[]',
    confirmed                INTEGER NOT NULL DEFAULT 0,
    confirmed_modifications  TEXT NOT NULL DEFAULT '[]',
    timestamp                REAL NOT NULL
);
"""


class TursoDataStore(AbstractDataStore):
    """Turso/libSQL DataStore。远程用 HTTP，本地用 aiosqlite。"""

    def __init__(self, url: str | None = None, auth_token: str = ""):
        self.url = url or os.getenv("TURSO_DATABASE_URL", "file:transparent_sheet.db")
        self.auth_token = auth_token or os.getenv("TURSO_AUTH_TOKEN", "")
        self._is_remote = self.url.startswith("http://") or self.url.startswith("https://")
        self._client = None  # libsql_client.Client（远程）
        self._conn = None    # aiosqlite 连接（本地）

    async def _get_client(self):
        """获取远程 Turso 客户端（HTTP 模式）。"""
        if self._client is None:
            import libsql_client
            self._client = libsql_client.create_client(
                self.url, auth_token=self.auth_token or None,
            )
        return self._client

    async def _get_local_conn(self):
        """获取本地 aiosqlite 连接（文件模式）。"""
        if self._conn is None:
            import aiosqlite
            db_path = self.url.replace("file:", "")
            self._conn = await aiosqlite.connect(db_path)
            self._conn.row_factory = aiosqlite.Row
        return self._conn

    async def close(self):
        """关闭连接。"""
        if self._is_remote and self._client:
            self._client.close()
            self._client = None
        elif self._conn:
            await self._conn.close()
            self._conn = None

    # ============ Schema ============

    async def init_schema(self):
        if self._is_remote:
            client = await self._get_client()
            for stmt in _SCHEMA_SQL.strip().split(";"):
                stmt = stmt.strip()
                if stmt:
                    await client.execute(stmt)
        else:
            conn = await self._get_local_conn()
            await conn.executescript(_SCHEMA_SQL)
            await conn.commit()

    # ============ 远程 Turso（HTTP） ============

    async def _remote_save_records(self, task_id, records):
        client = await self._get_client()
        record_ids = [str(uuid.uuid4()) for _ in records]
        ts = time.time()
        for rid, r in zip(record_ids, records):
            await client.execute(
                "INSERT INTO records (record_id, task_id, data, created_at) VALUES (?, ?, ?, ?)",
                [rid, task_id, json.dumps(r, ensure_ascii=False), ts],
            )
        return record_ids

    async def _remote_get_records(self, task_id, record_ids):
        client = await self._get_client()
        placeholders = ",".join("?" * len(record_ids))
        rs = await client.execute(
            f"SELECT record_id, data, created_at FROM records WHERE task_id=? AND record_id IN ({placeholders})",
            [task_id] + record_ids,
        )
        return [
            Record(
                record_id=row[0],
                data=json.loads(row[1]),
                created_at=row[2],
            )
            for row in rs.rows
        ]

    async def _remote_save_agent_output(self, output):
        client = await self._get_client()
        await client.execute(
            "INSERT OR REPLACE INTO agent_outputs "
            "(task_id, agent_name, output_summary, full_output, status, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            [output.task_id, output.agent_name, output.output_summary,
             output.full_output, output.status, output.timestamp],
        )

    async def _remote_get_agent_output(self, task_id, agent_name):
        client = await self._get_client()
        rs = await client.execute(
            "SELECT task_id, agent_name, output_summary, full_output, status, timestamp "
            "FROM agent_outputs WHERE task_id=? AND agent_name=?",
            [task_id, agent_name],
        )
        if not rs.rows:
            return None
        row = rs.rows[0]
        return AgentOutput(
            task_id=row[0], agent_name=row[1], output_summary=row[2],
            full_output=row[3], status=row[4], timestamp=row[5],
        )

    async def _remote_save_confirmation(self, confirmation):
        client = await self._get_client()
        await client.execute(
            "INSERT OR REPLACE INTO confirmations "
            "(task_id, report_content, pending_confirmations, confirmed, "
            "confirmed_modifications, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
            [confirmation.task_id, confirmation.report_content,
             json.dumps(confirmation.pending_confirmations, ensure_ascii=False),
             int(confirmation.confirmed),
             json.dumps(confirmation.confirmed_modifications, ensure_ascii=False),
             confirmation.timestamp],
        )

    async def _remote_get_confirmation(self, task_id):
        client = await self._get_client()
        rs = await client.execute(
            "SELECT task_id, report_content, pending_confirmations, "
            "confirmed, confirmed_modifications, timestamp "
            "FROM confirmations WHERE task_id=?",
            [task_id],
        )
        if not rs.rows:
            return None
        row = rs.rows[0]
        return Confirmation(
            task_id=row[0], report_content=row[1],
            pending_confirmations=json.loads(row[2]),
            confirmed=bool(row[3]),
            confirmed_modifications=json.loads(row[4]),
            timestamp=row[5],
        )

    # ============ 本地文件（aiosqlite） ============

    async def _local_save_records(self, task_id, records):
        conn = await self._get_local_conn()
        record_ids = [str(uuid.uuid4()) for _ in records]
        ts = time.time()
        await conn.executemany(
            "INSERT INTO records (record_id, task_id, data, created_at) VALUES (?, ?, ?, ?)",
            [(rid, task_id, json.dumps(r, ensure_ascii=False), ts)
             for rid, r in zip(record_ids, records)],
        )
        await conn.commit()
        return record_ids

    async def _local_get_records(self, task_id, record_ids):
        conn = await self._get_local_conn()
        placeholders = ",".join("?" * len(record_ids))
        cursor = await conn.execute(
            f"SELECT record_id, data, created_at FROM records "
            f"WHERE task_id=? AND record_id IN ({placeholders})",
            [task_id] + record_ids,
        )
        rows = await cursor.fetchall()
        return [
            Record(record_id=r[0], data=json.loads(r[1]), created_at=r[2])
            for r in rows
        ]

    async def _local_save_agent_output(self, output):
        conn = await self._get_local_conn()
        await conn.execute(
            "INSERT OR REPLACE INTO agent_outputs "
            "(task_id, agent_name, output_summary, full_output, status, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (output.task_id, output.agent_name, output.output_summary,
             output.full_output, output.status, output.timestamp),
        )
        await conn.commit()

    async def _local_get_agent_output(self, task_id, agent_name):
        conn = await self._get_local_conn()
        cursor = await conn.execute(
            "SELECT * FROM agent_outputs WHERE task_id=? AND agent_name=?",
            (task_id, agent_name),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return AgentOutput(
            task_id=row[1], agent_name=row[2], output_summary=row[3],
            full_output=row[4], status=row[5], timestamp=row[6],
        )

    async def _local_save_confirmation(self, confirmation):
        conn = await self._get_local_conn()
        await conn.execute(
            "INSERT OR REPLACE INTO confirmations "
            "(task_id, report_content, pending_confirmations, confirmed, "
            "confirmed_modifications, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
            (confirmation.task_id, confirmation.report_content,
             json.dumps(confirmation.pending_confirmations, ensure_ascii=False),
             int(confirmation.confirmed),
             json.dumps(confirmation.confirmed_modifications, ensure_ascii=False),
             confirmation.timestamp),
        )
        await conn.commit()

    async def _local_get_confirmation(self, task_id):
        conn = await self._get_local_conn()
        cursor = await conn.execute(
            "SELECT * FROM confirmations WHERE task_id=?", (task_id,)
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return Confirmation(
            task_id=row[0], report_content=row[1],
            pending_confirmations=json.loads(row[2]),
            confirmed=bool(row[3]),
            confirmed_modifications=json.loads(row[4]),
            timestamp=row[5],
        )

    # ============ 统一接口（自动路由） ============

    async def save_records(self, task_id: str, records: list[dict]) -> list[str]:
        if self._is_remote:
            return await self._remote_save_records(task_id, records)
        return await self._local_save_records(task_id, records)

    async def get_records(self, task_id: str, record_ids: list[str]) -> list[Record]:
        if self._is_remote:
            return await self._remote_get_records(task_id, record_ids)
        return await self._local_get_records(task_id, record_ids)

    async def save_agent_output(self, output: AgentOutput) -> None:
        if self._is_remote:
            return await self._remote_save_agent_output(output)
        return await self._local_save_agent_output(output)

    async def get_agent_output(self, task_id: str, agent_name: str) -> AgentOutput | None:
        if self._is_remote:
            return await self._remote_get_agent_output(task_id, agent_name)
        return await self._local_get_agent_output(task_id, agent_name)

    async def save_confirmation(self, confirmation: Confirmation) -> None:
        if self._is_remote:
            return await self._remote_save_confirmation(confirmation)
        return await self._local_save_confirmation(confirmation)

    async def get_confirmation(self, task_id: str) -> Confirmation | None:
        if self._is_remote:
            return await self._remote_get_confirmation(task_id)
        return await self._local_get_confirmation(task_id)
