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
def get_me(payload: dict = Depends(get_current_user_payload), db: Session = Depends(get_db)):
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
        
    user = db.get(SystemUser, UUID(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
    # Get active assignment
    from app.modules.authorization.domain.models import UserAssignment
    from app.modules.organization.domain.models import Organization, Department
    
    assignment = db.query(UserAssignment).filter(UserAssignment.user_id == user.id, UserAssignment.active == True).first()
    
    profile = {
        "id": str(user.id),
        "username": user.username,
        "role_name": "NONE",
        "organization_name": "UNASSIGNED",
        "department_name": "UNASSIGNED",
        "permissions": []
    }
    
    if assignment:
        role = assignment.role
        org = db.get(Organization, assignment.organization_id)
        dept = db.get(Department, assignment.department_id)
        
        if role:
            profile["role_name"] = role.name
            profile["permissions"] = [p.name for p in role.permissions]
        if org:
            profile["organization_name"] = org.name
        if dept:
            profile["department_name"] = dept.name
            
    return profile
