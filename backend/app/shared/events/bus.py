from collections.abc import Callable
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.shared.domain.events import DomainEvent
from app.shared.domain.commands import Command
from app.shared.infrastructure.event_store import StoredDomainEvent, StoredCommand

logger = logging.getLogger(__name__)

EventHandler = Callable[[DomainEvent, Session], None]
CommandHandler = Callable[[Command, Session], None]


class InMemoryEventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = {}
        self.published_events: list[DomainEvent] = []

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    def publish(self, event: DomainEvent, session: Session) -> None:
        self.published_events.append(event)

        # Idempotencia: Verificar si el evento ya fue procesado con éxito
        stmt = select(StoredDomainEvent).where(StoredDomainEvent.event_id == event.event_id)
        stored_event = session.scalars(stmt).first()

        if stored_event and stored_event.processed:
            logger.info(f"Event {event.event_id} already processed. Skipping.")
            return

        if not stored_event:
            stored_event = StoredDomainEvent(
                event_id=event.event_id,
                event_type=event.event_type,
                aggregate_type=event.aggregate_type,
                aggregate_id=event.aggregate_id,
                payload=event.payload,
                occurred_at=event.occurred_at,
                processed=False,
                retry_count=0
            )
            session.add(stored_event)
            session.flush()

        for handler in self._handlers.get(event.event_type, []):
            try:
                handler(event, session)
                stored_event.processed = True
                stored_event.processed_at = datetime.now(timezone.utc)
                stored_event.error_message = None
            except Exception as e:
                logger.error(f"Error handling event {event.event_id}: {str(e)}")
                stored_event.retry_count += 1
                stored_event.error_message = str(e)
                # No propagamos para no romper la transacción del publicador
                # y permitir reintentar de forma independiente.
                
        session.flush()

    def dispatch(self, session: Session) -> None:
        # Reintenta eventos que hayan fallado o que no se hayan completado
        stmt = select(StoredDomainEvent).where(StoredDomainEvent.processed == False).where(StoredDomainEvent.retry_count < 3)
        pending_events = session.scalars(stmt).all()

        for stored in pending_events:
            event = DomainEvent(
                event_id=stored.event_id,
                event_type=stored.event_type,
                aggregate_id=stored.aggregate_id,
                aggregate_type=stored.aggregate_type,
                payload=stored.payload,
                occurred_at=stored.occurred_at
            )
            for handler in self._handlers.get(stored.event_type, []):
                try:
                    handler(event, session)
                    stored.processed = True
                    stored.processed_at = datetime.now(timezone.utc)
                    stored.error_message = None
                except Exception as e:
                    stored.retry_count += 1
                    stored.error_message = str(e)
            session.flush()


class InMemoryCommandBus:
    def __init__(self) -> None:
        self._handlers: dict[str, CommandHandler] = {}
        self.dispatched_commands: list[Command] = []

    def register(self, command_type: str, handler: CommandHandler) -> None:
        self._handlers[command_type] = handler

    def dispatch(self, command: Command, session: Session) -> None:
        self.dispatched_commands.append(command)

        # Idempotencia: Verificar si el comando ya fue procesado con éxito
        stmt = select(StoredCommand).where(StoredCommand.command_id == command.command_id)
        stored_command = session.scalars(stmt).first()

        if stored_command and stored_command.processed:
            logger.info(f"Command {command.command_id} already processed. Skipping.")
            return

        if not stored_command:
            stored_command = StoredCommand(
                command_id=command.command_id,
                command_type=command.command_type,
                payload=command.payload,
                created_at=command.created_at,
                processed=False,
                retry_count=0
            )
            session.add(stored_command)
            session.flush()

        handler = self._handlers.get(command.command_type)
        if not handler:
            err_msg = f"No handler registered for command {command.command_type}"
            stored_command.error_message = err_msg
            session.flush()
            raise ValueError(err_msg)

        try:
            handler(command, session)
            stored_command.processed = True
            stored_command.processed_at = datetime.now(timezone.utc)
            stored_command.error_message = None
        except Exception as e:
            logger.error(f"Error handling command {command.command_id}: {str(e)}")
            stored_command.retry_count += 1
            stored_command.error_message = str(e)
            session.flush()
            raise e

        session.flush()

    def retry_failed_commands(self, session: Session) -> None:
        stmt = select(StoredCommand).where(StoredCommand.processed == False).where(StoredCommand.retry_count < 3)
        pending_commands = session.scalars(stmt).all()

        for stored in pending_commands:
            command = Command(
                command_id=stored.command_id,
                command_type=stored.command_type,
                payload=stored.payload,
                created_at=stored.created_at
            )
            handler = self._handlers.get(stored.command_type)
            if handler:
                try:
                    handler(command, session)
                    stored.processed = True
                    stored.processed_at = datetime.now(timezone.utc)
                    stored.error_message = None
                except Exception as e:
                    stored.retry_count += 1
                    stored.error_message = str(e)
            session.flush()


event_bus = InMemoryEventBus()
command_bus = InMemoryCommandBus()
