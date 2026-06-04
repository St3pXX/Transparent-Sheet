import pytest
import pytest_asyncio
import tempfile
import os
from transparent_sheet.datastore.sqlite import SQLiteDataStore
from transparent_sheet.datastore.interfaces import AgentOutput

@pytest_asyncio.fixture
async def store():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    store = SQLiteDataStore(path)
    await store.init_schema()
    yield store
    os.unlink(path)

@pytest.mark.asyncio
async def test_save_and_get_records(store):
    ids = await store.save_records("task-1", [{"name": "Alice"}, {"name": "Bob"}])
    assert len(ids) == 2
    records = await store.get_records("task-1", ids)
    assert len(records) == 2

@pytest.mark.asyncio
async def test_agent_output_roundtrip(store):
    output = AgentOutput(
        task_id="task-1", agent_name="review",
        output_summary="审核完成", full_output="全部正常",
        status="success", timestamp=123456.0
    )
    await store.save_agent_output(output)
    retrieved = await store.get_agent_output("task-1", "review")
    assert retrieved is not None
    assert retrieved.agent_name == "review"
    assert retrieved.status == "success"
