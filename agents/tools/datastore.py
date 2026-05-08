from langchain_core.tools import tool
from langchain_core.runnables import RunnableLambda
from transparent_sheet.datastore.interfaces import AgentOutput
from transparent_sheet.datastore.sqlite import SQLiteDataStore
import time
import asyncio
import uuid

# 全局 store 实例 — 运行时注入
_store: SQLiteDataStore | None = None

def set_store(store: SQLiteDataStore):
    global _store
    _store = store

def get_store() -> SQLiteDataStore:
    if _store is None:
        raise RuntimeError("DataStore not initialized. Call set_store() first.")
    return _store

def _sync_save_records(task_id: str, records: list[dict]) -> list[str]:
    """同步包装器，避免 async tool 和 MiniMax ReAct 不兼容。"""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_async_save_records(task_id, records))
    finally:
        loop.close()

async def _async_save_records(task_id: str, records: list[dict]) -> list[str]:
    store = get_store()
    return await store.save_records(task_id, records)

@tool
def save_records_tool(task_id: str, records: list[dict]) -> list[str]:
    """
    保存记录到 DataStore。
    task_id: 任务的唯一标识符（从 state.task_id 获取）
    records: 要保存的记录列表，每个 dict 包含字段
    返回: 保存后的 record_ids 列表
    """
    return _sync_save_records(task_id, records)

@tool
def get_records_tool(task_id: str, record_ids: list[str]) -> list[dict]:
    """从 DataStore 按 ID 获取记录。"""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_async_get_records(task_id, record_ids))
    finally:
        loop.close()

async def _async_get_records(task_id: str, record_ids: list[str]) -> list[dict]:
    store = get_store()
    records = await store.get_records(task_id, record_ids)
    return [{"record_id": r.record_id, "data": r.data} for r in records]

@tool
def save_agent_output_tool(
    task_id: str,
    agent_name: str,
    output_summary: str,
    full_output: str,
    status: str,
) -> None:
    """保存 agent 执行输出。"""
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_async_save_agent_output(
            task_id, agent_name, output_summary, full_output, status
        ))
    finally:
        loop.close()

async def _async_save_agent_output(
    task_id: str, agent_name: str,
    output_summary: str, full_output: str, status: str,
) -> None:
    store = get_store()
    output = AgentOutput(
        task_id=task_id, agent_name=agent_name,
        output_summary=output_summary, full_output=full_output,
        status=status, timestamp=time.time()
    )
    await store.save_agent_output(output)
