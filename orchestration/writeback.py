"""
writeback_node — 将分析结果写入飞书多维表格。
"""
import os
from typing import Any

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
    将分析结果写入飞书多维表格。
    用户确认后由 Graph 恢复执行时调用。
    自动创建所需字段（如果不存在）。
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
    risk_levels: dict[str, str] = state.get("risk_levels", {})

    # 构建写入记录
    if not record_ids:
        # 无 record_ids 时：写入报告摘要记录
        records: list[dict[str, Any]] = [
            {
                "fields": {
                    "任务": state.get("task", ""),
                    "分析结论": (state.get("analysis_summary") or "")[:2000],
                    "风险摘要": str(risk_levels)[:500] if risk_levels else "",
                }
            }
        ]
    else:
        # 有 record_ids 时：批量写入分析记录
        records = []
        for rid in record_ids:
            risk = risk_levels.get(rid, "low")
            records.append(
                {
                    "fields": {
                        "原记录ID": rid,
                        "风险等级": risk,
                        "关联任务": state.get("task", "")[:500],
                    }
                }
            )

    # 自动创建字段（若不存在），然后写入
    created_ids = await client.batch_create_records(app_token, table_id, records)

    new_outputs = dict(state.get("agent_outputs", {}))
    new_outputs["writeback"] = f"写入 {len(created_ids)} 条记录到飞书"

    return {
        **state,
        "agent_outputs": new_outputs,
        "status": "completed",
    }
