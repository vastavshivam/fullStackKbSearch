from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from enum import Enum
from jose import jwt, JWTError, ExpiredSignatureError
from datetime import datetime, timedelta
import os

router = APIRouter()
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")
ALGORITHM = "HS256"

class RoleEnum(str, Enum):
    user = "user"
    admin = "admin"

class TokenRequest(BaseModel):
    user_id: str
    role: RoleEnum
    remember: bool = False

class RefreshRequest(BaseModel):
    refresh_token: str

@router.post("/auth/token")
def issue_token(payload: TokenRequest):
    access_exp = datetime.utcnow() + (timedelta(days=7) if payload.remember else timedelta(minutes=15))
    refresh_exp = datetime.utcnow() + timedelta(days=30)

    access_token = jwt.encode({
        "sub": payload.user_id,
        "role": payload.role,
        "exp": access_exp
    }, JWT_SECRET, algorithm=ALGORITHM)

    refresh_token = jwt.encode({
        "sub": payload.user_id,
        "role": payload.role,
        "exp": refresh_exp
    }, JWT_SECRET, algorithm=ALGORITHM)

    return {
        "token": access_token,
        "refresh_token": refresh_token
    }

@router.post("/auth/refresh")
def refresh_token(payload: RefreshRequest):
    try:
        decoded = jwt.decode(payload.refresh_token, JWT_SECRET, algorithms=[ALGORITHM])
        user_id = decoded["sub"]
        role = decoded.get("role", "user")

        new_token = jwt.encode({
            "sub": user_id,
            "role": role,
            "exp": datetime.utcnow() + timedelta(minutes=15)
        }, JWT_SECRET, algorithm=ALGORITHM)

        return {"token": new_token}

    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
