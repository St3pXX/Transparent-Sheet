import pytest
import asyncio
import uuid
from transparent_sheet.orchestration.graph import build_graph
from transparent_sheet.orchestration.state import OrchestrationState
from transparent_sheet.datastore.sqlite import SQLiteDataStore
from transparent_sheet.agents.tools.datastore import set_store


@pytest.fixture
def store():
    store = SQLiteDataStore(":memory:")
    asyncio.get_event_loop().run_until_complete(store.init_schema())
    set_store(store)
    return store


@pytest.mark.asyncio
async def test_graph_astream_to_completion(store):
    """验证 graph.astream() 能异步迭代不报错。"""
    graph = build_graph()  # 包含 checkpointer，无须单独 compile

    task_id = str(uuid.uuid4())
    config = {
        "configurable": {
            "thread_id": f"test-user:{task_id}",
            "user_id": "test-user",
        }
    }

    events = []
    async for event in graph.astream(
        {"messages": [("user", "补全本周销售数据")]},
        config,
    ):
        events.append(event)
        if event.get("status") == "awaiting_confirm":
            break

    assert len(events) > 0


@pytest.mark.asyncio
async def test_graph_resume_after_interrupt(store):
    """验证中断后能通过 update_state + astream 恢复。"""
    graph = build_graph()

    task_id = str(uuid.uuid4())
    config = {
        "configurable": {
            "thread_id": f"test-user:{task_id}",
            "user_id": "test-user",
        }
    }

    # 运行到 interrupt
    async for event in graph.astream(
        {"messages": [("user", "补全本周销售数据")]},
        config,
    ):
        if event.get("status") == "awaiting_confirm":
            break

    # 模拟用户确认：更新状态 + 恢复执行
    graph.update_state(
        config,
        {"confirmed": True, "confirmed_modifications": []}
    )

    # 继续执行 writeback_node
    final_events = []
    async for event in graph.astream(None, config):
        final_events.append(event)

    assert len(final_events) > 0
