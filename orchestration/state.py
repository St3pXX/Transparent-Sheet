from typing import TypedDict, Literal

class OrchestrationState(TypedDict):
    task_id: str
    user_id: str
    task: str
    intent: str
    sub_tasks: list[str]

    record_ids: list[str]
    anomaly_record_ids: list[str]

    agent_status: dict[str, str]
    agent_outputs: dict[str, str]

    risk_levels: dict[str, str]
    analysis_summary: str
    report_content: str
    original_report: str
    pending_confirmations: list[dict]

    confirmed: bool
    confirmed_modifications: list[dict]
    status: Literal["pending", "running", "awaiting_confirm", "completed", "error", "cancelled"]
    error: str | None