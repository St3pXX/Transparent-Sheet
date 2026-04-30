from typing import TypedDict, Literal, Any, Annotated


def _merge_dicts(left: dict, right: dict) -> dict:
    """Merge two dicts — right takes precedence on key conflicts."""
    return {**left, **right}


class OrchestrationState(TypedDict):
    # create_react_agent required keys
    messages: Annotated[list[Any], lambda a, b: a + b]
    remaining_steps: int

    # Task context
    task_id: str
    user_id: str
    task: str
    intent: str
    sub_tasks: list[str]

    record_ids: list[str]
    anomaly_record_ids: list[str]

    agent_status: Annotated[dict[str, str], _merge_dicts]
    agent_outputs: Annotated[dict[str, str], _merge_dicts]

    risk_levels: Annotated[dict[str, str], _merge_dicts]
    analysis_summary: str
    report_content: str
    original_report: str
    pending_confirmations: list[dict]

    confirmed: bool
    confirmed_modifications: list[dict]
    status: Literal["pending", "running", "awaiting_confirm", "completed", "error", "cancelled"]
    error: str | None
