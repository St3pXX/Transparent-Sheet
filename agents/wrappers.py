"""
Node Wrapper — 解决 create_react_agent 与全局 State 的隔离陷阱。

create_react_agent 内部维护自己的 messages 上下文，不会自动
将 Tool 输出映射到全局 OrchestrationState。Wrapper 的职责：
1. 调用 Agent
2. 解析 Tool 调用结果，提取需要写回 State 的字段
3. 显式 return 状态更新字典

所有 Agent Node 都通过 Wrapper 封装后再加入 Graph。
"""
import re
from typing import Any
from transparent_sheet.orchestration.state import OrchestrationState
from transparent_sheet.agents.entry import build_entry_agent
from transparent_sheet.agents.review import build_review_agent
from transparent_sheet.agents.analysis import build_analysis_agent
from transparent_sheet.agents.risk import build_risk_agent
from transparent_sheet.agents.report import build_report_agent

def _extract_record_ids_from_result(result: Any) -> list[str]:
    """从 Agent 返回的 Tool 结果中提取 record_ids。"""
    text = str(result)
    match = re.search(r"\['[a-f0-9-]+'(?:,\s*'[a-f0-9-]+')*\]", text)
    if match:
        import ast
        return ast.literal_eval(match.group())
    match = re.search(r"\[([a-f0-9\-,\s]+)\]", text)
    if match:
        return [x.strip().strip("'\"") for x in match.group(1).split(",")]
    return []

def _parse_key_value(text: str, key: str) -> Any:
    """从 Agent 输出中解析 key: value 对。"""
    pattern = rf"{key}\s*[:：]\s*(.+?)(?:\n|$)"
    match = re.search(pattern, text)
    return match.group(1).strip() if match else None

# ============ Entry Wrapper ============
def entry_node_wrapper(state: OrchestrationState) -> OrchestrationState:
    """
    1. 调用 Entry Agent（内部执行 save_records_tool）
    2. 从 Agent 输出中解析 record_ids
    3. 返回更新后的 State
    """
    agent = build_entry_agent()
    result = agent.invoke({"messages": [("user", state["task"])]})

    output_text = result["messages"][-1].content if result.get("messages") else ""
    record_ids = _extract_record_ids_from_result(output_text)

    new_status = dict(state.get("agent_status", {}))
    new_status["entry"] = "success" if record_ids else "failed"

    new_outputs = dict(state.get("agent_outputs", {}))
    new_outputs["entry"] = f"录入 {len(record_ids)} 条记录" if record_ids else "录入失败"

    return {
        **state,
        "record_ids": record_ids,
        "agent_status": new_status,
        "agent_outputs": new_outputs,
    }

# ============ Review Wrapper ============
def review_node_wrapper(state: OrchestrationState) -> OrchestrationState:
    """调用 Review Agent，解析 anomaly_record_ids，更新 agent_status。"""
    agent = build_review_agent()
    result = agent.invoke({
        "messages": [("user", f"请审核以下记录：{state['record_ids']}")],
        **{k: v for k, v in state.items() if k not in ("messages",)}
    })

    output_text = result["messages"][-1].content if result.get("messages") else ""
    anomaly_ids = _extract_record_ids_from_result(output_text)

    new_status = dict(state.get("agent_status", {}))
    new_status["review"] = "success"

    new_outputs = dict(state.get("agent_outputs", {}))
    new_outputs["review"] = f"审核完成，异常记录：{len(anomaly_ids)} 条"

    return {
        **state,
        "anomaly_record_ids": anomaly_ids,
        "agent_status": new_status,
        "agent_outputs": new_outputs,
    }

# ============ Analysis Wrapper ============
def analysis_node_wrapper(state: OrchestrationState) -> OrchestrationState:
    """调用 Analysis Agent，解析 analysis_summary，更新 agent_status。"""
    agent = build_analysis_agent()
    result = agent.invoke({
        "messages": [("user", f"请分析以下记录：{state['record_ids']}")],
        **{k: v for k, v in state.items() if k not in ("messages",)}
    })

    output_text = result["messages"][-1].content if result.get("messages") else ""
    summary = _parse_key_value(output_text, "analysis_summary") or output_text[:200]

    new_status = dict(state.get("agent_status", {}))
    new_status["analysis"] = "success"

    new_outputs = dict(state.get("agent_outputs", {}))
    new_outputs["analysis"] = summary[:100]

    return {
        **state,
        "analysis_summary": summary,
        "agent_status": new_status,
        "agent_outputs": new_outputs,
    }

# ============ Risk Wrapper ============
def risk_node_wrapper(state: OrchestrationState) -> OrchestrationState:
    """调用 Risk Agent，解析 risk_levels dict，更新 agent_status。"""
    agent = build_risk_agent()
    result = agent.invoke({
        "messages": [("user", f"请检测风险：{state['record_ids']}")],
        **{k: v for k, v in state.items() if k not in ("messages",)}
    })

    output_text = result["messages"][-1].content if result.get("messages") else ""

    risk_levels: dict[str, str] = {}
    for line in output_text.split("\n"):
        if any(l in line.lower() for l in ["high", "medium", "low"]):
            parts = line.strip().split()
            for p in parts:
                if p.lower() in ["high", "medium", "low"]:
                    rid = line.replace(p, "").strip().split()[-1]
                    risk_levels[rid] = p.lower()

    new_status = dict(state.get("agent_status", {}))
    new_status["risk"] = "success"

    new_outputs = dict(state.get("agent_outputs", {}))
    new_outputs["risk"] = f"风险检测完成，high: {sum(1 for v in risk_levels.values() if v=='high')} 条"

    return {
        **state,
        "risk_levels": risk_levels,
        "agent_status": new_status,
        "agent_outputs": new_outputs,
    }

# ============ Report Wrapper ============
def report_node_wrapper(state: OrchestrationState) -> OrchestrationState:
    """调用 Report Agent，解析 report_content 和 pending_confirmations。"""
    agent = build_report_agent()
    context = (
        f"Review 结果：{state.get('agent_outputs', {}).get('review', '')}\n"
        f"Analysis 结果：{state.get('analysis_summary', '')}\n"
        f"Risk 结果：{state.get('risk_levels', {})}\n"
    )
    result = agent.invoke({
        "messages": [("user", f"请生成运营周报。上下文：\n{context}")],
        **{k: v for k, v in state.items() if k not in ("messages",)}
    })

    output_text = result["messages"][-1].content if result.get("messages") else ""

    pending = []
    if "pending" in output_text.lower() or "确认" in output_text:
        pending = [{"item": "数据来源需要人工确认", "type": "data_source"}]

    new_status = dict(state.get("agent_status", {}))
    new_status["report"] = "success"

    return {
        **state,
        "report_content": output_text,
        "original_report": output_text,
        "pending_confirmations": pending,
        "agent_status": new_status,
        "agent_outputs": {
            **dict(state.get("agent_outputs", {})),
            "report": output_text[:100],
        },
    }