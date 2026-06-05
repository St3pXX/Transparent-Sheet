"""
TransparentSheet 控制台 — 纯 HTML + FastAPI

直接集成到 FastAPI 后端，避免 Streamlit 的静态文件 MIME 类型 bug。
所有逻辑在前端（JS），后端只提供 SSE API。
"""
import asyncio
import json
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator

# 加载 .env 环境变量（项目根目录的上一级）
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / "../.env")

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

from transparent_sheet.agents.tools.datastore import set_store
from transparent_sheet.channels.callback_registry import resolve as resolve_callback
from transparent_sheet.channels.base import ConfirmationResponse
from transparent_sheet.datastore.factory import create_datastore, create_checkpointer
from transparent_sheet.orchestration.graph import build_graph
from transparent_sheet.orchestration.state import OrchestrationState

# ============ 全局状态 ============
_graph = None
_store = None
_checkpointer_ctx = None  # context manager for cleanup


# ============ 生命周期 ============
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global _graph, _store, _checkpointer_ctx

    # 根据 DATASTORE_BACKEND 环境变量自动选择后端
    _store = create_datastore()
    await _store.init_schema()
    set_store(_store)

    checkpointer, _checkpointer_ctx = create_checkpointer()
    _graph = build_graph(checkpointer=checkpointer)
    backend = os.getenv("DATASTORE_BACKEND", "sqlite").lower()
    print(f"[backend] DataStore({backend}) + Graph + Checkpointer initialized")
    yield
    # 清理 checkpointer context manager
    if _checkpointer_ctx and hasattr(_checkpointer_ctx, "__exit__"):
        try:
            _checkpointer_ctx.__exit__(None, None, None)
        except Exception:
            pass
    # 清理 DataStore 连接池
    if hasattr(_store, "close"):
        await _store.close()
    print("[backend] Shutdown")


app = FastAPI(title="TransparentSheet API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ SSE 流式任务执行 ============
@app.get("/stream/{task_id}")
async def stream_task(task_id: str, input: str = ""):
    """
    启动 LangGraph 执行，通过 SSE 流式推送状态更新。
    执行到 writeback_node 前自动中断，等待人工确认。
    """
    if not _graph or not _store:
        raise HTTPException(503, "Backend not initialized")

    if not input.strip():
        raise HTTPException(400, "input is required")

    user_id = "console-user"
    thread_id = f"{user_id}:{task_id}"
    config = {"configurable": {"thread_id": thread_id, "user_id": user_id}}

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            yield _sse("state", {"task_id": task_id, "agent_status": {}})

            initial_state: OrchestrationState = {
                "task_id": task_id,
                "user_id": user_id,
                "task": input,
                "intent": "",
                "sub_tasks": [],
                "record_ids": [],
                "anomaly_record_ids": [],
                "agent_status": {},
                "agent_outputs": {},
                "risk_levels": {},
                "analysis_summary": "",
                "report_content": "",
                "original_report": "",
                "pending_confirmations": [],
                "confirmed": False,
                "confirmed_modifications": [],
                "status": "pending",
                "error": None,
            }

            result = await _graph.ainvoke(
                {"messages": [("user", input)], **initial_state},
                config,
            )

            yield _sse("state", _scrub(result))
            yield _sse("confirm_required", {"task_id": task_id})

        except Exception as e:
            yield _sse("error", {"message": str(e)})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/confirm/{task_id}")
async def confirm_task(task_id: str, action: str = "confirm"):
    """
    恢复挂起的 graph，执行 writeback_node。
    """
    if not _graph:
        raise HTTPException(503, "Backend not initialized")

    user_id = "console-user"
    thread_id = f"{user_id}:{task_id}"
    config = {"configurable": {"thread_id": thread_id, "user_id": user_id}}

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            if action == "confirm":
                await _graph.aupdate_state(config, {"confirmed": True})
                result = await _graph.ainvoke(None, config)
                yield _sse("state", _scrub(result))
                yield _sse("done", {"task_id": task_id})
            else:
                yield _sse("error", {"message": f"Unknown action: {action}"})

        except Exception as e:
            yield _sse("error", {"message": str(e)})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/health")
async def health():
    """健康检查"""
    from transparent_sheet.channels.callback_registry import get_pending_task_ids
    return {
        "status": "ok",
        "graph": _graph is not None,
        "store": _store is not None,
        "pending_confirmations": get_pending_task_ids(),
    }


# ============ 飞书卡片回调 ============
@app.post("/feishu/card_callback")
async def feishu_card_callback(request: Request):
    """
    接收飞书卡片按钮回调。

    飞书卡片的按钮点击会触发此端点。
    请求体包含 action.value，其中包含 task_id 和 action（confirm/revise）。
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, "Invalid JSON body")

    # 飞书卡片回调格式：{ "action": { "value": { "task_id": "...", "action": "confirm" } } }
    action_data = body.get("action", {}).get("value", {})
    task_id = action_data.get("task_id", "")
    action = action_data.get("action", "confirm")

    if not task_id:
        # 飞书 URL 验证请求（首次配置回调时）
        challenge = body.get("challenge")
        if challenge:
            return JSONResponse({"challenge": challenge})
        raise HTTPException(400, "task_id is required")

    # 构建 ConfirmationResponse
    if action == "confirm":
        response = ConfirmationResponse(action="confirm")
    elif action == "revise":
        response = ConfirmationResponse(action="revise", modifications=[])
    else:
        response = ConfirmationResponse(action="confirm")

    # 解析注册的 Future
    resolved = resolve_callback(task_id, response)

    if resolved:
        print(f"[feishu] 卡片回调已处理: task_id={task_id}, action={action}")
        # 更新卡片状态为"已处理"
        try:
            _update_card_after_action(task_id, action)
        except Exception:
            pass
        return JSONResponse({"code": 0, "msg": "ok"})
    else:
        print(f"[feishu] 卡片回调: task_id={task_id} 无待确认任务")
        return JSONResponse({"code": 0, "msg": "no pending task"})


def _update_card_after_action(task_id: str, action: str):
    """卡片操作后更新卡片状态（同步辅助函数，供异步调用）。"""
    # 此处可扩展为更新飞书卡片内容（如显示"已确认"状态）
    pass


@app.post("/feishu/event")
async def feishu_event(request: Request):
    """
    接收飞书开放平台事件回调。

    处理 @机器人 消息，触发任务执行。
    飞书事件订阅的验证请求（challenge）也在此处理。
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, "Invalid JSON body")

    # URL 验证请求
    challenge = body.get("challenge")
    if challenge:
        return JSONResponse({"challenge": challenge})

    # 事件处理
    header = body.get("header", {})
    event_type = header.get("event_type", "")

    if event_type == "im.message.receive_v1":
        event = body.get("event", {})
        message = event.get("message", {})
        chat_id = message.get("chat_id", "")
        message_type = message.get("message_type", "")

        if message_type == "text":
            import json as _json
            content = _json.loads(message.get("content", "{}"))
            text = content.get("text", "").strip()

            # 去除 @机器人 的 mention
            mentions = event.get("message", {}).get("mentions", [])
            for m in mentions:
                text = text.replace(m.get("key", ""), "").strip()

            if text and chat_id:
                # 异步触发任务执行（不阻塞事件响应）
                asyncio.create_task(
                    _run_feishu_task(text, chat_id)
                )

    return JSONResponse({"code": 0, "msg": "ok"})


