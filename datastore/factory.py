"""
DataStore 工厂 — 根据 DATASTORE_BACKEND 环境变量创建对应实例。

支持的后端:
  - sqlite  (默认): aiosqlite，单机开发
  - postgres: asyncpg，生产部署
  - turso:   libsql-experimental，边缘部署

同时提供对应的 Checkpointer 创建。
"""
import os

from .base import AbstractDataStore


def create_datastore() -> AbstractDataStore:
    """根据环境变量创建 DataStore 实例。"""
    backend = os.getenv("DATASTORE_BACKEND", "sqlite").lower()

    if backend == "postgres":
        from .postgres import PostgresDataStore

        return PostgresDataStore()

    elif backend == "turso":
        from .turso import TursoDataStore

        return TursoDataStore()

    else:
        from .sqlite import SQLiteDataStore

        return SQLiteDataStore(os.getenv("SQLITE_DB_PATH", "transparent_sheet.db"))


def create_checkpointer():
    """根据环境变量创建 LangGraph Checkpointer。

    Returns:
        (checkpointer, cleanup_ctx) 元组。
        checkpointer 可直接传入 build_graph()；
        cleanup_ctx 为 context manager（PostgresSaver 需要），SQLite/内存时为 None。
    """
    backend = os.getenv("DATASTORE_BACKEND", "sqlite").lower()

    if backend == "postgres":
        try:
            from langgraph_checkpoint_postgres.aio import AsyncPostgresSaver
            from contextlib import contextmanager

            dsn = os.getenv(
                "DATABASE_URL", "postgresql://localhost:5432/transparent_sheet"
            )
            saver = AsyncPostgresSaver.from_conn_string(dsn)
            return saver, saver  # AsyncPostgresSaver 本身就是 async context manager
        except ImportError:
            print("[warn] langgraph-checkpoint-postgres 未安装，回退到 MemorySaver")

    # sqlite / turso / fallback → SqliteSaver
    try:
        from langgraph.checkpoint.sqlite import SqliteSaver
        from contextlib import contextmanager

        db_path = os.getenv("CHECKPOINT_DB_PATH", "checkpoints.db")
        ctx = SqliteSaver.from_conn_string(db_path)
        saver = ctx.__enter__()
        return saver, ctx
    except Exception:
        from langgraph.checkpoint.memory import MemorySaver

        return MemorySaver(), None
