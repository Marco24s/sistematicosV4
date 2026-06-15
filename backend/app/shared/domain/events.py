from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4


@dataclass(frozen=True)
class DomainEvent:
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: str = ""
    aggregate_id: UUID = field(default_factory=uuid4)
    aggregate_type: str = ""
    version: int = 1
    payload: dict[str, Any] = field(default_factory=dict)

