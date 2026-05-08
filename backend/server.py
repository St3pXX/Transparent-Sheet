"""
FastAPI SSE 端点 — 包装 LangGraph graph.astream_events()
供 Next.js 前端消费，实现实时分轨展示。
"""
import sys
import json
import uuid
import os
from pathlib import Path
from typing import AsyncGenerator

from dotenv import load_dotenv

# 加载项目根目录的 .env 文件
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / ".env")

# 将 transparent-sheet 根目录加入 import path
TRANSPARENT_SHEET_ROOT = ROOT_DIR / "transparent-sheet"
sys.path.insert(0, str(TRANSPARENT_SHEET_ROOT))

from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
import asyncio

from transparent_sheet.orchestration.graph import build_graph
from transparent_sheet.orchestration.state import OrchestrationState
from transparent_sheet.datastore.sqlite import SQLiteDataStore
from transparent_sheet.agents.tools.datastore import set_store

app = FastAPI(title="TransparentSheet SSE API")

# 初始化 DataStore
_store: SQLiteDataStore | None = None

@app.on_event("startup")
async def startup():
    global _store
    _store = SQLiteDataStore("transparent_sheet.db")
    await _store.init_schema()
    set_store(_store)


def build_initial_state(task_id: str, user_input: str, user_id: str = "demo-user") -> dict:
    return {
        "messages": [("user", user_input)],
        "remaining_steps": 10,
        "task_id": task_id,
        "user_id": user_id,
        "task": user_input,
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


def _make_sse_event(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


@app.get("/stream/{task_id}")
async def stream_task(
    task_id: str,
    input: str = Query(..., description="用户任务描述"),
):
    """
    SSE 流式端点。
    1. 启动 graph.astream_events()
    2. 按 node_name 分轨推送事件
    3. 在 finish_report_node 后推送 confirm_required
    4. 支持 confirm / revise 后续操作
    """
    graph = build_graph()
    config = {
        "configurable": {
            "thread_id": f"demo-user:{task_id}",
            "user_id": "demo-user",
        }
    }
    initial_state = build_initial_state(task_id, input)

    async def event_generator() -> AsyncGenerator[str, None]:
        # 第一阶段：执行到 interrupt
        async for event in graph.astream(
            initial_state,
            config,
            stream_mode="values",
        ):
            status = event.get("status", "running")
            yield _make_sse_event({
                "type": "state",
                "node": None,  # stream_mode=values 不带 node 名，用 status 代替
                "status": status,
                "data": {
                    "agent_status": event.get("agent_status", {}),
                    "agent_outputs": event.get("agent_outputs", {}),
                    "record_ids": event.get("record_ids", []),
                    "anomaly_record_ids": event.get("anomaly_record_ids", []),
                    "risk_levels": event.get("risk_levels", {}),
                    "analysis_summary": event.get("analysis_summary", ""),
                    "report_content": event.get("report_content", ""),
                    "pending_confirmations": event.get("pending_confirmations", []),
                    "status": status,
                },
            })

            if status == "awaiting_confirm":
                yield _make_sse_event({"type": "confirm_required", "data": event})
                break

        # 第二阶段：等待用户确认（这里简化处理，实际需要 WebSocket 或轮询）
        # 前端通过 POST /confirm/{task_id} 发送确认结果
        yield _make_sse_event({"type": "waiting_confirm", "data": None})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/confirm/{task_id}")
async def confirm_task(
    task_id: str,
    action: str = Query(..., description="confirm 或 revise"),
    modifications: str = Query("[]", description="JSON 数组的修改内容"),
):
    """
    用户确认/修改后，恢复 Graph 执行。
    前端在 confirm_required 事件后调用此端点。
    """
    import json as _json

    graph = build_graph()
    config = {
        "configurable": {
            "thread_id": f"demo-user:{task_id}",
            "user_id": "demo-user",
        }
    }

    thread = graph.get_state(config)
    current_state = thread.values if thread else {}

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            if action == "confirm":
                graph.update_state(
                    config,
                    {"confirmed": True, "confirmed_modifications": _json.loads(modifications)},
                )
                async for event in graph.astream(None, config):
                    yield _make_sse_event({"type": "continuation", "data": event})

            elif action == "revise":
                graph.update_state(
                    config,
                    {"confirmed_modifications": _json.loads(modifications)},
                )
                async for event in graph.astream({"type": "revise"}, config):
                    yield _make_sse_event({"type": "continuation", "data": event})

            yield _make_sse_event({"type": "done", "data": None})

        except Exception as e:
            yield _make_sse_event({"type": "error", "data": str(e)})

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
