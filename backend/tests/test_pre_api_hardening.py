import pytest
from datetime import date, datetime, timedelta
from uuid import uuid4

from app.shared.domain.exceptions import DomainError

# Imports from various modules
from app.modules.assets.domain.models import Asset, AssetStatus, AssetCondition, AssetClassification, LifeLimitedComponent
from app.modules.assets.domain.services import LifeLimitedComponentService

from app.modules.asset_reallocation.domain.models import CannibalizationRequest
from app.modules.asset_reallocation.domain.services import CannibalizationService

from app.modules.configuration_baseline.domain.models import AircraftBaselineConfiguration, ConfigurationDeviation
from app.modules.squadron_operations.domain.models import AircraftConfiguration, MountedComponent
from app.modules.fod_management.domain.models import FODInspection, FODIncident
from app.modules.flight_release_control.domain.services import FlightReleaseService

from app.modules.engine_management.domain.models import EngineAssembly
from app.modules.engine_management.domain.services import EngineTrendService

from app.modules.maintenance.domain.models import MaintenanceTaskExecution, MaintenanceDualInspection
from app.modules.maintenance.domain.services import MaintenanceExecutionService
from app.modules.personnel_certification.domain.models import TechnicianProfile
from app.modules.authorization.domain.models import DigitalSignatureCertificate
from app.modules.tool_calibration.domain.models import ToolUsageRecord
from app.modules.maintenance_human_factors.domain.models import HumanFactorIncident


# 1. Cannibalization Control Test
def test_cannibalization_status_cascade():
    service = CannibalizationService()
    
    donor = Asset(id=uuid4(), asset_type_id=uuid4(), part_number="DN-001", serial_number="SN-DN", nomenclature="Donor Aircraft", current_status=AssetStatus.RELEASED)
    receiver = Asset(id=uuid4(), asset_type_id=uuid4(), part_number="RC-001", serial_number="SN-RC", nomenclature="Receiver Aircraft", current_status=AssetStatus.GROUNDED)
    comp = Asset(id=uuid4(), asset_type_id=uuid4(), part_number="CP-001", serial_number="SN-CP", nomenclature="Engine Component", current_status=AssetStatus.RELEASED)
    
    req = service.request_cannibalization(donor, receiver, comp, "COMBAT_PRIORITY", "Commanding Officer")
    
    assert donor.current_status == AssetStatus.GROUNDED
    assert req.donor_aircraft_id == donor.id
    assert req.receiver_aircraft_id == receiver.id
    
    service.complete_installation(req, receiver, comp)
    
    assert comp.current_status == AssetStatus.INSTALLED
    assert receiver.current_status == AssetStatus.RELEASED


# 2. Quality Sign-off Validation Pipeline Tests
def test_maintenance_signoff_technician_inactive():
    service = MaintenanceExecutionService()
    exec_task = MaintenanceTaskExecution(task_id=uuid4(), asset_id=uuid4(), technician_id=uuid4())
    tech = TechnicianProfile(id=exec_task.technician_id, technical_code="T01", join_date=date.today(), current_level="LEVEL_A", active=False)
    cert = DigitalSignatureCertificate(user_id=tech.id, certificate_serial="SIG-01", issued_at=datetime.utcnow(), expires_at=datetime.utcnow() + timedelta(days=10), active=True)
    
    with pytest.raises(DomainError, match="Technician profile is inactive"):
        service.validate_and_signoff(exec_task, tech, cert, [], [])


def test_maintenance_signoff_human_factors_suspension():
    service = MaintenanceExecutionService()
    exec_task = MaintenanceTaskExecution(task_id=uuid4(), asset_id=uuid4(), technician_id=uuid4())
    tech = TechnicianProfile(id=exec_task.technician_id, technical_code="T01", join_date=date.today(), current_level="LEVEL_A", active=True)
    cert = DigitalSignatureCertificate(user_id=tech.id, certificate_serial="SIG-01", issued_at=datetime.utcnow(), expires_at=datetime.utcnow() + timedelta(days=10), active=True)
    
    incidents = [
        HumanFactorIncident(technician_id=tech.id, task_id=uuid4(), asset_id=uuid4(), incident_type="IMPROPER_TORQUE", severity_level="CRITICAL")
    ]
    
    with pytest.raises(DomainError, match="Technician is suspended due to critical/high human factor incidents"):
        service.validate_and_signoff(exec_task, tech, cert, [], incidents)


