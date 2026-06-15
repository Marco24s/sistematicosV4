from uuid import UUID
from sqlalchemy.orm import Session

class SquadronOperationsApplicationService:
    def block_aircraft(
        self,
        aircraft_id: UUID,
        reason: str,
        session: Session
    ) -> None:
        from app.modules.squadron_operations.domain.models import AirworthinessBlock
        from datetime import datetime, timezone
        
        block = AirworthinessBlock(
            aircraft_asset_id=aircraft_id,
            reason=reason,
            blocked_since=datetime.now(timezone.utc),
            severity="GROUNDING",
            active=True
        )
        session.add(block)
        session.flush()

    def block_technician_tasks(
        self,
        technician_id: UUID,
        session: Session
    ) -> None:
        # Registra una inactividad del técnico o bloquea sus tareas autorizadas
        from app.modules.personnel_certification.domain.models import TaskAuthorization
        from sqlalchemy import select
        
        stmt = select(TaskAuthorization).where(TaskAuthorization.technician_profile_id == technician_id)
        authorizations = session.scalars(stmt).all()
        for auth in authorizations:
            auth.authorized = False
        session.flush()
