import asyncio
import logging
import time
from threading import Thread
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.shared.events.bus import event_bus, command_bus

logger = logging.getLogger(__name__)

class OutboxWorker:
    def __init__(self, interval_seconds: float = 2.0):
        self.interval_seconds = interval_seconds
        self.running = False
        self._thread = None

    def start(self):
        if self.running:
            return
        self.running = True
        self._thread = Thread(target=self._run_loop, daemon=True, name="OutboxWorkerThread")
        self._thread.start()
        logger.info("Outbox worker thread started successfully")

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=5)
            logger.info("Outbox worker thread stopped")

    def _run_loop(self):
        while self.running:
            try:
                with SessionLocal() as db:
                    # Dispatch pending outbox events (processed=False)
                    event_bus.dispatch(db)
                    
                    # Dispatch pending commands
                    command_bus.retry_failed_commands(db)
                    
                    db.commit()
            except Exception as e:
                logger.error(f"Error in outbox worker loop: {str(e)}")
            time.sleep(self.interval_seconds)

# Global singleton worker instance
outbox_worker = OutboxWorker()
