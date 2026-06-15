from uuid import UUID
from datetime import datetime, date
from app.shared.domain.exceptions import DomainError
from app.modules.assets.domain.models import Asset, AssetStatus, AssetCondition
from app.modules.engine_management.domain.models import EngineAssembly, EngineTrendMonitoring, OilAnalysisRecord
from app.modules.engine_management.domain.events import EngineInspectionRequiredEvent

class EngineTrendService:
    def record_trend(
        self,
        engine_assembly: EngineAssembly,
        engine_asset: Asset,
        turbine_temperature_c: float,
        oil_pressure_psi: float,
        vibration_level: float,
        egt_c: float = 0.0,
        torque_percent: float = 0.0,
        n1_percent: float = 0.0,
        n2_percent: float = 0.0,
        fuel_flow_gph: float = 0.0,
        oil_temperature_c: float = 0.0
    ) -> tuple[EngineTrendMonitoring, EngineInspectionRequiredEvent | None]:
        
        # Check thresholds
        requires_inspection = (
            egt_c > 800.0 or
            vibration_level > 2.5 or
            oil_pressure_psi < 30.0 or
            oil_temperature_c > 115.0 or
            turbine_temperature_c > 850.0
        )
        
        trend = EngineTrendMonitoring(
            engine_assembly_id=engine_assembly.id,
            recorded_at=datetime.utcnow(),
            turbine_temperature_c=turbine_temperature_c,
            oil_pressure_psi=oil_pressure_psi,
            vibration_level=vibration_level,
            egt_c=egt_c,
            torque_percent=torque_percent,
            n1_percent=n1_percent,
            n2_percent=n2_percent,
            fuel_flow_gph=fuel_flow_gph,
            oil_temperature_c=oil_temperature_c
        )
        
        event = None
        if requires_inspection:
            engine_asset.current_status = AssetStatus.GROUNDED
            engine_asset.condition = AssetCondition.UNSERVICEABLE
            event = EngineInspectionRequiredEvent(
                aggregate_id=engine_assembly.id,
                payload={
                    "reason": "Exceeded safe operating parameter limit in trend monitoring",
                    "egt_c": egt_c,
                    "vibration_level": vibration_level,
                    "oil_pressure_psi": oil_pressure_psi,
                    "oil_temperature_c": oil_temperature_c,
                    "turbine_temperature_c": turbine_temperature_c
                }
            )
            
        return trend, event

    def record_oil_analysis(
        self,
        engine_assembly: EngineAssembly,
        engine_asset: Asset,
        iron_ppm: float,
        copper_ppm: float,
        silicon_ppm: float,
        aluminum_ppm: float = 0.0,
        chrome_ppm: float = 0.0,
        nickel_ppm: float = 0.0,
        contamination_detected: bool = False
    ) -> tuple[OilAnalysisRecord, EngineInspectionRequiredEvent | None]:
        
        critical_metal = (
            iron_ppm > 50.0 or
            copper_ppm > 20.0 or
            silicon_ppm > 15.0 or
            aluminum_ppm > 30.0 or
            chrome_ppm > 10.0 or
            nickel_ppm > 10.0
        )
        
        is_critical = critical_metal or contamination_detected
        verdict = "CRITICAL" if is_critical else "NORMAL"
        
        record = OilAnalysisRecord(
            engine_assembly_id=engine_assembly.id,
            sampled_at=date.today(),
            iron_ppm=iron_ppm,
            copper_ppm=copper_ppm,
            silicon_ppm=silicon_ppm,
            aluminum_ppm=aluminum_ppm,
            chrome_ppm=chrome_ppm,
            nickel_ppm=nickel_ppm,
            contamination_detected=contamination_detected,
            verdict=verdict
        )
        
        event = None
        if is_critical:
            engine_asset.current_status = AssetStatus.GROUNDED
            engine_asset.condition = AssetCondition.UNSERVICEABLE
            event = EngineInspectionRequiredEvent(
                aggregate_id=engine_assembly.id,
                payload={
                    "reason": "Critical engine wear metals or contamination detected in oil analysis",
                    "iron_ppm": iron_ppm,
                    "copper_ppm": copper_ppm,
                    "silicon_ppm": silicon_ppm,
                    "aluminum_ppm": aluminum_ppm,
                    "chrome_ppm": chrome_ppm,
                    "nickel_ppm": nickel_ppm,
                    "contamination_detected": contamination_detected
                }
            )
            
        return record, event
