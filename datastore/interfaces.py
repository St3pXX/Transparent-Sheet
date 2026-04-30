from dataclasses import dataclass
from typing import Any

@dataclass
class Record:
    record_id: str
    data: dict[str, Any]
    created_at: float

@dataclass
class AgentOutput:
    task_id: str
    agent_name: str
    output_summary: str
    full_output: str
    status: str  # success/failed/skipped
    timestamp: float

@dataclass
class Confirmation:
    task_id: str
    report_content: str
    pending_confirmations: list[dict]
    confirmed: bool
    confirmed_modifications: list[dict]
    timestamp: float
