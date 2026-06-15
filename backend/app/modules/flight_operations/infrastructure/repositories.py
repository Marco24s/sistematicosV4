from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.flight_operations.domain.models import (
    FlightHourConsumptionEvent,
    FlightSheet,
    InstallationEvent,
    InstalledAsset,
    InstalledAssetStatus,
    Mission,
    OperationalAlert,
    OperationalAlertStatus,
)
from app.shared.infrastructure.repositories import BaseRepository


class MissionRepository(BaseRepository[Mission]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Mission)


class FlightSheetRepository(BaseRepository[FlightSheet]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, FlightSheet)


class InstalledAssetRepository(BaseRepository[InstalledAsset]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, InstalledAsset)

    def list_active_by_aircraft_id(self, aircraft_asset_id: UUID) -> list[InstalledAsset]:
        statement = select(InstalledAsset).where(
            InstalledAsset.aircraft_asset_id == aircraft_asset_id,
            InstalledAsset.status == InstalledAssetStatus.INSTALLED,
            InstalledAsset.is_deleted.is_(False),
        )
        return list(self.session.scalars(statement).all())


class InstallationEventRepository(BaseRepository[InstallationEvent]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, InstallationEvent)


class FlightHourConsumptionEventRepository(BaseRepository[FlightHourConsumptionEvent]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, FlightHourConsumptionEvent)

    def list_by_flight_sheet_id(self, flight_sheet_id: UUID) -> list[FlightHourConsumptionEvent]:
        statement = select(FlightHourConsumptionEvent).where(
            FlightHourConsumptionEvent.flight_sheet_id == flight_sheet_id,
            FlightHourConsumptionEvent.is_deleted.is_(False),
        )
        return list(self.session.scalars(statement).all())


class OperationalAlertRepository(BaseRepository[OperationalAlert]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, OperationalAlert)

    def list_open_by_asset_id(self, asset_id: UUID) -> list[OperationalAlert]:
        statement = select(OperationalAlert).where(
            OperationalAlert.asset_id == asset_id,
            OperationalAlert.status == OperationalAlertStatus.OPEN,
            OperationalAlert.is_deleted.is_(False),
        )
        return list(self.session.scalars(statement).all())
