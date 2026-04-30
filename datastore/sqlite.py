import aiosqlite
import uuid
import time
from .base import AbstractDataStore
from .interfaces import Record, AgentOutput, Confirmation

class SQLiteDataStore(AbstractDataStore):
    def __init__(self, db_path: str = "transparent_sheet.db"):
        self.db_path = db_path

    async def _get_db(self):
        db = await aiosqlite.connect(self.db_path)
        db.row_factory = aiosqlite.Row
        return db

    async def init_schema(self):
        db = await self._get_db()
        try:
            await db.executescript("""
                CREATE TABLE IF NOT EXISTS records (
                    record_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    data TEXT NOT NULL,
                    created_at REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS agent_outputs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    output_summary TEXT NOT NULL,
                    full_output TEXT NOT NULL,
                    status TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    UNIQUE(task_id, agent_name)
                );
                CREATE TABLE IF NOT EXISTS confirmations (
                    task_id TEXT PRIMARY KEY,
                    report_content TEXT NOT NULL,
                    pending_confirmations TEXT NOT NULL,
                    confirmed INTEGER NOT NULL,
                    confirmed_modifications TEXT NOT NULL,
                    timestamp REAL NOT NULL
                );
                PRAGMA journal_mode=WAL;
            """)
            await db.commit()
        finally:
            await db.close()

    async def save_records(self, task_id: str, records: list[dict]) -> list[str]:
        db = await self._get_db()
        try:
            record_ids = [str(uuid.uuid4()) for _ in records]
            ts = time.time()
            await db.executemany(
                "INSERT INTO records (record_id, task_id, data, created_at) VALUES (?, ?, ?, ?)",
                [(rid, task_id, str(r), ts) for rid, r in zip(record_ids, records)]
            )
            await db.commit()
            return record_ids
        finally:
            await db.close()

    async def get_records(self, task_id: str, record_ids: list[str]) -> list[Record]:
        db = await self._get_db()
        try:
            placeholders = ",".join("?" * len(record_ids))
            cursor = await db.execute(
                f"SELECT * FROM records WHERE task_id=? AND record_id IN ({placeholders})",
                [task_id] + record_ids
            )
            rows = await cursor.fetchall()
            return [Record(record_id=r["record_id"], data=eval(r["data"]), created_at=r["created_at"]) for r in rows]
        finally:
            await db.close()

    async def save_agent_output(self, output: AgentOutput) -> None:
        db = await self._get_db()
        try:
            await db.execute("""
                INSERT OR REPLACE INTO agent_outputs
                (task_id, agent_name, output_summary, full_output, status, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (output.task_id, output.agent_name, output.output_summary,
                  output.full_output, output.status, output.timestamp))
            await db.commit()
        finally:
            await db.close()

    async def get_agent_output(self, task_id: str, agent_name: str) -> AgentOutput | None:
        db = await self._get_db()
        try:
            cursor = await db.execute(
                "SELECT * FROM agent_outputs WHERE task_id=? AND agent_name=?",
                (task_id, agent_name)
            )
            row = await cursor.fetchone()
            if not row:
                return None
            return AgentOutput(
                task_id=row["task_id"], agent_name=row["agent_name"],
                output_summary=row["output_summary"], full_output=row["full_output"],
                status=row["status"], timestamp=row["timestamp"]
            )
        finally:
            await db.close()

    async def save_confirmation(self, confirmation: Confirmation) -> None:
        db = await self._get_db()
        try:
            await db.execute("""
                INSERT OR REPLACE INTO confirmations
                (task_id, report_content, pending_confirmations, confirmed, confirmed_modifications, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (confirmation.task_id, confirmation.report_content,
                  str(confirmation.pending_confirmations), int(confirmation.confirmed),
                  str(confirmation.confirmed_modifications), confirmation.timestamp))
            await db.commit()
        finally:
            await db.close()

    async def get_confirmation(self, task_id: str) -> Confirmation | None:
        db = await self._get_db()
        try:
            cursor = await db.execute("SELECT * FROM confirmations WHERE task_id=?", (task_id,))
            row = await cursor.fetchone()
            if not row:
                return None
            return Confirmation(
                task_id=row["task_id"], report_content=row["report_content"],
                pending_confirmations=eval(row["pending_confirmations"]),
                confirmed=bool(row["confirmed"]),
                confirmed_modifications=eval(row["confirmed_modifications"]),
                timestamp=row["timestamp"]
            )
        finally:
            await db.close()
