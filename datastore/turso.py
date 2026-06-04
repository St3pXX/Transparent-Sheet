"""
TursoDataStore — 基于 libsql-experimental 的 Turso/libSQL 实现。

Turso 是 libSQL（SQLite fork）的托管服务，支持 HTTP 远程访问。
本地开发时退化为普通 SQLite 行为。
需要安装: pip install libsql-experimental
"""
import json
import uuid
import time
import os

import libsql_experimental as libsql

from .base import AbstractDataStore
from .interfaces import Record, AgentOutput, Confirmation


class TursoDataStore(AbstractDataStore):
    """Turso/libSQL DataStore。本地文件或远程 URL 均可。"""

    def __init__(self, url: str | None = None, auth_token: str = ""):
        self.url = url or os.getenv("TURSO_DATABASE_URL", "file:transparent_sheet.db")
        self.auth_token = auth_token or os.getenv("TURSO_AUTH_TOKEN", "")
        self._conn = None

    async def _get_conn(self):
        if self._conn is None:
            # libsql_experimental.connect(url, auth_token)
            # 本地 file: 开头时 auth_token 忽略
            self._conn = libsql.connect(
                self.url.replace("file:", ""),
                auth_token=self.auth_token if self.auth_token else None,
            )
        return self._conn

    async def close(self):
        """关闭连接。"""
        if self._conn:
            self._conn.close()
            self._conn = None

    async def init_schema(self):
        conn = await self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS records (
                record_id TEXT PRIMARY KEY,
                task_id   TEXT NOT NULL,
                data      TEXT NOT NULL,
                created_at REAL NOT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_records_task_id ON records (task_id)
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_outputs (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id        TEXT NOT NULL,
                agent_name     TEXT NOT NULL,
                output_summary TEXT NOT NULL,
                full_output    TEXT NOT NULL,
                status         TEXT NOT NULL,
                timestamp      REAL NOT NULL,
                UNIQUE(task_id, agent_name)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS confirmations (
                task_id                  TEXT PRIMARY KEY,
                report_content           TEXT NOT NULL,
                pending_confirmations    TEXT NOT NULL DEFAULT '[]',
                confirmed                INTEGER NOT NULL DEFAULT 0,
                confirmed_modifications  TEXT NOT NULL DEFAULT '[]',
                timestamp                REAL NOT NULL
            )
        """)
        conn.commit()

    async def save_records(self, task_id: str, records: list[dict]) -> list[str]:
        conn = await self._get_conn()
        record_ids = [str(uuid.uuid4()) for _ in records]
        ts = time.time()
        for rid, r in zip(record_ids, records):
            conn.execute(
                "INSERT INTO records (record_id, task_id, data, created_at) VALUES (?, ?, ?, ?)",
                (rid, task_id, json.dumps(r, ensure_ascii=False), ts),
            )
        conn.commit()
        return record_ids

    async def get_records(self, task_id: str, record_ids: list[str]) -> list[Record]:
        conn = await self._get_conn()
        placeholders = ",".join("?" * len(record_ids))
        cursor = conn.execute(
            f"SELECT * FROM records WHERE task_id=? AND record_id IN ({placeholders})",
            [task_id] + record_ids,
        )
        rows = cursor.fetchall()
        return [
            Record(
                record_id=r[0],
                data=json.loads(r[2]) if isinstance(r[2], str) else r[2],
                created_at=r[3],
            )
            for r in rows
        ]

    async def save_agent_output(self, output: AgentOutput) -> None:
        conn = await self._get_conn()
        conn.execute(
            """
            INSERT OR REPLACE INTO agent_outputs
            (task_id, agent_name, output_summary, full_output, status, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                output.task_id,
                output.agent_name,
                output.output_summary,
                output.full_output,
                output.status,
                output.timestamp,
            ),
        )
        conn.commit()

    async def get_agent_output(
        self, task_id: str, agent_name: str
    ) -> AgentOutput | None:
        conn = await self._get_conn()
        cursor = conn.execute(
            "SELECT * FROM agent_outputs WHERE task_id=? AND agent_name=?",
            (task_id, agent_name),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return AgentOutput(
            task_id=row[1],
            agent_name=row[2],
            output_summary=row[3],
            full_output=row[4],
            status=row[5],
            timestamp=row[6],
        )

    async def save_confirmation(self, confirmation: Confirmation) -> None:
        conn = await self._get_conn()
        conn.execute(
            """
            INSERT OR REPLACE INTO confirmations
            (task_id, report_content, pending_confirmations, confirmed,
             confirmed_modifications, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                confirmation.task_id,
                confirmation.report_content,
                json.dumps(confirmation.pending_confirmations, ensure_ascii=False),
                int(confirmation.confirmed),
                json.dumps(confirmation.confirmed_modifications, ensure_ascii=False),
                confirmation.timestamp,
            ),
        )
        conn.commit()

    async def get_confirmation(self, task_id: str) -> Confirmation | None:
        conn = await self._get_conn()
        cursor = conn.execute(
            "SELECT * FROM confirmations WHERE task_id=?", (task_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        return Confirmation(
            task_id=row[0],
            report_content=row[1],
            pending_confirmations=json.loads(row[2]),
            confirmed=bool(row[3]),
            confirmed_modifications=json.loads(row[4]),
            timestamp=row[5],
        )
