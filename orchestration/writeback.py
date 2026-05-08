"""
writeback_node — 将分析结果写入飞书多维表格。
"""
import os
from typing import TypedDict

from transparent_sheet.orchestration.state import OrchestrationState


def _get_feishu_client():
    """延迟初始化 FeishuApiClient（避免循环导入）。"""
    from transparent_sheet.feishu.client import FeishuApiClient

    app_id = os.getenv("FEISHU_APP_ID")
    app_secret = os.getenv("FEISHU_APP_SECRET")
    if not app_id or not app_secret:
        raise RuntimeError(
            "FEISHU_APP_ID / FEISHU_APP_SECRET 未配置。"
            "请在 .env 中填入飞书应用凭证。"
        )
    return FeishuApiClient(app_id, app_secret)


async def writeback_node(state: OrchestrationState) -> OrchestrationState:
    """
    将 record_ids 写入飞书多维表格。
    用户确认后由 Graph 恢复执行时调用。
    """
    app_token = os.getenv("FEISHU_BITABLE_APP_TOKEN")
    table_id = os.getenv("FEISHU_BITABLE_TABLE_ID")
    if not app_token or not table_id:
        raise RuntimeError(
            "FEISHU_BITABLE_APP_TOKEN / FEISHU_BITABLE_TABLE_ID 未配置。"
            "请在 .env 中填入多维表格凭证。"
        )

    client = _get_feishu_client()
    record_ids: list[str] = state.get("record_ids", [])

    if not record_ids:
        # 无数据时写入报告摘要作为一条记录
        records = [
            {
                "fields": {
                    "任务": state.get("task", ""),
                    "报告摘要": (state.get("report_content") or "")[:500],
                    "分析结论": state.get("analysis_summary", "")[:500],
                }
            }
        ]
    else:
        # 从 DataStore 读取实际记录写入
        # Phase 1-4：这里简化处理，直接将 record_ids 相关数据写入
        records = [
            {
                "fields": {
                    "record_id": rid,
                    "风险等级": state.get("risk_levels", {}).get(rid, "low"),
                }
            }
            for rid in record_ids
        ]

    created_ids = await client.batch_create_records(app_token, table_id, records)

    new_outputs = dict(state.get("agent_outputs", {}))
    new_outputs["writeback"] = f"写入 {len(created_ids)} 条记录到飞书"

    return {
        **state,
        "agent_outputs": new_outputs,
        "status": "completed",
    }
