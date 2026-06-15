import os
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.modules.authorization.domain.models import SystemUser
from app.api.routes.auth import get_me
from starlette.requests import Request

db = SessionLocal()
user = db.query(SystemUser).filter_by(username='comando').first()
print("User found:", user is not None)
try:
    # Just testing a simple query to see if the DB is corrupted by the migration
    db.execute("SELECT 1")
    print("DB connection OK")
    
    # Testing the get_me function since login probably calls something similar, 
    # wait, login just does get_user and checks password, then returns JWT.
    
    # Let's test the login logic directly:
    from app.modules.authorization.application.services import get_user
    u = get_user(db, 'comando')
    print("User via get_user:", u.username if u else None)
    
except Exception as e:
    import traceback
    traceback.print_exc()
