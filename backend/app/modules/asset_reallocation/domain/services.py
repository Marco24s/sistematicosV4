from uuid import UUID
from datetime import datetime
from app.shared.domain.exceptions import DomainError
from app.modules.assets.domain.models import Asset, AssetStatus
from app.modules.asset_reallocation.domain.models import CannibalizationRequest

class CannibalizationService:
    def request_cannibalization(
        self,
        donor_aircraft: Asset,
        receiver_aircraft: Asset,
        component_asset: Asset,
        priority_reason: str,
        authorized_by: str
    ) -> CannibalizationRequest:
        
        # Degrade donor status to GROUNDED
        donor_aircraft.current_status = AssetStatus.GROUNDED
        
        return CannibalizationRequest(
            donor_aircraft_id=donor_aircraft.id,
            receiver_aircraft_id=receiver_aircraft.id,
            component_asset_id=component_asset.id,
            priority_reason=priority_reason,
            authorized_by=authorized_by,
            approved_at=datetime.utcnow()
        )

    def complete_installation(
        self,
        request: CannibalizationRequest,
        receiver_aircraft: Asset,
        component_asset: Asset
    ) -> None:
        if request.component_asset_id != component_asset.id:
            raise DomainError("Component asset does not match the cannibalization request.")
            
        # Re-verify and set receivers' status
        component_asset.current_status = AssetStatus.INSTALLED
        receiver_aircraft.current_status = AssetStatus.RELEASED
