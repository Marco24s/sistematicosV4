from dataclasses import dataclass
from typing import Any
from uuid import UUID

from app.shared.domain.commands import Command


@dataclass(frozen=True)
class CreateMaintenanceRequestCommand(Command):
    command_type: str = "CreateMaintenanceRequestCommand"


@dataclass(frozen=True)
class CreateQualityInspectionCommand(Command):
    command_type: str = "CreateQualityInspectionCommand"


@dataclass(frozen=True)
class CreateServiceReleaseCommand(Command):
    command_type: str = "CreateServiceReleaseCommand"


@dataclass(frozen=True)
class UpdateTechnicalHistoryCommand(Command):
    command_type: str = "UpdateTechnicalHistoryCommand"


@dataclass(frozen=True)
class UpdateServiceStatusCommand(Command):
    command_type: str = "UpdateServiceStatusCommand"


@dataclass(frozen=True)
class CreateStockAvailabilityCommand(Command):
    command_type: str = "CreateStockAvailabilityCommand"


@dataclass(frozen=True)
class BlockAircraftCommand(Command):
    command_type: str = "BlockAircraftCommand"
