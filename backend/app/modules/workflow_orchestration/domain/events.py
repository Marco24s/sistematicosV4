from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from app.shared.domain.events import DomainEvent


@dataclass(frozen=True)
class FlightClosedEvent(DomainEvent):
    event_type: str = "FlightClosedEvent"
    aggregate_type: str = "flight_operations"


@dataclass(frozen=True)
class AssetInstalledEvent(DomainEvent):
    event_type: str = "AssetInstalledEvent"
    aggregate_type: str = "flight_operations"


@dataclass(frozen=True)
class AssetRemovedEvent(DomainEvent):
    event_type: str = "AssetRemovedEvent"
    aggregate_type: str = "flight_operations"


@dataclass(frozen=True)
class FailureDetectedEvent(DomainEvent):
    event_type: str = "FailureDetectedEvent"
    aggregate_type: str = "maintenance"


@dataclass(frozen=True)
class MaintenanceRequestCreatedEvent(DomainEvent):
    event_type: str = "MaintenanceRequestCreatedEvent"
    aggregate_type: str = "arsenal_workflow"


@dataclass(frozen=True)
class RepairTaskCompletedEvent(DomainEvent):
    event_type: str = "RepairTaskCompletedEvent"
    aggregate_type: str = "arsenal_workflow"


@dataclass(frozen=True)
class QualityInspectionApprovedEvent(DomainEvent):
    event_type: str = "QualityInspectionApprovedEvent"
    aggregate_type: str = "arsenal_workflow"


@dataclass(frozen=True)
class ServiceReleasedEvent(DomainEvent):
    event_type: str = "ServiceReleasedEvent"
    aggregate_type: str = "arsenal_workflow"


@dataclass(frozen=True)
class PurchaseApprovedEvent(DomainEvent):
    event_type: str = "PurchaseApprovedEvent"
    aggregate_type: str = "supply_chain"


@dataclass(frozen=True)
class CertificationExpiredEvent(DomainEvent):
    event_type: str = "CertificationExpiredEvent"
    aggregate_type: str = "personnel_certification"
