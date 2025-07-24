from pymongo import MongoClient
from uuid import uuid4
from datetime import datetime
import bcrypt
from typing import Optional, Dict, Any, List

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['chat_db']
users = db['users']

# Create indexes for better performance
users.create_index("email", unique=True)
users.create_index("user_id", unique=True)

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_user(name: str, email: str, password: str, role: str = "user") -> Dict[str, Any]:
    """Create a new user in MongoDB"""
    # Check if user already exists
    existing_user = users.find_one({"email": email})
    if existing_user:
        raise ValueError("User with this email already exists")
    
    # Generate user ID
    user_id = str(uuid4())
    
    # Hash password
    hashed_password = hash_password(password)
    
    # Create user document
    user_doc = {
        "user_id": user_id,
        "name": name,
        "email": email,
        "hashed_password": hashed_password,
        "role": role,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    # Insert user
    result = users.insert_one(user_doc)
    
    # Return user without password
    user_doc.pop('hashed_password')
    user_doc['id'] = user_id
    return user_doc

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user by email"""
    user = users.find_one({"email": email})
    if user:
        user['id'] = user['user_id']
        return user
    return None

def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user by ID"""
    user = users.find_one({"user_id": user_id})
    if user:
        user['id'] = user['user_id']
        return user
    return None

def authenticate_user(email: str, password: str, role: str) -> Optional[Dict[str, Any]]:
    """Authenticate user with email, password, and role"""
    user = get_user_by_email(email)
    if not user:
        return None
    
    # Verify password
    if not verify_password(password, user['hashed_password']):
        return None
    
    # Check role
    if user['role'] != role:
        return None
    
    # Check if user is active
    if not user.get('is_active', True):
        return None
    
    # Return user without password
    user_copy = user.copy()
    user_copy.pop('hashed_password', None)
    return user_copy

def update_user(user_id: str, update_data: Dict[str, Any]) -> bool:
    """Update user data"""
    update_data['updated_at'] = datetime.utcnow()
    
    # Remove fields that shouldn't be updated directly
    forbidden_fields = ['user_id', 'hashed_password', 'created_at']
    for field in forbidden_fields:
        update_data.pop(field, None)
    
    result = users.update_one(
        {"user_id": user_id},
        {"$set": update_data}
    )
    return result.modified_count > 0

def delete_user(user_id: str) -> bool:
    """Soft delete user by setting is_active to False"""
    result = users.update_one(
        {"user_id": user_id},
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )
    return result.modified_count > 0

def change_password(user_id: str, new_password: str) -> bool:
    """Change user password"""
    hashed_password = hash_password(new_password)
    result = users.update_one(
        {"user_id": user_id},
        {"$set": {"hashed_password": hashed_password, "updated_at": datetime.utcnow()}}
    )
    return result.modified_count > 0

def get_all_users(skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
    """Get all users with pagination"""
    cursor = users.find(
        {"is_active": True},
        {"hashed_password": 0}  # Exclude password from results
    ).skip(skip).limit(limit)
    
    user_list = []
    for user in cursor:
        user['id'] = user['user_id']
        user_list.append(user)
    
    return user_list

def count_users() -> int:
    """Count total active users"""
    return users.count_documents({"is_active": True})
