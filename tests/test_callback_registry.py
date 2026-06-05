"""
callback_registry 测试 — 验证 Future 注册/解析/取消机制。
"""
import asyncio
import pytest
from transparent_sheet.channels.base import ConfirmationResponse
from transparent_sheet.channels import callback_registry


@pytest.fixture(autouse=True)
def clean_registry():
    """每个测试前清理注册表。"""
    callback_registry._pending.clear()
    yield
    callback_registry._pending.clear()


@pytest.mark.asyncio
async def test_register_and_resolve():
    """register → resolve 往返验证。"""
    future = callback_registry.register("task-001")
    assert callback_registry.is_pending("task-001")
    assert "task-001" in callback_registry.get_pending_task_ids()

    response = ConfirmationResponse(action="confirm")
    assert callback_registry.resolve("task-001", response) is True
    assert not callback_registry.is_pending("task-001")

    result = await future
    assert result.action == "confirm"


@pytest.mark.asyncio
async def test_resolve_nonexistent():
    """解析不存在的 task_id 返回 False。"""
    response = ConfirmationResponse(action="confirm")
    assert callback_registry.resolve("nonexistent", response) is False


@pytest.mark.asyncio
async def test_cancel():
    """取消等待中的 Future。"""
    future = callback_registry.register("task-002")
    assert callback_registry.is_pending("task-002")

    assert callback_registry.cancel("task-002") is True
    assert not callback_registry.is_pending("task-002")
    assert future.cancelled()


@pytest.mark.asyncio
async def test_cancel_nonexistent():
    """取消不存在的 task_id 返回 False。"""
    assert callback_registry.cancel("nonexistent") is False


@pytest.mark.asyncio
async def test_multiple_pending():
    """多个 task 并行等待。"""
    f1 = callback_registry.register("task-a")
    f2 = callback_registry.register("task-b")
    f3 = callback_registry.register("task-c")

    pending = callback_registry.get_pending_task_ids()
    assert len(pending) == 3
    assert set(pending) == {"task-a", "task-b", "task-c"}

    # 只解析 task-b
    callback_registry.resolve("task-b", ConfirmationResponse(action="revise"))
    assert callback_registry.get_pending_task_ids() == ["task-a", "task-c"]

    result = await f2
    assert result.action == "revise"

    # 清理
    callback_registry.cancel("task-a")
    callback_registry.cancel("task-c")


@pytest.mark.asyncio
async def test_resolve_sets_future_result():
    """resolve 后 Future 的 result 就是传入的 ConfirmationResponse。"""
    future = callback_registry.register("task-verify")
    resp = ConfirmationResponse(action="revise", modifications=[{"field": "x"}])
    callback_registry.resolve("task-verify", resp)

    result = await future
    assert result.action == "revise"
    assert result.modifications == [{"field": "x"}]
