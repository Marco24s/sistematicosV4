from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from app.modules.assets.domain.models import Asset, TechnicalHistory
from app.modules.flight_operations.domain.models import (
    ConsumptionType,
    FlightHourConsumptionEvent,
    FlightSheet,
    FlightSheetStatus,
    InstalledAsset,
    Mission,
    MissionStatus,
    OperationalAlert,
    OperationalAlertSeverity,
    OperationalAlertStatus,
)
from app.modules.maintenance.domain.models import MaintenanceCounter
from app.shared.domain.exceptions import DomainError


@dataclass(frozen=True)
class FlightClosureInput:
    mission: Mission
    flight_sheet: FlightSheet
    aircraft: Asset
    aircraft_history: TechnicalHistory
    installed_assets: list[InstalledAsset]
    installed_asset_histories: dict[UUID, TechnicalHistory]
    maintenance_counters_by_asset_id: dict[UUID, list[MaintenanceCounter]] = field(default_factory=dict)
    has_flight_sheet_document: bool = False
    remaining_usage_threshold: int = 5
    cycles_consumed: int = 1


@dataclass(frozen=True)
class FlightClosureResult:
    consumption_events: list[FlightHourConsumptionEvent]
    alerts: list[OperationalAlert]


@dataclass(frozen=True)
class AirworthinessRisk:
    asset_id: UUID
    code: str
    message: str


@dataclass(frozen=True)
class AirworthinessRiskAssessment:
    aircraft_asset_id: UUID
    is_airworthy: bool
    risks: list[AirworthinessRisk]


class FlightOperationsService:
    def close_flight(self, closure: FlightClosureInput) -> FlightClosureResult:
        if not closure.has_flight_sheet_document:
            raise DomainError("OPERACIÓN DENEGADA: No se puede cerrar el vuelo sin el documento 'Flight Sheet' asociado.")
            
        flight_sheet = closure.flight_sheet
        if flight_sheet.status == FlightSheetStatus.CLOSED:
            raise DomainError("Flight sheet is already closed.")
        if flight_sheet.actual_hours_flown is None:
            raise DomainError("Actual hours flown are required before closing a flight.")
        if flight_sheet.actual_hours_flown <= 0:
            raise DomainError("Actual hours flown must be greater than zero.")
        if flight_sheet.aircraft_asset_id != closure.aircraft.id:
            raise DomainError("Flight sheet aircraft does not match closure aircraft.")
        if closure.aircraft_history.asset_id != closure.aircraft.id:
            raise DomainError("Aircraft technical history does not match aircraft asset.")

        hours = Decimal(flight_sheet.actual_hours_flown)
        cycles = closure.cycles_consumed
        affected_asset_ids = [closure.aircraft.id] + [installed.installed_asset_id for installed in closure.installed_assets]

        closure.aircraft_history.current_total_hours += hours
        closure.aircraft_history.current_total_cycles += cycles

        events = [
            self._build_consumption_event(
                flight_sheet_id=flight_sheet.id,
                asset_id=closure.aircraft.id,
                hours=hours,
                cycles=cycles,
            )
        ]

        for installed in closure.installed_assets:
            history = closure.installed_asset_histories.get(installed.installed_asset_id)
            if history is None:
                raise DomainError(f"Installed asset {installed.installed_asset_id} has no technical history.")
            if history.asset_id != installed.installed_asset_id:
                raise DomainError("Installed asset technical history does not match installed asset.")

            history.current_total_hours += hours
            history.current_total_cycles += cycles
            events.append(
                self._build_consumption_event(
                    flight_sheet_id=flight_sheet.id,
                    asset_id=installed.installed_asset_id,
                    hours=hours,
                    cycles=cycles,
                )
            )

        alerts: list[OperationalAlert] = []
        for asset_id in affected_asset_ids:
            counters = closure.maintenance_counters_by_asset_id.get(asset_id, [])
            for counter in counters:
                counter.current_usage += int(hours)
                counter.remaining_usage -= int(hours)
                if counter.remaining_usage <= closure.remaining_usage_threshold:
                    alerts.append(
                        OperationalAlert(
                            asset_id=asset_id,
                            flight_sheet_id=flight_sheet.id,
                            severity=self._alert_severity(counter.remaining_usage),
                            status=OperationalAlertStatus.OPEN,
                            alert_code="maintenance_threshold_reached",
                            message=(
                                "El asset alcanzo el umbral de vencimiento de mantenimiento "
                                f"con remaining_usage={counter.remaining_usage}."
                            ),
                        )
                    )

        flight_sheet.status = FlightSheetStatus.CLOSED
        closure.mission.status = MissionStatus.COMPLETED
        return FlightClosureResult(consumption_events=events, alerts=alerts)

    def detect_airworthiness_risk(
        self,
        aircraft: Asset,
        aircraft_history: TechnicalHistory,
        installed_asset_histories: list[TechnicalHistory],
        maintenance_counters_by_asset_id: dict[UUID, list[MaintenanceCounter]],
    ) -> AirworthinessRiskAssessment:
        risks: list[AirworthinessRisk] = []
        histories = [aircraft_history] + installed_asset_histories
        now = datetime.now(timezone.utc).date()

        for history in histories:
            if history.calendar_expiration and history.calendar_expiration <= now:
                risks.append(
                    AirworthinessRisk(
                        asset_id=history.asset_id,
                        code="calendar_expired",
                        message="El asset tiene vida calendario vencida.",
                    )
                )
            if history.preservation_expiration and history.preservation_expiration <= now:
                risks.append(
                    AirworthinessRisk(
                        asset_id=history.asset_id,
                        code="preservation_expired",
                        message="El asset tiene preservacion vencida.",
                    )
                )

        for asset_id, counters in maintenance_counters_by_asset_id.items():
            for counter in counters:
                if counter.remaining_usage <= 0:
                    risks.append(
                        AirworthinessRisk(
                            asset_id=asset_id,
                            code="maintenance_overdue",
                            message="El asset tiene mantenimiento vencido por consumo.",
                        )
                    )
                if counter.next_due and counter.next_due <= now:
                    risks.append(
                        AirworthinessRisk(
                            asset_id=asset_id,
                            code="inspection_overdue",
                            message="El asset tiene inspeccion vencida por calendario.",
                        )
                    )

        return AirworthinessRiskAssessment(
            aircraft_asset_id=aircraft.id,
            is_airworthy=len(risks) == 0,
            risks=risks,
        )

    def _build_consumption_event(
        self,
        flight_sheet_id: UUID,
        asset_id: UUID,
        hours: Decimal,
        cycles: int,
    ) -> FlightHourConsumptionEvent:
        return FlightHourConsumptionEvent(
            flight_sheet_id=flight_sheet_id,
            asset_id=asset_id,
            consumption_type=ConsumptionType.FLIGHT_HOURS,
            hours_consumed=hours,
            cycles_consumed=cycles,
            recorded_at=datetime.now(timezone.utc),
        )

    def _alert_severity(self, remaining_usage: int) -> OperationalAlertSeverity:
        if remaining_usage <= 0:
            return OperationalAlertSeverity.CRITICAL
        return OperationalAlertSeverity.WARNING
