import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_cron_attendance():
    response = client.get("/api/cron/check-attendance")
    assert response.status_code == 200
    assert response.json()["message"] == "Attendance checked."

def test_frontend_serving():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
