# ==========================================
# 💡 Support Assistant Project .gitignore
# For FastAPI + PostgreSQL + React + Docker
# Author: Shivam Srivastav
# ==========================================
# File: backend/api/files.py    
# ==========================================

from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from db.crud import *
from database.database import get_db

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from passlib.context import CryptContext
from db import crud
from models import schemas

# Secret key & algorithm (ideally store in env)
SECRET_KEY = "your_secret_key_here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60   # Token expiration time in minutes

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

async def authenticate_user(db: AsyncSession, email: str, password: str, role: str):
    """
    Temporarily hardcoded authentication for development.
    """
    if email == "krish.ishaan@gmail.com" and password == "root":
        return schemas.UserOut(id=1, name="Krish Ishaan", email=email, is_active=True)

    # Original logic
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if user.role != role:
        return None
    return user


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta if expires_delta else datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def register_user_helper(db: AsyncSession, user: schemas.UserCreate) -> schemas.UserOut:
    """
    Helper function to register a new user. Hashes password and stores user in DB.
    """

    existing_user = await crud.get_user_by_email(db, email=user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )

    # 🚫 Restrict registering as admin unless a condition is met
    if user.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role cannot be self-assigned"
        )

    hashed_password = get_password_hash(user.password)
    user.password = hashed_password

    new_user = await crud.create_user(db, user)
    return new_user

