from uuid import UUID, uuid4
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db

from app.shared.events.bus import command_bus
from app.shared.domain.commands import Command

router = APIRouter()

class ConsoleCommandRequest(BaseModel):
    command_type: str
    payload: dict

@router.post("/command-console/execute", tags=["command-console"])
def execute_console_command(request: ConsoleCommandRequest, db: Session = Depends(get_db)):
    cmd = Command(
        command_id=uuid4(),
        command_type=request.command_type,
        payload=request.payload,
        created_at=datetime.utcnow()
    )
    try:
        command_bus.dispatch(cmd, db)
        db.commit()
        return {
            "status": "SUCCESS",
            "command_id": str(cmd.command_id),
            "command_type": cmd.command_type
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Command execution failed: {str(e)}")
