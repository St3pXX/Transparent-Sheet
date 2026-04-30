from abc import ABC, abstractmethod
from .interfaces import Record, AgentOutput, Confirmation

class AbstractDataStore(ABC):
    @abstractmethod
    async def save_records(self, task_id: str, records: list[dict]) -> list[str]:
        ...

    @abstractmethod
    async def get_records(self, task_id: str, record_ids: list[str]) -> list[Record]:
        ...

    @abstractmethod
    async def save_agent_output(self, output: AgentOutput) -> None:
        ...

    @abstractmethod
    async def get_agent_output(self, task_id: str, agent_name: str) -> AgentOutput | None:
        ...

    @abstractmethod
    async def save_confirmation(self, confirmation: Confirmation) -> None:
        ...

    @abstractmethod
    async def get_confirmation(self, task_id: str) -> Confirmation | None:
        ...
