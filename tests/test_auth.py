import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
from fastapi.testclient import TestClient
from main import app
from database import get_db
import models

client = TestClient(app)

def test_request_otp():
    response = client.post("/auth/request-otp", params={"phone": "+20101111111"})
    assert response.status_code == 200
    assert response.json() == {"message": "OTP sent via WhatsApp"}

    # Check DB
    db = next(get_db())
    otp = db.query(models.OTPCode).filter(models.OTPCode.phone == "+20101111111").first()
    assert otp is not None
    assert otp.code is not None

def test_verify_otp():
    db = next(get_db())
    otp = db.query(models.OTPCode).filter(models.OTPCode.phone == "+20101111111").first()
    code = otp.code

    response = client.post("/auth/verify-otp", params={"phone": "+20101111111", "code": code})
    assert response.status_code == 200
    assert "token" in response.json()
    assert "user_id" in response.json()
