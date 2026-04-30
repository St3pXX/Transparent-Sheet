from langchain_core.tools import tool
from transparent_sheet.datastore.interfaces import AgentOutput
from transparent_sheet.datastore.sqlite import SQLiteDataStore
import time

# 全局 store 实例 — 运行时注入
_store: SQLiteDataStore | None = None

def set_store(store: SQLiteDataStore):
    global _store
    _store = store

def get_store() -> SQLiteDataStore:
    if _store is None:
        raise RuntimeError("DataStore not initialized. Call set_store() first.")
    return _store

@tool
async def save_records_tool(task_id: str, records: list[dict]) -> list[str]:
    """保存记录到 DataStore。返回 record_ids。"""
    store = get_store()
    return await store.save_records(task_id, records)

@tool
async def get_records_tool(task_id: str, record_ids: list[str]) -> list[dict]:
    """从 DataStore 按 ID 获取记录。"""
    store = get_store()
    records = await store.get_records(task_id, record_ids)
    return [{"record_id": r.record_id, "data": r.data} for r in records]

@tool
async def save_agent_output_tool(
    task_id: str,
    agent_name: str,
    output_summary: str,
    full_output: str,
    status: str,
) -> None:
    """保存 agent 执行输出。"""
    store = get_store()
    output = AgentOutput(
        task_id=task_id, agent_name=agent_name,
        output_summary=output_summary, full_output=full_output,
        status=status, timestamp=time.time()
    )
    await store.save_agent_output(output)