def test_maintenance_signoff_tool_uncalibrated_or_damaged():
    service = MaintenanceExecutionService()
    exec_task = MaintenanceTaskExecution(task_id=uuid4(), asset_id=uuid4(), technician_id=uuid4())
    tech = TechnicianProfile(id=exec_task.technician_id, technical_code="T01", join_date=date.today(), current_level="LEVEL_A", active=True)
    cert = DigitalSignatureCertificate(user_id=tech.id, certificate_serial="SIG-01", issued_at=datetime.utcnow(), expires_at=datetime.utcnow() + timedelta(days=10), active=True)
    
    usage1 = ToolUsageRecord(tool_id=uuid4(), technician_id=tech.id, task_id=exec_task.task_id, checked_out_at=datetime.utcnow(), calibration_valid_at_usage=False)
    with pytest.raises(DomainError, match="Tool calibration was invalid at time of usage"):
        service.validate_and_signoff(exec_task, tech, cert, [usage1], [])
        
    usage2 = ToolUsageRecord(tool_id=uuid4(), technician_id=tech.id, task_id=exec_task.task_id, checked_out_at=datetime.utcnow(), calibration_valid_at_usage=True, damage_detected=True)
    with pytest.raises(DomainError, match="Tool was returned damaged"):
        service.validate_and_signoff(exec_task, tech, cert, [usage2], [])


def test_maintenance_signoff_expired_signature():
    service = MaintenanceExecutionService()
    exec_task = MaintenanceTaskExecution(task_id=uuid4(), asset_id=uuid4(), technician_id=uuid4())
    tech = TechnicianProfile(id=exec_task.technician_id, technical_code="T01", join_date=date.today(), current_level="LEVEL_A", active=True)
    cert = DigitalSignatureCertificate(user_id=tech.id, certificate_serial="SIG-01", issued_at=datetime.utcnow() - timedelta(days=20), expires_at=datetime.utcnow() - timedelta(days=1), active=True)
    
    with pytest.raises(DomainError, match="Digital signature certificate has expired"):
        service.validate_and_signoff(exec_task, tech, cert, [], [])


def test_maintenance_signoff_critical_dual_inspection():
    service = MaintenanceExecutionService()
    exec_task = MaintenanceTaskExecution(task_id=uuid4(), asset_id=uuid4(), technician_id=uuid4())
    tech = TechnicianProfile(id=exec_task.technician_id, technical_code="T01", join_date=date.today(), current_level="LEVEL_A", active=True)
    cert = DigitalSignatureCertificate(user_id=tech.id, certificate_serial="SIG-01", issued_at=datetime.utcnow(), expires_at=datetime.utcnow() + timedelta(days=10), active=True)
    
    with pytest.raises(DomainError, match="Critical task requires a dual inspection"):
        service.validate_and_signoff(exec_task, tech, cert, [], [], is_critical=True)
        
    dual = MaintenanceDualInspection(execution_id=exec_task.id, inspector_id=uuid4(), second_inspector_id=uuid4(), approval_status="PENDING")
    with pytest.raises(DomainError, match="Dual inspection has not been approved"):
        service.validate_and_signoff(exec_task, tech, cert, [], [], dual_inspection=dual, is_critical=True)
        
    dual.approval_status = "APPROVED"
    inspector1 = TechnicianProfile(id=dual.inspector_id, technical_code="I01", join_date=date.today(), current_level="LEVEL_B", active=True)
    inspector2 = TechnicianProfile(id=dual.second_inspector_id, technical_code="I02", join_date=date.today(), current_level="INSPECTOR", active=True)
    
    with pytest.raises(DomainError, match="Inspectors must be active and have INSPECTOR certification level"):
        service.validate_and_signoff(exec_task, tech, cert, [], [], dual_inspection=dual, inspectors_profiles=[inspector1, inspector2], is_critical=True)


# 3. Life-Limited Component Test
def test_life_limited_component_condemnation():
    service = LifeLimitedComponentService()
    
    asset = Asset(id=uuid4(), asset_type_id=uuid4(), part_number="PN-001", serial_number="SN-001", nomenclature="Rotor Blade", condition=AssetCondition.SERVICEABLE, current_status=AssetStatus.IN_STOCK)
    comp = LifeLimitedComponent(asset_id=asset.id, life_limit_hours=1000.0, life_limit_cycles=500, consumed_hours=900.0, consumed_cycles=400, remaining_hours=100.0, remaining_cycles=100)
    
    service.update_usage(comp, asset, 50.0, 50)
    assert asset.condition == AssetCondition.SERVICEABLE
    assert asset.current_status == AssetStatus.IN_STOCK
    assert comp.remaining_hours == 50.0
    
    service.update_usage(comp, asset, 100.0, 10)
    assert asset.condition == AssetCondition.CONDEMNED
    assert asset.current_status == AssetStatus.SCRAPPED
    assert comp.remaining_hours == 0.0


