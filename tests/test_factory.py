"""
DataStore 工厂测试 — 验证环境变量切换逻辑。
"""
import os
import pytest
from unittest.mock import patch


def test_factory_default_returns_sqlite():
    """默认 DATASTORE_BACKEND=sqlite 返回 SQLiteDataStore。"""
    from transparent_sheet.datastore.factory import create_datastore
    from transparent_sheet.datastore.sqlite import SQLiteDataStore

    with patch.dict(os.environ, {"DATASTORE_BACKEND": "sqlite"}, clear=False):
        store = create_datastore()
    assert isinstance(store, SQLiteDataStore)


def test_factory_sqlite_explicit():
    """显式 DATASTORE_BACKEND=sqlite。"""
    from transparent_sheet.datastore.factory import create_datastore
    from transparent_sheet.datastore.sqlite import SQLiteDataStore

    with patch.dict(os.environ, {"DATASTORE_BACKEND": "sqlite", "SQLITE_DB_PATH": ":memory:"}, clear=False):
        store = create_datastore()
    assert isinstance(store, SQLiteDataStore)
    assert store.db_path == ":memory:"


def test_factory_postgres():
    """DATASTORE_BACKEND=postgres 返回 PostgresDataStore。"""
    pytest.importorskip("asyncpg", reason="需要 asyncpg: pip install asyncpg")
    from transparent_sheet.datastore.factory import create_datastore
    from transparent_sheet.datastore.postgres import PostgresDataStore

    with patch.dict(os.environ, {"DATASTORE_BACKEND": "postgres"}, clear=False):
        store = create_datastore()
    assert isinstance(store, PostgresDataStore)


def test_factory_turso():
    """DATASTORE_BACKEND=turso 返回 TursoDataStore。"""
    pytest.importorskip("libsql_experimental", reason="需要 libsql-experimental")
    from transparent_sheet.datastore.factory import create_datastore
    from transparent_sheet.datastore.turso import TursoDataStore

    with patch.dict(os.environ, {"DATASTORE_BACKEND": "turso"}, clear=False):
        store = create_datastore()
    assert isinstance(store, TursoDataStore)


def test_factory_unknown_defaults_to_sqlite():
    """未知后端退化为 SQLite。"""
    from transparent_sheet.datastore.factory import create_datastore
    from transparent_sheet.datastore.sqlite import SQLiteDataStore

    with patch.dict(os.environ, {"DATASTORE_BACKEND": "unknown"}, clear=False):
        store = create_datastore()
    assert isinstance(store, SQLiteDataStore)
