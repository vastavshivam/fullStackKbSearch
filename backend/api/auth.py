from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta, datetime
from database.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from db import crud
from models import schemas

from supabase import create_client, Client
from utils.auth_utils import (
    authenticate_user,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    register_user_helper
)

router = APIRouter()

# Initialize Supabase client
supabase_url = "https://ddfuhlysbhdfjrnaadlk.supabase.co"
supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRkZnVobHlzYmhkZmpybmFhZGxrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTMwODYyNjMsImV4cCI6MjA2ODY2MjI2M30.nTuVs5VNKd_MhYwrjslH1wr_XtOdCS0M3QnVEtcWp6g"
supabase: Client = create_client(supabase_url, supabase_key)

@router.post("/login", response_model=schemas.Token)
async def login(data: schemas.LoginRequest):
    """
    User login endpoint using Supabase
    """
    response = await supabase.auth.sign_in_with_password(
        email=data.email,
        password=data.password
    )

    if response.error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {"access_token": response.data.access_token, "token_type": "bearer"}

@router.post("/register", response_model=schemas.UserOut, status_code=201)
async def register_user(user: schemas.UserCreate):
    """
    User registration endpoint using Supabase
    """
    response = await supabase.auth.sign_up(
        email=user.email,
        password=user.password
    )

    if response.error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=response.error.message
        )

    # Save user credentials in Supabase database
    data = {
        "email": user.email,
        "password": user.password,
        "created_at": datetime.utcnow().isoformat()
    }
    db_response = supabase.table("users").insert(data).execute()

    if db_response.error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save user credentials."
        )

    return {"email": response.data.user.email, "id": response.data.user.id}