# 4. Flight Release Control Test
def test_flight_release_deviation_and_fod_blocks():
    service = FlightReleaseService()
    aircraft_id = uuid4()
    
    # Baseline & Config Setup
    baseline = AircraftBaselineConfiguration(aircraft_model_id=uuid4(), approved_configuration_json={"slots": {"SLOT-1": "Turbine"}}, approved_by_engineering="Eng", revision_number="1", certification_date=date.today())
    
    comp_asset = Asset(id=uuid4(), asset_type_id=uuid4(), part_number="P-01", serial_number="S-01", nomenclature="Turbine")
    
    # Correct config
    active_config = AircraftConfiguration(aircraft_asset_id=aircraft_id, configuration_name="Alpha", active=True)
    active_config.mounted_components = [
        MountedComponent(aircraft_configuration_id=active_config.id, asset_id=comp_asset.id, asset=comp_asset, position_code="SLOT-1", installation_date=datetime.utcnow(), installed_by="Me", status="ACTIVE")
    ]
    
    # Case A: Happy path configuration baseline matches
    auth = service.release_aircraft(aircraft_id, "Captain", "NORMAL_RELEASE", active_config, baseline, [], [], [])
    assert auth.aircraft_id == aircraft_id
    
    # Case B: FOD inspection failed blocks
    fod_insp = FODInspection(aircraft_id=aircraft_id, inspection_location="Engine Bay", performed_by="Crew", cleared_for_operation=False)
    with pytest.raises(DomainError, match="FOD inspection failed"):
        service.release_aircraft(aircraft_id, "Captain", "NORMAL_RELEASE", active_config, baseline, [], [fod_insp], [])
        
    # Case C: FOD incident blocks
    fod_inc = FODIncident(asset_id=aircraft_id, incident_description="Metal scrap on intake", severity="HIGH", foreign_object_type="Metal")
    with pytest.raises(DomainError, match="Unresolved FOD incident"):
        service.release_aircraft(aircraft_id, "Captain", "NORMAL_RELEASE", active_config, baseline, [], [], [fod_inc])

    # Case D: Configuration mismatch (no turbine mounted, but mismatch in name/nomenclature or missing slot)
    active_config.mounted_components[0].status = "REMOVED" # slot empty
    with pytest.raises(DomainError, match="Aircraft configuration mismatch"):
        service.release_aircraft(aircraft_id, "Captain", "NORMAL_RELEASE", active_config, baseline, [], [], [])
        
    # Case E: Deviation approved bypasses mismatch block
    dev = ConfigurationDeviation(aircraft_id=aircraft_id, deviation_type="TEMPORARY_MODIFICATION", approved_by="Gen", justification="SAR Emergency", expiration_date=date.today() + timedelta(days=1))
    auth_dev = service.release_aircraft(aircraft_id, "Captain", "NORMAL_RELEASE", active_config, baseline, [dev], [], [])
    assert auth_dev.aircraft_id == aircraft_id


# 5. Engine Trend Monitoring Test
def test_engine_trend_and_oil_alarms():
    service = EngineTrendService()
    
    engine_asset = Asset(id=uuid4(), asset_type_id=uuid4(), part_number="E-01", serial_number="S-E01", nomenclature="GE-T700", condition=AssetCondition.SERVICEABLE, current_status=AssetStatus.RELEASED)
    assembly = EngineAssembly(id=uuid4(), asset_id=engine_asset.id, engine_model="GE-T700", serial_number="S-E01")
    
    # Normal trend
    trend, event = service.record_trend(assembly, engine_asset, turbine_temperature_c=650.0, oil_pressure_psi=45.0, vibration_level=1.2, egt_c=700.0, oil_temperature_c=90.0)
    assert event is None
    assert engine_asset.current_status == AssetStatus.RELEASED
    
    # Exceeded temperature limit trend
    trend_hot, event_hot = service.record_trend(assembly, engine_asset, turbine_temperature_c=650.0, oil_pressure_psi=45.0, vibration_level=1.2, egt_c=810.0, oil_temperature_c=90.0)
    assert event_hot is not None
    assert engine_asset.current_status == AssetStatus.GROUNDED
    assert engine_asset.condition == AssetCondition.UNSERVICEABLE
    assert "egt_c" in event_hot.payload
    
    # Reset status
    engine_asset.current_status = AssetStatus.RELEASED
    engine_asset.condition = AssetCondition.SERVICEABLE
    
    # Normal oil analysis
    oil, event_oil = service.record_oil_analysis(assembly, engine_asset, iron_ppm=10.0, copper_ppm=5.0, silicon_ppm=2.0)
    assert event_oil is None
    
    # Critical wear metal detection
    oil_crit, event_oil_crit = service.record_oil_analysis(assembly, engine_asset, iron_ppm=55.0, copper_ppm=5.0, silicon_ppm=2.0)
    assert event_oil_crit is not None
    assert engine_asset.current_status == AssetStatus.GROUNDED
    assert engine_asset.condition == AssetCondition.UNSERVICEABLE
