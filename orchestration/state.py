from typing import TypedDict, Literal, Any, Annotated
from collections import OrderedDict


def _merge_dicts(left: dict, right: dict) -> dict:
    """Merge two dicts — right takes precedence on key conflicts."""
    return {**left, **right}


def _last_wins(left: Any, right: Any) -> Any:
    """Annotated reducer: last value wins (for scalar channels)."""
    return right


class OrchestrationState(TypedDict):
    # create_react_agent required keys
    messages: Annotated[list[Any], lambda a, b: a + b]
    remaining_steps: int

    # Task context — scalar keys that receive only one value per step
    task_id: Annotated[str, _last_wins]
    user_id: Annotated[str, _last_wins]
    task: Annotated[str, _last_wins]
    intent: Annotated[str, _last_wins]
    sub_tasks: Annotated[list[str], _last_wins]

    record_ids: Annotated[list[str], _last_wins]
    anomaly_record_ids: Annotated[list[str], _last_wins]

    agent_status: Annotated[dict[str, str], _merge_dicts]
    agent_outputs: Annotated[dict[str, str], _merge_dicts]

    risk_levels: Annotated[dict[str, str], _merge_dicts]
    analysis_summary: Annotated[str, _last_wins]
    report_content: Annotated[str, _last_wins]
    original_report: Annotated[str, _last_wins]
    pending_confirmations: Annotated[list[dict], _last_wins]

    confirmed: Annotated[bool, _last_wins]
    confirmed_modifications: Annotated[list[dict], _last_wins]
    status: Annotated[Literal["pending", "running", "awaiting_confirm", "completed", "error", "cancelled"], _last_wins]
    error: Annotated[str | None, _last_wins]
