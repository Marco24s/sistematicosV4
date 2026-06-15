import base64
import hmac
import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

SECRET_KEY = "SECRET_MILITARY_KEY_AVIONICS_SYSTEM_TOP_SECRET"

def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

def base64url_decode(data: str) -> bytes:
    padding = '=' * (4 - (len(data) % 4))
    return base64.urlsafe_b64decode(data + padding)

def create_jwt_token(payload: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    
    # Set expiration
    payload_copy = payload.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=8)
    payload_copy["exp"] = int(expire.timestamp())
    
    header_json = json.dumps(header, separators=(',', ':')).encode('utf-8')
    payload_json = json.dumps(payload_copy, separators=(',', ':')).encode('utf-8')
    
    encoded_header = base64url_encode(header_json)
    encoded_payload = base64url_encode(payload_json)
    
    signature_base = f"{encoded_header}.{encoded_payload}".encode('utf-8')
    signature = hmac.new(SECRET_KEY.encode('utf-8'), signature_base, hashlib.sha256).digest()
    encoded_signature = base64url_encode(signature)
    
    return f"{encoded_header}.{encoded_payload}.{encoded_signature}"

def verify_jwt_token(token: str) -> Optional[dict[str, Any]]:
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
            
        encoded_header, encoded_payload, encoded_signature = parts
        
        # Verify signature
        signature_base = f"{encoded_header}.{encoded_payload}".encode('utf-8')
        expected_sig = hmac.new(SECRET_KEY.encode('utf-8'), signature_base, hashlib.sha256).digest()
        expected_sig_encoded = base64url_encode(expected_sig)
        
        if not hmac.compare_digest(encoded_signature, expected_sig_encoded):
            return None
            
        # Decode payload
        payload_bytes = base64url_decode(encoded_payload)
        payload = json.loads(payload_bytes.decode('utf-8'))
        
        # Verify expiration
        exp = payload.get("exp")
        if exp and datetime.now(timezone.utc).timestamp() > exp:
            return None
            
        return payload
    except Exception:
        return None

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from uuid import UUID
from app.core.database import get_db
from app.modules.authorization.domain.policies import AuthorizationPolicy

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_user_payload(token: str = Depends(oauth2_scheme)) -> dict:
    payload = verify_jwt_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload

def check_permission(permission_name: str):
    def dependency(
        user_payload: dict = Depends(get_current_user_payload),
        db: Session = Depends(get_db)
    ):
        user_id = UUID(user_payload["sub"])
        
        policy = AuthorizationPolicy()
        has_perm = policy._has_permission(user_id, permission_name, db)
        if not has_perm:
            raise HTTPException(status_code=403, detail=f"Forbidden: Missing permission {permission_name}")
            
        return user_id
    return dependency
