from typing import Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from transparent_sheet.orchestration.state import OrchestrationState
from transparent_sheet.agents.wrappers import (
    entry_node_wrapper,
    review_node_wrapper,
    analysis_node_wrapper,
    risk_node_wrapper,
    report_node_wrapper,
)
from transparent_sheet.orchestration.writeback import writeback_node


def _set_awaiting_confirm(state: OrchestrationState) -> dict[str, Any]:
    """设置状态为 awaiting_confirm，等待人工确认。"""
    return {"status": "awaiting_confirm"}


def handle_partial_failure(state: OrchestrationState) -> OrchestrationState:
    """并行 Agent 失败时，标记它并继续。"""
    failed_agents = [
        name for name, status in state.get("agent_status", {}).items()
        if status == "failed"
    ]
    if failed_agents:
        note = f"\n\n⚠️ 以下分析未能完成：{', '.join(failed_agents)}"
        state["report_content"] = (state.get("report_content") or "") + note
    return state

def build_graph():
    builder = StateGraph(OrchestrationState)

    # 注意：所有 Agent 通过 Wrapper 封装，不直接作为 Node
    builder.add_node("orchestration_node", lambda state: state)
    builder.add_node("entry_node", entry_node_wrapper)
    builder.add_node("review_node", review_node_wrapper)
    builder.add_node("analysis_node", analysis_node_wrapper)
    builder.add_node("risk_node", risk_node_wrapper)
    builder.add_node("report_node", report_node_wrapper)
    builder.add_node("finish_report_node", _set_awaiting_confirm)  # sets awaiting_confirm before interrupt
    builder.add_node("revise_report_node", report_node_wrapper)
    builder.add_node("writeback_node", writeback_node)
    builder.add_node("error_handler_node", handle_partial_failure)

    # Edges
    builder.add_edge("orchestration_node", "entry_node")

    # Fan-out: entry → 3 parallel
    builder.add_edge("entry_node", "review_node")
    builder.add_edge("entry_node", "analysis_node")
    builder.add_edge("entry_node", "risk_node")

    # Fan-in: 3 parallel → report
    builder.add_edge("review_node", "report_node")
    builder.add_edge("analysis_node", "report_node")
    builder.add_edge("risk_node", "report_node")

    builder.add_edge("report_node", "finish_report_node")
    builder.add_edge("finish_report_node", "writeback_node")

    builder.set_entry_point("orchestration_node")

    # ⚠️ 关键：interrupt_before 必须配合 Checkpointer
    memory = MemorySaver()
    return builder.compile(
        checkpointer=memory,
        interrupt_before=["writeback_node"],
    )