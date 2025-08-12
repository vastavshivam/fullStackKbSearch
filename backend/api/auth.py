from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta, datetime
from database.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from db import crud
from models import schemas

import hashlib
from mongo.models import MONGODB_AVAILABLE, SQLITE_AVAILABLE, mongo_db
from sqlite_fallback import save_user_sqlite
from utils.auth_utils import (
    authenticate_user,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    register_user_helper
)

router = APIRouter()

# Initialize Supabase client

@router.post("/login", response_model=schemas.Token)
async def login(data: schemas.LoginRequest):
    """
    Login endpoint using MongoDB (with SQLite fallback)
    """
    try:
        # For the demo user, allow both admin and user access
        if data.email == "krish.ishaan@gmail.com" and data.password == "root123":
            user_data = {
                "id": 1,
                "name": "Krish Ishaan",
                "email": data.email,
                "is_active": True,
                "role": data.role
            }
            return {
                "access_token": f"demo_token_{data.role}",
                "token_type": "bearer",
                "role": data.role,
                "user": user_data
            }

        # Use plain text password for SQLite fallback (no hashing)
        print(f"[DEBUG] Login attempt for: {data.email}, password: {data.password}")
        user = None
        print(f"[DEBUG] Forcing SQLite fallback for login (ignoring MongoDB)")
        import sqlite3, os
        DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'feedback.db'))
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Print all users for debug
        cursor.execute('SELECT id, name, email, role, is_active, hashed_password FROM users')
        all_users = cursor.fetchall()
        print(f"[DEBUG] All users in SQLite: {all_users}")
        # Print all roles for debug
        cursor.execute('SELECT role FROM users')
        all_roles = cursor.fetchall()
        print(f"[DEBUG] All roles in SQLite: {all_roles}")
        # Print received role
        print(f"[DEBUG] Received role: '{data.role}' (raw), Normalized: '{data.role.strip().lower()}'")
        # Now do the actual lookup (require normalized role match, plain password)
        normalized_role = data.role.strip().lower()
        cursor.execute('''SELECT id, name, email, role, is_active FROM users WHERE email = ? AND hashed_password = ? AND LOWER(TRIM(role)) = ?''', (data.email, data.password, normalized_role))
        row = cursor.fetchone()
        print(f"[DEBUG] SQLite user lookup result: {row}")
        conn.close()
        if row:
            user = {"id": row[0], "name": row[1], "email": row[2], "role": row[3], "is_active": row[4]}
        print(f"[DEBUG] Final user object: {user}")

        if user:
            # Generate a dummy token (replace with JWT if needed)
            return {
                "access_token": f"token_{user['id']}",
                "token_type": "bearer",
                "role": user["role"],
                "user": user
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except Exception as e:
        print(f"[DEBUG] Exception in login: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


import hashlib
from mongo.models import MONGODB_AVAILABLE, SQLITE_AVAILABLE, mongo_db
from sqlite_fallback import save_user_sqlite

@router.post("/register", response_model=schemas.UserOut, status_code=201)
async def register_user(user: schemas.UserCreate):
    """
    User registration endpoint using MongoDB (with SQLite fallback)
    """
    try:
        # Hash the password for storage
        print(f"[DEBUG] Registration for: {user.email}, password: {user.password}")
        hashed_password = hashlib.sha256(user.password.encode()).hexdigest()
        print(f"[DEBUG] Hashed password: {hashed_password}")
        user_data = {
            "name": user.name,
            "email": user.email,
            "hashed_password": hashed_password,
            "role": user.role,
            "is_active": True,
            "created_at": datetime.utcnow().isoformat()
        }
        print(f"[DEBUG] User data to save: {user_data}")
        if MONGODB_AVAILABLE:
            users_col = mongo_db["users"]
            # Check if user already exists
            if users_col.find_one({"email": user.email}):
                raise HTTPException(status_code=400, detail="User already exists")
            result = users_col.insert_one(user_data)
            user_id = str(result.inserted_id)
        elif SQLITE_AVAILABLE:
            user_id = save_user_sqlite(user_data)  # Implement this function in your SQLite fallback
        else:
            raise HTTPException(status_code=500, detail="No database available for registration")
        return {
            "id": user_id,
            "name": user.name,
            "email": user.email,
            "is_active": True,
            "role": user.role
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration failed: {str(e)}"
        )