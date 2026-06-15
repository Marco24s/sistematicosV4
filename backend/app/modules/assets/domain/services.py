from dataclasses import dataclass, field
from datetime import date
from uuid import UUID

from app.modules.assets.domain.models import (
    Asset,
    AssetCondition,
    AssetStatus,
    AssetTransfer,
    TechnicalHistory,
    TransferStatus,
    LifeLimitedComponent,
)
from app.modules.maintenance.domain.models import MaintenanceCounter
from app.shared.domain.exceptions import DomainError


@dataclass(frozen=True)
class AirworthinessFinding:
    code: str
    message: str
    asset_id: UUID | None = None
    serial_number: str | None = None


@dataclass(frozen=True)
class AirworthinessAssessment:
    asset_id: UUID
    is_airworthy: bool
    findings: list[AirworthinessFinding] = field(default_factory=list)


class AssetRegistrationService:
    def create_asset_with_history(
        self,
        asset: Asset,
        technical_history: TechnicalHistory,
    ) -> Asset:
        if asset.id and asset.id != technical_history.asset_id:
            raise DomainError("Technical history must belong to the same asset.")
        asset.technical_history = technical_history
        return asset


class AssetTransferService:
    def create_transfer(
        self,
        asset: Asset,
        transfer: AssetTransfer,
    ) -> AssetTransfer:
        if transfer.origin_department_id == transfer.destination_department_id:
            raise DomainError("Origin and destination departments must be different.")
        if asset.current_custodian_id and asset.current_custodian_id != transfer.origin_department_id:
            raise DomainError("Transfer origin must match current asset custodian.")

        transfer.status = TransferStatus.CREATED
        asset.current_status = AssetStatus.IN_TRANSFER
        return transfer

    def receive_transfer(self, asset: Asset, transfer: AssetTransfer) -> None:
        if transfer.status != TransferStatus.IN_TRANSIT:
            raise DomainError("Only transfers in transit can be received.")
        transfer.status = TransferStatus.RECEIVED
        asset.current_custodian_id = transfer.destination_department_id
        asset.current_status = AssetStatus.IN_STOCK


class AirworthinessPolicy:
    def assess(
        self,
        asset: Asset,
        maintenance_counters: list[MaintenanceCounter] | None = None,
    ) -> AirworthinessAssessment:
        findings: list[AirworthinessFinding] = []
        maintenance_counters = maintenance_counters or []
        today = date.today()

        if asset.condition != AssetCondition.SERVICEABLE:
            findings.append(
                AirworthinessFinding(
                    code="asset_not_serviceable",
                    message="El asset no esta en condicion SERVICEABLE.",
                    asset_id=asset.id,
                    serial_number=asset.serial_number,
                )
            )

        if asset.current_status in {AssetStatus.IN_TRANSFER, AssetStatus.IN_REPAIR, AssetStatus.WAITING_QUALITY, AssetStatus.GROUNDED}:
            findings.append(
                AirworthinessFinding(
                    code="asset_not_released",
                    message="El asset no esta en un estado operativo liberado.",
                    asset_id=asset.id,
                    serial_number=asset.serial_number,
                )
            )

        history = asset.technical_history
        if history is None:
            findings.append(
                AirworthinessFinding(
                    code="missing_technical_history",
                    message="El asset no tiene historial tecnico individual.",
                    asset_id=asset.id,
                    serial_number=asset.serial_number,
                )
            )
        else:
            if history.calendar_expiration and history.calendar_expiration <= today:
                findings.append(
                    AirworthinessFinding(
                        code="calendar_expired",
                        message="La vida calendario del asset esta vencida.",
                        asset_id=asset.id,
                        serial_number=asset.serial_number,
                    )
                )
            if history.preservation_expiration and history.preservation_expiration <= today:
                findings.append(
                    AirworthinessFinding(
                        code="preservation_expired",
                        message="La preservacion del asset esta vencida.",
                        asset_id=asset.id,
                        serial_number=asset.serial_number,
                    )
                )

        for counter in maintenance_counters:
            if counter.remaining_usage <= 0:
                findings.append(
                    AirworthinessFinding(
                        code="maintenance_due",
                        message="El asset tiene un programa de mantenimiento vencido.",
                        asset_id=asset.id,
                        serial_number=asset.serial_number,
                    )
                )
            if counter.next_due and counter.next_due <= today:
                findings.append(
                    AirworthinessFinding(
                        code="maintenance_calendar_due",
                        message="El asset tiene una proxima inspeccion vencida por calendario.",
                        asset_id=asset.id,
                        serial_number=asset.serial_number,
                    )
                )

        return AirworthinessAssessment(
            asset_id=asset.id,
            is_airworthy=len(findings) == 0,
            findings=findings,
        )


class LifeLimitedComponentService:
    def update_usage(
        self,
        component: LifeLimitedComponent,
        asset: Asset,
        hours: float,
        cycles: int
    ) -> None:
        if component.asset_id != asset.id:
            raise DomainError("LifeLimitedComponent does not match the asset.")
            
        component.consumed_hours += hours
        component.consumed_cycles += cycles
        component.remaining_hours = max(0.0, component.life_limit_hours - component.consumed_hours)
        component.remaining_cycles = max(0, component.life_limit_cycles - component.consumed_cycles)
        
        if component.remaining_hours <= 0.0 or component.remaining_cycles <= 0:
            asset.condition = AssetCondition.CONDEMNED
            asset.current_status = AssetStatus.SCRAPPED

