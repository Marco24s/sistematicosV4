import sys
import os
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

response = client.post(
    "/api/v1/auth/login",
    json={"username": "comando", "password": "comando123"}
)

print(response.status_code)
print(response.json())
