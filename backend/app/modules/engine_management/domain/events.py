from dataclasses import dataclass
from app.shared.domain.events import DomainEvent

@dataclass(frozen=True)
class EngineInspectionRequiredEvent(DomainEvent):
    event_type: str = "EngineInspectionRequiredEvent"
    aggregate_type: str = "engine_management"
