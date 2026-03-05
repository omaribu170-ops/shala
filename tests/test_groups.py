import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
import uuid
from fastapi.testclient import TestClient
from main import app
from database import get_db
import models

client = TestClient(app)

def get_auth_token():
    phone = str(uuid.uuid4())[:10] # Unique to avoid 5 group limit crash in tests
    client.post("/auth/request-otp", params={"phone": phone})
    db = next(get_db())
    code = db.query(models.OTPCode).filter(models.OTPCode.phone == phone).first().code
    return client.post("/auth/verify-otp", params={"phone": phone, "code": code}).json()["token"]

def test_create_group():
    token = get_auth_token()
    payload = {"name": "Test Group", "phones": ["12345"]}
    response = client.post("/groups/create", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["name"] == "Test Group"

def test_get_groups():
    token = get_auth_token()
    response = client.get("/groups", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert type(response.json()) == list
