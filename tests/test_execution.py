import pytest
import asyncio
import uuid
from langgraph.checkpoint.memory import MemorySaver
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


@pytest.fixture
def shared_checkpointer():
    """共享的 MemorySaver — 同一测试中多次 build_graph 复用同一个实例。"""
    return MemorySaver()


@pytest.mark.asyncio
async def test_graph_astream_to_completion(store, shared_checkpointer):
    """验证 graph.astream() 能异步迭代不报错。"""
    graph = build_graph(checkpointer=shared_checkpointer)

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
async def test_graph_resume_after_interrupt(store, shared_checkpointer):
    """验证中断后能通过 update_state + astream 恢复（writeback 需飞书凭证，这里验证状态正确恢复即可）。"""
    graph = build_graph(checkpointer=shared_checkpointer)

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

    # 验证中断后的状态可被 checkpointer 恢复
    snapshot = await graph.aget_state(config)
    assert snapshot is not None
    assert snapshot.values.get("status") == "awaiting_confirm"
    assert "writeback_node" in [t.name for t in snapshot.tasks]

    # 模拟用户确认：更新状态（不实际恢复执行，避免触发飞书写入）
    graph.update_state(
        config,
        {"confirmed": True, "confirmed_modifications": []}
    )

    # 验证状态已更新
    updated = await graph.aget_state(config)
    assert updated.values.get("confirmed") is True
