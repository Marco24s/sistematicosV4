from datetime import datetime, timezone
from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

ModelT = TypeVar("ModelT")


class BaseRepository(Generic[ModelT]):
    model: type[ModelT]

    def __init__(self, session: Session, model: type[ModelT]) -> None:
        self.session = session
        self.model = model

    def query(self, include_deleted: bool = False) -> Select[tuple[ModelT]]:
        statement = select(self.model)
        if not include_deleted and hasattr(self.model, "is_deleted"):
            statement = statement.where(self.model.is_deleted.is_(False))
        return statement

    def get(self, entity_id: UUID, include_deleted: bool = False) -> ModelT | None:
        statement = self.query(include_deleted).where(self.model.id == entity_id)
        return self.session.scalars(statement).first()

    def list(self, include_deleted: bool = False) -> list[ModelT]:
        return list(self.session.scalars(self.query(include_deleted)).all())

    def add(self, entity: ModelT, commit: bool = False) -> ModelT:
        self.session.add(entity)
        if commit:
            self.session.commit()
            self.session.refresh(entity)
        return entity

    def update(self, entity: ModelT, values: dict[str, Any], commit: bool = False) -> ModelT:
        for key, value in values.items():
            setattr(entity, key, value)
        if commit:
            self.session.commit()
            self.session.refresh(entity)
        return entity

    def soft_delete(self, entity: ModelT, commit: bool = False) -> ModelT:
        if not hasattr(entity, "is_deleted"):
            raise TypeError(f"{type(entity).__name__} does not support soft delete")
        entity.is_deleted = True
        entity.deleted_at = datetime.now(timezone.utc)
        if commit:
            self.session.commit()
            self.session.refresh(entity)
        return entity
