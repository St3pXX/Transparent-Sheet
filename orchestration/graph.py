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
    """并行 Agent 失败时，标记它并继续。

    遍历三个并行 Agent，若尚未标记状态则补 success；
    若有 failed 的 Agent，在 report_content 中追加警告。
    """
    PARALLEL_AGENTS = ("review", "analysis", "risk")
    agent_status = dict(state.get("agent_status", {}))

    for name in PARALLEL_AGENTS:
        if name not in agent_status:
            agent_status[name] = "success"

    failed = [n for n in PARALLEL_AGENTS if agent_status.get(n) == "failed"]
    if failed:
        note = f"\n\n⚠️ 以下分析未能完成：{', '.join(failed)}"
        report = (state.get("report_content") or "") + note
        return {**state, "agent_status": agent_status, "report_content": report}

    return {**state, "agent_status": agent_status}


def build_graph(checkpointer=None):
    """构建 LangGraph 编排图。

    Args:
        checkpointer: 可选的持久化 Checkpointer。
            传入 SqliteSaver 可实现进程重启后状态恢复；
            默认使用 MemorySaver（进程内内存，重启丢失）。
    """
    builder = StateGraph(OrchestrationState)

    # 注意：所有 Agent 通过 Wrapper 封装，不直接作为 Node
    builder.add_node("orchestration_node", lambda state: state)
    builder.add_node("entry_node", entry_node_wrapper)
    builder.add_node("review_node", review_node_wrapper)
    builder.add_node("analysis_node", analysis_node_wrapper)
    builder.add_node("risk_node", risk_node_wrapper)
    builder.add_node("error_handler_node", handle_partial_failure)
    builder.add_node("report_node", report_node_wrapper)
    builder.add_node("finish_report_node", _set_awaiting_confirm)  # sets awaiting_confirm before interrupt
    builder.add_node("revise_report_node", report_node_wrapper)
    builder.add_node("writeback_node", writeback_node)

    # Edges
    builder.add_edge("orchestration_node", "entry_node")

    # Fan-out: entry → 3 parallel
    builder.add_edge("entry_node", "review_node")
    builder.add_edge("entry_node", "analysis_node")
    builder.add_edge("entry_node", "risk_node")

    # Fan-in: 3 parallel → error_handler → report
    builder.add_edge("review_node", "error_handler_node")
    builder.add_edge("analysis_node", "error_handler_node")
    builder.add_edge("risk_node", "error_handler_node")
    builder.add_edge("error_handler_node", "report_node")

    builder.add_edge("report_node", "finish_report_node")
    builder.add_edge("finish_report_node", "writeback_node")

    builder.set_entry_point("orchestration_node")

    # ⚠️ 关键：interrupt_before 必须配合 Checkpointer
    memory = checkpointer or MemorySaver()
    return builder.compile(
        checkpointer=memory,
        interrupt_before=["writeback_node"],
    )