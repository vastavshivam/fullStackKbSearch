from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import HTTPException, status
from mongo.users import authenticate_user as mongo_authenticate_user, create_user as mongo_create_user
from models import schemas
from typing import Optional

# Secret key & algorithm (ideally store in env)
SECRET_KEY = "your_secret_key_here_change_in_production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60   # Token expiration time in minutes

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def authenticate_user(email: str, password: str, role: str):
    """Authenticate user using MongoDB"""
    user = mongo_authenticate_user(email, password, role)
    return user

async def register_user_helper(user: schemas.UserCreate) -> schemas.UserOut:
    """Helper function to register a new user using MongoDB"""
    try:
        # Check if trying to register as admin
        if user.role == "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin role cannot be self-assigned"
            )
        
        # Create user in MongoDB
        new_user = mongo_create_user(
            name=user.name,
            email=user.email,
            password=user.password,
            role=user.role
        )
        
        # Return user in expected format
        return schemas.UserOut(
            id=new_user['user_id'],
            name=new_user['name'],
            email=new_user['email'],
            is_active=new_user['is_active']
        )
        
    except ValueError as e:
        if "already exists" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )
