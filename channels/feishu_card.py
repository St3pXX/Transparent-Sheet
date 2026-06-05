"""
FeishuCardChannel — 通过飞书交互式消息卡片进行人工确认。

流程：
1. render_confirmation(): 构建消息卡片 JSON → 发送到飞书群聊
2. wait_for_response(): 注册 Future → 阻塞等待卡片按钮回调
3. webhook handler 收到回调 → resolve Future → 返回 ConfirmationResponse
"""
import asyncio
import json
import os
from typing import Any

from .base import ConfirmationChannel, ConfirmationResponse
from . import callback_registry
from transparent_sheet.orchestration.state import OrchestrationState


def build_card(state: OrchestrationState) -> dict[str, Any]:
    """构建飞书消息卡片 JSON。

    卡片包含：报告内容 + 待确认项 + 确认/修改按钮。
    """
    task_id = state.get("task_id", "")
    report = state.get("report_content", "（无报告内容）")
    pending = state.get("pending_confirmations", [])

    # 飞书卡片 markdown 有 4096 字符限制，截断超长报告
    if len(report) > 3800:
        report = report[:3800] + "\n\n... (报告已截断)"

    elements: list[dict] = [
        {"tag": "markdown", "content": report},
    ]

    # 待确认项
    if pending:
        items_text = "\n".join(
            f"⚠️ {item.get('item', str(item))}" for item in pending
        )
        elements.extend([
            {"tag": "hr"},
            {"tag": "markdown", "content": f"**待确认项：**\n{items_text}"},
        ])

    # 操作按钮
    elements.extend([
        {"tag": "hr"},
        {
            "tag": "action",
            "actions": [
                {
                    "tag": "button",
                    "text": {"tag": "plain_text", "content": "✅ 确认并写入"},
                    "type": "primary",
                    "value": {"action": "confirm", "task_id": task_id},
                },
                {
                    "tag": "button",
                    "text": {"tag": "plain_text", "content": "✏️ 修改报告"},
                    "type": "danger",
                    "value": {"action": "revise", "task_id": task_id},
                },
            ],
        },
    ])

    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": "📋 TransparentSheet 运营报告"},
            "template": "blue",
        },
        "elements": elements,
    }


class FeishuCardChannel(ConfirmationChannel):
    """通过飞书消息卡片进行人工确认。"""

    def __init__(self, feishu_client=None, chat_id: str | None = None):
        """
        Args:
            feishu_client: FeishuApiClient 实例（可选，未传则延迟初始化）
            chat_id: 目标群聊 ID（可选，默认从 FEISHU_CHAT_ID 环境变量读取）
        """
        self._client = feishu_client
        self._chat_id = chat_id or os.getenv("FEISHU_CHAT_ID", "")
        self._timeout = float(os.getenv("FEISHU_CARD_CALLBACK_TIMEOUT", "600"))
        self._last_message_id: str | None = None

    async def _ensure_client(self):
        """延迟初始化飞书客户端。"""
        if self._client is None:
            from feishu.client import FeishuApiClient

            app_id = os.getenv("FEISHU_APP_ID", "")
            app_secret = os.getenv("FEISHU_APP_SECRET", "")
            if not app_id or not app_secret:
                raise RuntimeError(
                    "FEISHU_APP_ID / FEISHU_APP_SECRET 未设置，"
                    "无法发送飞书卡片。请配置 .env 文件。"
                )
            self._client = FeishuApiClient(app_id, app_secret)

    async def render_confirmation(self, state: OrchestrationState) -> None:
        """构建并发送飞书消息卡片。"""
        await self._ensure_client()

        if not self._chat_id:
            raise RuntimeError(
                "FEISHU_CHAT_ID 未设置，请配置目标群聊 ID。"
            )

        card = build_card(state)
        card_json = json.dumps(card, ensure_ascii=False)

        result = await self._client.send_message(
            receive_id=self._chat_id,
            receive_id_type="chat_id",
            msg_type="interactive",
            content=card_json,
        )

        self._last_message_id = result.get("message_id")
        task_id = state.get("task_id", "unknown")
        print(f"[feishu] 已发送确认卡片到群 {self._chat_id}，任务 {task_id}")

    async def wait_for_response(self) -> ConfirmationResponse:
        """阻塞等待用户在飞书卡片上的操作。"""
        # 从最近发送的卡片中提取 task_id
        # 如果没有 render_confirmation 调用过，直接报错
        if not self._last_message_id:
            raise RuntimeError("请先调用 render_confirmation() 发送卡片")

        # 从 card value 中获取 task_id（render_confirmation 时已写入）
        # 这里需要从 registry 中获取
        pending_ids = callback_registry.get_pending_task_ids()
        if not pending_ids:
            raise RuntimeError("没有待确认的任务，请先调用 render_confirmation()")

        # 取最新的 task_id（通常是最后一个注册的）
        task_id = pending_ids[-1]

        # 注册 Future 并等待
        future = callback_registry.register(task_id, timeout=self._timeout)
        try:
            response = await asyncio.wait_for(future, timeout=self._timeout)
            return response
        except asyncio.TimeoutError:
            callback_registry.cancel(task_id)
            # 超时后更新卡片为"已超时"状态
            await self._update_card_timeout()
            return ConfirmationResponse(action="confirm")  # 超时自动确认
        except asyncio.CancelledError:
            return ConfirmationResponse(action="confirm")

    async def _update_card_timeout(self):
        """超时后更新卡片状态。"""
        if self._last_message_id and self._client:
            try:
                card = {
                    "config": {"wide_screen_mode": True},
                    "header": {
                        "title": {"tag": "plain_text", "content": "⏰ 确认已超时"},
                        "template": "grey",
                    },
                    "elements": [
                        {"tag": "markdown", "content": "确认等待已超时（10 分钟），系统将自动执行。"},
                    ],
                }
                await self._client.update_message(
                    message_id=self._last_message_id,
                    msg_type="interactive",
                    content=json.dumps(card, ensure_ascii=False),
                )
            except Exception:
                pass  # 更新失败不影响主流程
