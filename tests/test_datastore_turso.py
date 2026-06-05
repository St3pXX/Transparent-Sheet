"""
TursoDataStore 测试 — 验证本地文件模式（aiosqlite 后端）。
远程 Turso 模式需要真实凭证，此处仅测试本地模式。
"""
import os
import pytest
import pytest_asyncio
import tempfile

from transparent_sheet.datastore.turso import TursoDataStore
from transparent_sheet.datastore.interfaces import AgentOutput, Confirmation


@pytest_asyncio.fixture
async def store():
    """使用临时文件的 TursoDataStore（本地模式）。"""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    s = TursoDataStore(url=f"file:{path}")
    await s.init_schema()
    yield s
    await s.close()
    os.unlink(path)


@pytest.mark.asyncio
async def test_save_and_get_records(store):
    """save_records → get_records 往返验证。"""
    records = [{"商品": "T恤", "销量": 100}, {"商品": "牛仔裤", "销量": 200}]
    ids = await store.save_records("test-turso", records)
    assert len(ids) == 2

    fetched = await store.get_records("test-turso", ids)
    assert len(fetched) == 2
    data_map = {r.data["商品"]: r.data["销量"] for r in fetched}
    assert data_map["T恤"] == 100
    assert data_map["牛仔裤"] == 200


@pytest.mark.asyncio
async def test_agent_output_roundtrip(store):
    """save_agent_output → get_agent_output 往返验证。"""
    output = AgentOutput(
        task_id="test-turso-agent", agent_name="review",
        output_summary="审核完成", full_output="详细报告",
        status="success", timestamp=1700000000.0,
    )
    await store.save_agent_output(output)
    fetched = await store.get_agent_output("test-turso-agent", "review")
    assert fetched is not None
    assert fetched.output_summary == "审核完成"


@pytest.mark.asyncio
async def test_confirmation_roundtrip(store):
    """save_confirmation → get_confirmation 往返验证。"""
    conf = Confirmation(
        task_id="test-turso-confirm", report_content="周报内容",
        pending_confirmations=[{"item": "数据来源"}],
        confirmed=True, confirmed_modifications=[],
        timestamp=1700000000.0,
    )
    await store.save_confirmation(conf)
    fetched = await store.get_confirmation("test-turso-confirm")
    assert fetched is not None
    assert fetched.confirmed is True


@pytest.mark.asyncio
async def test_is_remote_flag():
    """验证 URL 解析逻辑。"""
    local = TursoDataStore(url="file:test.db")
    assert not local._is_remote

    remote = TursoDataStore(url="https://my-db.turso.io")
    assert remote._is_remote

    remote2 = TursoDataStore(url="http://localhost:8080")
    assert remote2._is_remote


@pytest.mark.asyncio
async def test_get_nonexistent_returns_none(store):
    """查询不存在的记录返回 None。"""
    assert await store.get_records("none", ["x"]) == []
    assert await store.get_agent_output("none", "none") is None
    assert await store.get_confirmation("none") is None
