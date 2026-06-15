import os
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.api.routes.auth import login_for_access_token
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends

db = SessionLocal()

class DummyForm:
    def __init__(self):
        self.username = 'comando'
        self.password = 'comando123'
        self.scopes = []
        self.client_id = None
        self.client_secret = None

form = DummyForm()
try:
    res = login_for_access_token(form_data=form, db=db)
    print("Login success:", res)
except Exception as e:
    import traceback
    traceback.print_exc()
