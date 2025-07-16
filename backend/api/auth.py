from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from database.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from db import crud
from models import schemas

from utils.auth_utils import (
    authenticate_user,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    register_user_helper
)

router = APIRouter()

@router.post("/login", response_model=schemas.Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(),db: AsyncSession = Depends(get_db),):
    """
    User login endpoint using OAuth2PasswordRequestForm
    """
    user = await authenticate_user(db, form_data.username, form_data.password)
    print(f"User authenticated:================> {user}")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Assume user.scopes is a list of scopes, e.g. ["admin", "user"]
    scopes = getattr(user, "scopes", ["user"])  # fallback to 'user' if not present
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.email, "scopes": scopes}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer", "scopes": scopes}


@router.post("/register", response_model=schemas.UserOut, status_code=201)
async def register_user(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    return await register_user_helper(db, user) 