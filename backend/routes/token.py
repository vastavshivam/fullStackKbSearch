from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import jwt, os, time
from enum import Enum  

router = APIRouter()
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")

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
    exp = time.time() + (7 * 24 * 60 * 60 if payload.remember else 15 * 60)
    refresh_exp = time.time() + (30 * 24 * 60 * 60)
    token = jwt.encode({"user_id": payload.user_id, "role": payload.role, "exp": exp}, JWT_SECRET, algorithm="HS256")
    refresh_token = jwt.encode({"user_id": payload.user_id, "exp": refresh_exp}, JWT_SECRET, algorithm="HS256")
    return {"token": token, "refresh_token": refresh_token}

@router.post("/auth/refresh")
def refresh_token(payload: RefreshRequest):
    try:
        decoded = jwt.decode(payload.refresh_token, JWT_SECRET, algorithms=["HS256"])
        # Add 'role' here if you want it to persist across refresh
        # Either store it in refresh_token or fetch it from DB
        user_id = decoded["user_id"]

        # Option 1: Store role in refresh_token and decode here:
        role = decoded.get("role", "user")  # fallback if missing

        # Option 2: Fetch from DB (recommended for security)
        # user = get_user_from_db(user_id)  # <- you'd implement this
        # role = user.role

        token = jwt.encode({"user_id": user_id, "role": role, "exp": time.time() + 15 * 60}, JWT_SECRET, algorithm="HS256")
        return {"token": token}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
