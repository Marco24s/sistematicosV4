from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.squadron_operations.domain.models import (
    AircraftConfiguration,
    AircraftInspectionProgram,
    AirworthinessBlock,
    MaintenanceAction,
    MountedComponent,
    MountedComponentStatus,
    SquadronInventoryMovement,
    SquadronQualityApproval,
    StatisticalControlRecord,
)
from app.shared.infrastructure.repositories import BaseRepository


class AircraftConfigurationRepository(BaseRepository[AircraftConfiguration]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, AircraftConfiguration)

    def get_active_by_aircraft_id(self, aircraft_asset_id: UUID) -> AircraftConfiguration | None:
        statement = select(AircraftConfiguration).where(
            AircraftConfiguration.aircraft_asset_id == aircraft_asset_id,
            AircraftConfiguration.active.is_(True),
            AircraftConfiguration.is_deleted.is_(False),
        )
        return self.session.scalars(statement).first()


class MountedComponentRepository(BaseRepository[MountedComponent]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, MountedComponent)

    def list_active_by_configuration_id(self, aircraft_configuration_id: UUID) -> list[MountedComponent]:
        statement = select(MountedComponent).where(
            MountedComponent.aircraft_configuration_id == aircraft_configuration_id,
            MountedComponent.status == MountedComponentStatus.ACTIVE,
            MountedComponent.is_deleted.is_(False),
        )
        return list(self.session.scalars(statement).all())


class AircraftInspectionProgramRepository(BaseRepository[AircraftInspectionProgram]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, AircraftInspectionProgram)


class StatisticalControlRecordRepository(BaseRepository[StatisticalControlRecord]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, StatisticalControlRecord)


class MaintenanceActionRepository(BaseRepository[MaintenanceAction]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, MaintenanceAction)


class SquadronQualityApprovalRepository(BaseRepository[SquadronQualityApproval]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, SquadronQualityApproval)


class SquadronInventoryMovementRepository(BaseRepository[SquadronInventoryMovement]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, SquadronInventoryMovement)


class AirworthinessBlockRepository(BaseRepository[AirworthinessBlock]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, AirworthinessBlock)
