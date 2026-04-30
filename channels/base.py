from abc import ABC, abstractmethod
from transparent_sheet.orchestration.state import OrchestrationState

class ConfirmationResponse:
    def __init__(self, action: str, modifications: list[dict] | None = None):
        self.action = action  # "confirm" or "revise"
        self.modifications = modifications or []

class ConfirmationChannel(ABC):
    @abstractmethod
    async def render_confirmation(self, state: OrchestrationState) -> None:
        ...

    @abstractmethod
    async def wait_for_response(self) -> ConfirmationResponse:
        ...