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
    Enhanced login endpoint with role-based authentication
    """
    try:
        # For the demo user, allow both admin and user access
        if data.email == "krish.ishaan@gmail.com" and data.password == "root123":
            # Generate a simple token (for demo purposes)
            user_data = {
                "id": 1,
                "name": "Krish Ishaan",
                "email": data.email,
                "is_active": True,
                "role": data.role  # Use the requested role
            }
            
            return {
                "access_token": f"demo_token_{data.role}", 
                "token_type": "bearer", 
                "role": data.role,
                "user": user_data
            }
        
        # Original Supabase authentication for other users
        response = supabase.auth.sign_in_with_password(
            {"email": data.email, "password": data.password}
        )
        
        if response.user and response.session:
            return {"access_token": response.session.access_token, "token_type": "bearer"}
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/register", response_model=schemas.UserOut, status_code=201)
async def register_user(user: schemas.UserCreate):
    """
    User registration endpoint using Supabase
    """
    try:
        response = supabase.auth.sign_up(
            {"email": user.email, "password": user.password}
        )

        if response.user:
            # Save user credentials in Supabase database
            data = {
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "created_at": datetime.utcnow().isoformat()
            }
            db_response = supabase.table("users").insert(data).execute()

            return {
                "id": response.user.id, 
                "name": user.name,
                "email": response.user.email, 
                "is_active": True
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration failed: {str(e)}"
        )