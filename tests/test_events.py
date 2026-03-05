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
    phone = str(uuid.uuid4())[:10]
    client.post("/auth/request-otp", params={"phone": phone})
    db = next(get_db())
    code = db.query(models.OTPCode).filter(models.OTPCode.phone == phone).first().code
    return client.post("/auth/verify-otp", params={"phone": phone, "code": code}).json()["token"]

def test_create_event():
    token = get_auth_token()

    group_res = client.post("/groups/create", json={"name": "Event Group", "phones": []}, headers={"Authorization": f"Bearer {token}"})
    group_id = group_res.json()["id"]

    payload = {
        "title": "Burger Night",
        "group_id": group_id,
        "type": "Hangout",
        "date": "2024-12-01",
        "time": "20:00",
        "dynamic_fields": [{"link": "http://example.com"}]
    }
    response = client.post("/events/create", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["type"] == "Hangout"
    assert response.json()["title"] == "Burger Night"

def test_get_events():
    token = get_auth_token()
    response = client.get("/events", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert type(response.json()) == list
