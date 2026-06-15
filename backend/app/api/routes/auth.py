from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session
import bcrypt

from app.core.database import get_db
from app.core.security import create_jwt_token, verify_jwt_token
from app.modules.authorization.domain.models import SystemUser

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

class LoginRequest(BaseModel):
    username: str
    password: str

def get_current_user_payload(token: str = Depends(oauth2_scheme)) -> dict:
    payload = verify_jwt_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload

@router.post("/auth/login", tags=["auth"])
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(SystemUser).filter(SystemUser.username == request.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
        
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Usuario inactivo")
        
    if not bcrypt.checkpw(request.password.encode('utf-8'), user.password_hash.encode('utf-8')):
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
        
    # Generate token
    token = create_jwt_token({
        "sub": str(user.id),
        "username": user.username
    })
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": str(user.id)
    }

@router.get("/auth/me", tags=["auth"])
def get_me(payload: dict = Depends(get_current_user_payload)):
    return payload
