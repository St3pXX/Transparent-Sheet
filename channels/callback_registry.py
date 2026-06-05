"""
卡片回调注册表 — 在 FeishuCardChannel 和 webhook handler 之间传递确认结果。

使用 asyncio.Future 作为桥梁：
1. FeishuCardChannel.render_confirmation() 后调用 register(task_id) 获取 Future
2. FeishuCardChannel.wait_for_response() await 该 Future
3. webhook handler 收到飞书卡片回调后调用 resolve(task_id, response)
"""
import asyncio
from typing import Optional
from .base import ConfirmationResponse

# 全局注册表（进程内）
_pending: dict[str, asyncio.Future] = {}


def register(task_id: str, timeout: float = 600.0) -> asyncio.Future:
    """为 task_id 注册一个 Future，等待飞书卡片回调。

    Args:
        task_id: 任务 ID
        timeout: 超时秒数（默认 10 分钟）

    Returns:
        asyncio.Future，await 它即可等待用户在飞书卡片上的操作
    """
    loop = asyncio.get_event_loop()
    future: asyncio.Future = loop.create_future()
    _pending[task_id] = future
    return future


def resolve(task_id: str, response: ConfirmationResponse) -> bool:
    """webhook handler 调用：解析用户的卡片操作结果。

    Args:
        task_id: 任务 ID
        response: 用户的确认/修改响应

    Returns:
        True 如果找到并解析了对应的 Future，False 如果 task_id 不存在
    """
    future = _pending.pop(task_id, None)
    if future and not future.done():
        future.set_result(response)
        return True
    return False


def cancel(task_id: str) -> bool:
    """取消等待中的 Future（超时或错误时调用）。"""
    future = _pending.pop(task_id, None)
    if future and not future.done():
        future.cancel()
        return True
    return False


def get_pending_task_ids() -> list[str]:
    """返回所有正在等待回调的 task_id 列表。"""
    return list(_pending.keys())


def is_pending(task_id: str) -> bool:
    """检查 task_id 是否正在等待回调。"""
    return task_id in _pending and not _pending[task_id].done()
