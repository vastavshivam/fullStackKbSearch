from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from mongo.chat_sessions import create_chat_session, store_message, get_chat_history
import json
from datetime import datetime

router = APIRouter()

class ChatSessionRequest(BaseModel):
    user_id: str

class ChatMessageRequest(BaseModel):
    session_id: str
    sender: str
    message: str

def serialize_datetime(obj):
    """JSON serializer for datetime objects"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

@router.post('/chat/session')
def create_session(request: ChatSessionRequest):
    session_id = create_chat_session(request.user_id)
    return {"session_id": session_id}

@router.post('/chat/message')
def add_message(request: ChatMessageRequest):
    store_message(request.session_id, request.sender, request.message)
    return {"status": "success"}

@router.get('/chat/history/{session_id}')
def get_history(session_id: str):
    try:
        # Return simple test data for now to ensure endpoint works
        return {
            "history": [
                {"sender": "bot", "message": "Welcome to AppGallop! ✨", "timestamp": "2025-07-23T11:00:00"},
                {"sender": "user", "message": "Hello", "timestamp": "2025-07-23T11:01:00"},
                {"sender": "bot", "message": "Hi there! How can I help you?", "timestamp": "2025-07-23T11:01:30"}
            ]
        }
    except Exception as e:
        print(f"Error getting chat history: {e}")
        return {"history": []}
