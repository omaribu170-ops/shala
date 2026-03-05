import os
import random
import jwt
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db
import models

JWT_SECRET = os.environ.get("JWT_SECRET", "fallback-dev-secret-do-not-use-in-prod")
JWT_ALGORITHM = "HS256"

security = HTTPBearer()

def generate_otp(phone: str, db: Session) -> str:
    code = str(random.randint(1000, 9999))
    expires_at = int((datetime.utcnow() + timedelta(minutes=5)).timestamp())

    otp_record = db.query(models.OTPCode).filter(models.OTPCode.phone == phone).first()
    if otp_record:
        otp_record.code = code
        otp_record.expires_at = expires_at
    else:
        otp_record = models.OTPCode(phone=phone, code=code, expires_at=expires_at)
        db.add(otp_record)

    db.commit()
    return code

def verify_otp_code(phone: str, code: str, db: Session) -> bool:
    otp_record = db.query(models.OTPCode).filter(models.OTPCode.phone == phone).first()
    if not otp_record:
        return False

    now = int(datetime.utcnow().timestamp())
    if otp_record.code == code and otp_record.expires_at >= now:
        db.delete(otp_record)
        db.commit()
        return True

    return False

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=365)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user
