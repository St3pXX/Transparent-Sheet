"""
TransparentSheet 控制台 — 纯 HTML + FastAPI

直接集成到 FastAPI 后端，避免 Streamlit 的静态文件 MIME 类型 bug。
所有逻辑在前端（JS），后端只提供 SSE API。
"""
import asyncio
import json
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator

# 加载 .env 环境变量（项目根目录的上一级）
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / "../.env")

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse

from langgraph.checkpoint.sqlite import SqliteSaver

from transparent_sheet.agents.tools.datastore import set_store
from transparent_sheet.datastore.sqlite import SQLiteDataStore
from transparent_sheet.orchestration.graph import build_graph
from transparent_sheet.orchestration.state import OrchestrationState

# ============ 全局状态 ============
_graph = None
_store = None
_checkpointer_ctx = None  # SqliteSaver context manager


# ============ 生命周期 ============
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global _graph, _store, _checkpointer_ctx
    _store = SQLiteDataStore("transparent_sheet.db")
    await _store.init_schema()
    set_store(_store)

    # 持久化 Checkpointer — 进程重启后 Graph 状态可恢复
    _checkpointer_ctx = SqliteSaver.from_conn_string("checkpoints.db")
    checkpointer = _checkpointer_ctx.__enter__()
    _graph = build_graph(checkpointer=checkpointer)
    print("[backend] DataStore + Graph + Checkpointer initialized")
    yield
    _checkpointer_ctx.__exit__(None, None, None)
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
    return {"status": "ok", "graph": _graph is not None, "store": _store is not None}


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
