import pytest
from transparent_sheet.orchestration.state import OrchestrationState

def test_state_has_required_fields():
    state = OrchestrationState(
        task_id="test-task",
        user_id="test-user",
        task="补全本周销售数据",
        intent="数据补录",
        sub_tasks=["调用Entry Agent补录数据"],
        record_ids=[],
        anomaly_record_ids=[],
        agent_status={},
        agent_outputs={},
        risk_levels={},
        analysis_summary="",
        report_content="",
        original_report="",
        pending_confirmations=[],
        confirmed=False,
        confirmed_modifications=[],
        status="pending",
        error=None,
    )
    assert state["task_id"] == "test-task"
    assert state["status"] == "pending"

def test_state_status_literal():
    from transparent_sheet.orchestration.state import OrchestrationState
    state = OrchestrationState(
        task_id="t", user_id="u", task="t", intent="i", sub_tasks=[],
        record_ids=[], anomaly_record_ids=[], agent_status={}, agent_outputs={},
        risk_levels={}, analysis_summary="", report_content="", original_report="",
        pending_confirmations=[], confirmed=False, confirmed_modifications=[],
        status="running", error=None,
    )
    assert state["status"] == "running"