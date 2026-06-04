"""
PostgresDataStore 测试 — 需要本地 PostgreSQL。

无 PostgreSQL 时自动跳过。运行方式:
    DATASTORE_BACKEND=postgres DATABASE_URL=postgresql://... pytest tests/test_datastore_postgres.py -v
"""
import os
import pytest
import pytest_asyncio
import asyncio

# 无 asyncpg 时跳过整个模块
pytest.importorskip("asyncpg", reason="需要 asyncpg: pip install asyncpg")

from transparent_sheet.datastore.postgres import PostgresDataStore
from transparent_sheet.datastore.interfaces import AgentOutput, Confirmation


DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://localhost:5432/transparent_sheet"
)


def _pg_available() -> bool:
    """检查 PostgreSQL 是否可达。"""
    try:
        import asyncpg

        async def _check():
            conn = await asyncpg.connect(DATABASE_URL)
            await conn.close()

        asyncio.get_event_loop().run_until_complete(_check())
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _pg_available(),
    reason=f"PostgreSQL 不可达 ({DATABASE_URL})，跳过",
)


@pytest_asyncio.fixture
async def store():
    s = PostgresDataStore(DATABASE_URL)
    await s.init_schema()
    yield s
    # 清理测试数据
    pool = await s._get_pool()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM records WHERE task_id LIKE 'test-%'")
        await conn.execute("DELETE FROM agent_outputs WHERE task_id LIKE 'test-%'")
        await conn.execute("DELETE FROM confirmations WHERE task_id LIKE 'test-%'")
    await s.close()


@pytest.mark.asyncio
async def test_save_and_get_records(store):
    """save_records → get_records 往返验证。"""
    task_id = "test-pg-records"
    records = [{"商品": "T恤", "销量": 100}, {"商品": "牛仔裤", "销量": 200}]
    ids = await store.save_records(task_id, records)
    assert len(ids) == 2

    fetched = await store.get_records(task_id, ids)
    assert len(fetched) == 2
    assert fetched[0].data["商品"] == "T恤"
    assert fetched[1].data["销量"] == 200


@pytest.mark.asyncio
async def test_agent_output_roundtrip(store):
    """save_agent_output → get_agent_output 往返验证。"""
    output = AgentOutput(
        task_id="test-pg-agent",
        agent_name="review",
        output_summary="审核完成",
        full_output="详细审核报告...",
        status="success",
        timestamp=1700000000.0,
    )
    await store.save_agent_output(output)
    fetched = await store.get_agent_output("test-pg-agent", "review")
    assert fetched is not None
    assert fetched.output_summary == "审核完成"
    assert fetched.status == "success"


@pytest.mark.asyncio
async def test_agent_output_upsert(store):
    """ON CONFLICT 更新验证。"""
    output1 = AgentOutput(
        task_id="test-pg-upsert", agent_name="risk",
        output_summary="v1", full_output="v1", status="success", timestamp=1.0,
    )
    await store.save_agent_output(output1)

    output2 = AgentOutput(
        task_id="test-pg-upsert", agent_name="risk",
        output_summary="v2", full_output="v2", status="failed", timestamp=2.0,
    )
    await store.save_agent_output(output2)

    fetched = await store.get_agent_output("test-pg-upsert", "risk")
    assert fetched.output_summary == "v2"
    assert fetched.status == "failed"


@pytest.mark.asyncio
async def test_confirmation_roundtrip(store):
    """save_confirmation → get_confirmation 往返验证。"""
    conf = Confirmation(
        task_id="test-pg-confirm",
        report_content="周报内容",
        pending_confirmations=[{"item": "数据来源"}],
        confirmed=True,
        confirmed_modifications=[],
        timestamp=1700000000.0,
    )
    await store.save_confirmation(conf)
    fetched = await store.get_confirmation("test-pg-confirm")
    assert fetched is not None
    assert fetched.confirmed is True
    assert fetched.pending_confirmations == [{"item": "数据来源"}]


@pytest.mark.asyncio
async def test_get_nonexistent_returns_none(store):
    """查询不存在的记录返回 None。"""
    assert await store.get_records("test-pg-none", ["nonexistent"]) == []
    assert await store.get_agent_output("test-pg-none", "none") is None
    assert await store.get_confirmation("test-pg-none") is None
