"""
FeishuCardChannel 测试 — 验证卡片构建和 Future 机制。
飞书 API 调用通过 mock 隔离。
"""
import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from transparent_sheet.channels.feishu_card import FeishuCardChannel, build_card
from transparent_sheet.channels.base import ConfirmationResponse
from transparent_sheet.channels import callback_registry


@pytest.fixture(autouse=True)
def clean_registry():
    callback_registry._pending.clear()
    yield
    callback_registry._pending.clear()


def _sample_state():
    return {
        "task_id": "test-task-001",
        "user_id": "test-user",
        "task": "补全本周销售数据",
        "report_content": "## 本周运营周报\n- 总销售额：120,000 元\n- 订单数：350 单",
        "pending_confirmations": [
            {"item": "数据来源需要人工确认", "type": "data_source"}
        ],
        "agent_status": {"entry": "success", "review": "success", "analysis": "success", "risk": "success", "report": "success"},
    }


def test_build_card_structure():
    """卡片 JSON 结构验证。"""
    state = _sample_state()
    card = build_card(state)

    assert card["config"]["wide_screen_mode"] is True
    assert card["header"]["template"] == "blue"
    assert "TransparentSheet" in card["header"]["title"]["content"]

    elements = card["elements"]
    # 至少有：报告 markdown + hr + 待确认项 + hr + action
    assert len(elements) >= 4

    # 检查按钮
    action_elem = [e for e in elements if e["tag"] == "action"]
    assert len(action_elem) == 1
    buttons = action_elem[0]["actions"]
    assert len(buttons) == 2
    assert buttons[0]["value"]["action"] == "confirm"
    assert buttons[1]["value"]["action"] == "revise"
    assert buttons[0]["value"]["task_id"] == "test-task-001"


def test_build_card_no_pending():
    """无待确认项时卡片不包含待确认区域。"""
    state = _sample_state()
    state["pending_confirmations"] = []
    card = build_card(state)

    hr_count = sum(1 for e in card["elements"] if e["tag"] == "hr")
    assert hr_count == 1  # 只有 action 前的 hr


def test_build_card_long_report():
    """超长报告自动截断。"""
    state = _sample_state()
    state["report_content"] = "A" * 5000
    card = build_card(state)

    report_elem = [e for e in card["elements"] if e["tag"] == "markdown"][0]
    assert len(report_elem["content"]) <= 4000
    assert "截断" in report_elem["content"]


@pytest.mark.asyncio
async def test_render_confirmation_sends_card():
    """render_confirmation 调用飞书 send_message。"""
    mock_client = AsyncMock()
    mock_client.send_message = AsyncMock(return_value={"message_id": "msg-001"})

    channel = FeishuCardChannel(feishu_client=mock_client, chat_id="oc_test_chat")
    state = _sample_state()

    await channel.render_confirmation(state)

    mock_client.send_message.assert_called_once()
    call_kwargs = mock_client.send_message.call_args
    assert call_kwargs.kwargs["receive_id"] == "oc_test_chat"
    assert call_kwargs.kwargs["msg_type"] == "interactive"


@pytest.mark.asyncio
async def test_wait_for_response_resolves():
    """wait_for_response 在 resolve 后返回正确的 ConfirmationResponse。"""
    mock_client = AsyncMock()
    mock_client.send_message = AsyncMock(return_value={"message_id": "msg-002"})

    channel = FeishuCardChannel(feishu_client=mock_client, chat_id="oc_test_chat")
    state = _sample_state()

    await channel.render_confirmation(state)

    # 注册 Future（模拟 webhook handler 的行为）
    future = callback_registry.register("test-task-001")

    # 在后台 resolve
    async def delayed_resolve():
        await asyncio.sleep(0.1)
        callback_registry.resolve(
            "test-task-001",
            ConfirmationResponse(action="confirm"),
        )

    asyncio.create_task(delayed_resolve())

    # wait_for_response 应该返回确认响应
    # 注意：wait_for_response 会从 pending_ids 取最新的 task_id
    # 这里需要先清理其他 task_id
    callback_registry._pending.clear()
    callback_registry._pending["test-task-001"] = future

    channel._last_message_id = "msg-002"
    response = await channel.wait_for_response()
    assert response.action == "confirm"


@pytest.mark.asyncio
async def test_wait_for_response_timeout():
    """超时后自动确认。"""
    mock_client = AsyncMock()
    mock_client.update_message = AsyncMock()

    channel = FeishuCardChannel(feishu_client=mock_client, chat_id="oc_test_chat")
    channel._last_message_id = "msg-003"
    channel._timeout = 0.1  # 100ms 超时

    # 手动注册一个 Future（不会被 resolve）
    callback_registry.register("timeout-task")

    response = await channel.wait_for_response()
    assert response.action == "confirm"  # 超时自动确认
    assert not callback_registry.is_pending("timeout-task")
