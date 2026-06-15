from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.shared.domain.exceptions import DomainError
from app.modules.authorization.domain.models import UserAssignment, DigitalSignatureCertificate, SecurityAuditEvent, OrganizationRole


class AuthorizationPolicy:
    def _log_violation(self, user_id: UUID, event_type: str, action: str, details: str, session: Session) -> None:
        event = SecurityAuditEvent(
            user_id=user_id,
            event_type=event_type,
            action_attempted=action,
            details=details,
            timestamp=datetime.now(timezone.utc)
        )
        session.add(event)
        session.flush()

    def _has_permission(self, user_id: UUID, permission_name: str, session: Session, organization_id: UUID | None = None, department_id: UUID | None = None) -> bool:
        stmt = select(UserAssignment).where(UserAssignment.user_id == user_id).where(UserAssignment.active == True)
        if organization_id:
            stmt = stmt.where(UserAssignment.organization_id == organization_id)
        if department_id:
            stmt = stmt.where(UserAssignment.department_id == department_id)
            
        assignments = session.scalars(stmt).all()
        for assignment in assignments:
            role = assignment.role
            for perm in role.permissions:
                if perm.name == permission_name:
                    return True
        return False

    def can_create_mission(self, user_id: UUID, organization_id: UUID, session: Session) -> bool:
        allowed = self._has_permission(user_id, "CREATE_MISSION", session, organization_id=organization_id)
        if not allowed:
            self._log_violation(user_id, "PERMISSION_DENIED", "CREATE_MISSION", f"User tried to create mission in org {organization_id}", session)
            raise DomainError("Unauthorized to create mission in this organization")
        return True

    def can_close_flight(self, user_id: UUID, session: Session) -> bool:
        allowed = self._has_permission(user_id, "CLOSE_FLIGHT", session)
        if not allowed:
            self._log_violation(user_id, "PERMISSION_DENIED", "CLOSE_FLIGHT", "User tried to close flight sheet", session)
            raise DomainError("Unauthorized to close flight sheet")
        return True

    def can_install_component(self, user_id: UUID, department_id: UUID, session: Session) -> bool:
        allowed = self._has_permission(user_id, "INSTALL_COMPONENT", session, department_id=department_id)
        if not allowed:
            self._log_violation(user_id, "PERMISSION_DENIED", "INSTALL_COMPONENT", f"User tried to install component in department {department_id}", session)
            raise DomainError("Unauthorized to install components in this department")
        return True

    def can_release_aircraft(self, user_id: UUID, session: Session) -> bool:
        allowed = self._has_permission(user_id, "VALIDATE_FLIGHT_RELEASE", session)
        if not allowed:
            self._log_violation(user_id, "PERMISSION_DENIED", "VALIDATE_FLIGHT_RELEASE", "User tried to validate flight release", session)
            raise DomainError("Unauthorized to release aircraft for flight operations")
        return True

    def can_start_repair(self, user_id: UUID, session: Session) -> bool:
        allowed = self._has_permission(user_id, "AUTHORIZE_REPAIR_TASK", session)
        if not allowed:
            self._log_violation(user_id, "PERMISSION_DENIED", "AUTHORIZE_REPAIR_TASK", "User tried to authorize repair task", session)
            raise DomainError("Unauthorized to start repair tasks")
        return True

    def can_approve_quality(self, user_id: UUID, signature_serial: str, session: Session) -> bool:
        # 1. Validar el permiso
        allowed = self._has_permission(user_id, "APPROVE_QUALITY_INSPECTION", session)
        if not allowed:
            self._log_violation(user_id, "PERMISSION_DENIED", "APPROVE_QUALITY_INSPECTION", "User tried to approve quality inspection without permission", session)
            raise DomainError("Unauthorized to approve quality inspections")

        # 2. Validar certificado digital
        stmt = select(DigitalSignatureCertificate).where(DigitalSignatureCertificate.user_id == user_id).where(DigitalSignatureCertificate.certificate_serial == signature_serial).where(DigitalSignatureCertificate.active == True)
        cert = session.scalars(stmt).first()

        if not cert:
            self._log_violation(user_id, "SIGNATURE_VIOLATION", "APPROVE_QUALITY_INSPECTION", f"User tried to sign with invalid/missing cert serial {signature_serial}", session)
            raise DomainError("No active digital signature certificate found for this user")

        if cert.expires_at < datetime.utcnow():
            self._log_violation(user_id, "SIGNATURE_EXPIRED", "APPROVE_QUALITY_INSPECTION", f"User certificate {signature_serial} has expired", session)
            raise DomainError("Digital signature certificate has expired")


        # Registro de aprobación de seguridad exitosa
        self._log_violation(user_id, "CRITICAL_APPROVAL", "APPROVE_QUALITY_INSPECTION", f"Quality inspection approved with signature serial {signature_serial}", session)
        return True

    def can_issue_grounding(self, user_id: UUID, session: Session) -> bool:
        allowed = self._has_permission(user_id, "ISSUE_AIRWORTHINESS_BLOCK", session)
        if not allowed:
            self._log_violation(user_id, "PERMISSION_DENIED", "ISSUE_AIRWORTHINESS_BLOCK", "User tried to issue aircraft grounding block", session)
            raise DomainError("Unauthorized to ground aircraft")
        return True

    def can_approve_purchase(self, user_id: UUID, session: Session) -> bool:
        allowed = self._has_permission(user_id, "APPROVE_PURCHASE_ORDER", session)
        if not allowed:
            self._log_violation(user_id, "PERMISSION_DENIED", "APPROVE_PURCHASE_ORDER", "User tried to approve purchase order", session)
            raise DomainError("Unauthorized to approve purchase orders")
        return True
