from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.modules.assets.domain.models import Asset, AssetTransfer, AssetType, TechnicalHistory
from app.shared.infrastructure.repositories import BaseRepository


class AssetTypeRepository(BaseRepository[AssetType]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, AssetType)


class AssetRepository(BaseRepository[Asset]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Asset)

    def get_with_operational_state(self, asset_id: UUID) -> Asset | None:
        statement = (
            select(Asset)
            .options(
                joinedload(Asset.asset_type),
                joinedload(Asset.technical_history),
                joinedload(Asset.maintenance_counters),
            )
            .where(Asset.id == asset_id, Asset.is_deleted.is_(False))
        )
        return self.session.scalars(statement).first()


class TechnicalHistoryRepository(BaseRepository[TechnicalHistory]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, TechnicalHistory)

    def get_by_asset_id(self, asset_id: UUID) -> TechnicalHistory | None:
        statement = select(TechnicalHistory).where(
            TechnicalHistory.asset_id == asset_id,
            TechnicalHistory.is_deleted.is_(False),
        )
        return self.session.scalars(statement).first()


class AssetTransferRepository(BaseRepository[AssetTransfer]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, AssetTransfer)
