from datetime import date, datetime
from uuid import UUID
from app.shared.domain.exceptions import DomainError
from app.modules.flight_release_control.domain.models import FlightReleaseAuthorization
from app.modules.configuration_baseline.domain.models import AircraftBaselineConfiguration, ConfigurationDeviation
from app.modules.squadron_operations.domain.models import AircraftConfiguration
from app.modules.fod_management.domain.models import FODInspection, FODIncident

class FlightReleaseService:
    def release_aircraft(
        self,
        aircraft_id: UUID,
        authorized_by: str,
        authorization_type: str,
        active_config: AircraftConfiguration | None,
        baseline: AircraftBaselineConfiguration | None,
        deviations: list[ConfigurationDeviation],
        fod_inspections: list[FODInspection],
        fod_incidents: list[FODIncident],
        as_of: date | None = None
    ) -> FlightReleaseAuthorization:
        
        as_of = as_of or date.today()
        
        # 1. Foreign Object Damage (FOD) Control checks:
        for inspection in fod_inspections:
            if inspection.aircraft_id == aircraft_id and not inspection.cleared_for_operation:
                raise DomainError("FOD inspection failed. Flight release blocked.")
                
        # Block if there is any FOD incident matching the aircraft or its installed components
        installed_asset_ids = {aircraft_id}
        if active_config:
            installed_asset_ids.update({
                c.asset_id for c in active_config.mounted_components if c.status == "ACTIVE"
            })
            
        for incident in fod_incidents:
            if incident.asset_id in installed_asset_ids:
                raise DomainError("Unresolved FOD incident on aircraft or components. Flight release blocked.")

        # 2. Configuration deviation check:
        if active_config and baseline:
            approved_slots = baseline.approved_configuration_json.get("slots", {})
            mounted_slots = {
                c.position_code: c.asset.nomenclature for c in active_config.mounted_components if c.status == "ACTIVE"
            }
            
            mismatch = False
            for slot, nomenclature in approved_slots.items():
                if slot not in mounted_slots or mounted_slots[slot] != nomenclature:
                    mismatch = True
                    break
            
            for slot in mounted_slots:
                if slot not in approved_slots:
                    mismatch = True
                    break
                    
            if mismatch:
                # Require an active and approved deviation
                has_active_deviation = any(
                    dev.aircraft_id == aircraft_id
                    and dev.expiration_date >= as_of
                    for dev in deviations
                )
                if not has_active_deviation:
                    raise DomainError("Aircraft configuration mismatch. Flight release blocked without approved deviation.")
                    
        return FlightReleaseAuthorization(
            aircraft_id=aircraft_id,
            authorized_by=authorized_by,
            authorization_type=authorization_type,
            authorized_at=datetime.utcnow()
        )