async def _run_feishu_task(input_text: str, chat_id: str):
    """从飞书消息触发任务执行，中断时发送卡片确认。"""
    if not _graph or not _store:
        print("[feishu] 后端未初始化，跳过任务")
        return

    task_id = str(uuid.uuid4())
    user_id = f"feishu:{chat_id}"
    thread_id = f"{user_id}:{task_id}"
    config = {"configurable": {"thread_id": thread_id, "user_id": user_id}}

    initial_state: OrchestrationState = {
        "task_id": task_id,
        "user_id": user_id,
        "task": input_text,
        "intent": "",
        "sub_tasks": [],
        "record_ids": [],
        "anomaly_record_ids": [],
        "agent_status": {},
        "agent_outputs": {},
        "risk_levels": {},
        "analysis_summary": "",
        "report_content": "",
        "original_report": "",
        "pending_confirmations": [],
        "confirmed": False,
        "confirmed_modifications": [],
        "status": "pending",
        "error": None,
    }

    try:
        # 执行到中断点
        await _graph.ainvoke(
            {"messages": [("user", input_text)], **initial_state},
            config,
        )

        # 获取中断后的状态
        snapshot = await _graph.aget_state(config)
        state = snapshot.values if snapshot else {}

        if state.get("status") == "awaiting_confirm":
            # 发送飞书卡片确认
            from transparent_sheet.channels.feishu_card import FeishuCardChannel
            from transparent_sheet.channels import callback_registry

            channel = FeishuCardChannel(chat_id=chat_id)
            await channel.render_confirmation(state)

            # 注册回调等待
            future = callback_registry.register(task_id, timeout=600.0)
            try:
                response = await asyncio.wait_for(future, timeout=600.0)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                callback_registry.cancel(task_id)
                response = ConfirmationResponse(action="confirm")

            # 恢复执行
            if response.action == "confirm":
                await _graph.aupdate_state(config, {"confirmed": True})
            else:
                await _graph.aupdate_state(config, {
                    "confirmed_modifications": response.modifications,
                })

            await _graph.ainvoke(None, config)
            print(f"[feishu] 任务 {task_id} 完成")

    except Exception as e:
        print(f"[feishu] 任务 {task_id} 失败: {e}")


# ============ HTML 控制台 ============
CONSOLE_HTML_PATH = Path(__file__).parent.parent / "console" / "console.html"


@app.get("/", response_class=HTMLResponse)
async def console():
    """纯 HTML 控制台页面（避免 Streamlit 静态文件 bug）"""
    if CONSOLE_HTML_PATH.exists():
        return HTMLResponse(content=CONSOLE_HTML_PATH.read_text(encoding="utf-8"))
    # Fallback: inline minimal page
    return HTMLResponse(
        content="<html><body><h1>Console not found</h1><p>Run from the project root.</p></body></html>"
    )


# ============ 辅助函数 ============
def _sse(event: str, data: Any) -> str:
    return f"data: {json.dumps({'type': event, 'data': data})}\n\n"


def _scrub(state: dict) -> dict:
    """清理 state 中的内部字段，保留前端需要的字段"""
    return {
        "task_id": state.get("task_id"),
        "user_id": state.get("user_id"),
        "task": state.get("task"),
        "intent": state.get("intent"),
        "record_ids": state.get("record_ids", []),
        "anomaly_record_ids": state.get("anomaly_record_ids", []),
        "agent_status": state.get("agent_status", {}),
        "agent_outputs": state.get("agent_outputs", {}),
        "risk_levels": state.get("risk_levels", {}),
        "analysis_summary": state.get("analysis_summary", ""),
        "report_content": state.get("report_content", ""),
        "pending_confirmations": state.get("pending_confirmations", []),
        "status": state.get("status", "unknown"),
        "error": state.get("error"),
    }


if __name__ == "__main__":
    uvicorn.run("transparent_sheet.api.server:app", host="0.0.0.0", port=8000, reload=False)
