from sqlalchemy.orm import Session

from app.modules.organization.domain.models import Department, Organization
from app.shared.infrastructure.repositories import BaseRepository


class OrganizationRepository(BaseRepository[Organization]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Organization)


class DepartmentRepository(BaseRepository[Department]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Department)
