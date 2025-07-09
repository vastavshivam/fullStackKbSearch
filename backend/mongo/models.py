from pymongo import MongoClient
from datetime import datetime
import os
import redis
import json

# LangChain imports
from langchain.memory import RedisChatMessageHistory, ConversationBufferMemory

# MongoDB setup
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
mongo_client = MongoClient(MONGO_URI)

mongo_db = mongo_client["chat_support"]

# Collections
chat_logs_col = mongo_db["chat_logs"]
ticket_logs_col = mongo_db["ticket_logs"]
feedback_logs_col = mongo_db["feedback_logs"]

# Redis setup (plain Redis)
redis_client = redis.Redis(host="localhost", port=6379, db=0)


def save_chat_log_mongo(user_id, message, sender, session_id, sentiment=None, embedding=None, bot_reply=None):
    """
    Save a chat message with optional sentiment, embedding, and bot reply.
    """
    record = {
        "user_id": user_id,
        "session_id": session_id,
        "sender": sender,  # 'user' or 'bot'
        "message": message,
        "timestamp": datetime.utcnow(),
    }

    if sentiment:
        record["sentiment"] = sentiment

    if embedding:
        record["embedding"] = embedding

    if bot_reply:
        record["bot_reply"] = bot_reply

    result = chat_logs_col.insert_one(record)
    return result.inserted_id


def save_ticket_log_mongo(ticket_data):
    """
    Save a support ticket.
    """
    ticket_logs_col.insert_one({
        **ticket_data,
        "created_at": datetime.utcnow()
    })


def save_feedback_mongo(message_id, feedback):
    """
    Save thumbs up/down feedback.
    """
    feedback_logs_col.insert_one({
        "message_id": message_id,
        "feedback": feedback,  # 'up' or 'down'
        "timestamp": datetime.utcnow()
    })


def get_session_context(session_id):
    """
    Load recent session context from Redis (manual).
    Returns a list of strings.
    """
    redis_key = f"session:{session_id}"
    if redis_client.exists(redis_key):
        return json.loads(redis_client.get(redis_key))
    return []


def save_session_context(session_id, context_list):
    """
    Save updated context back to Redis (manual).
    """
    redis_key = f"session:{session_id}"
    redis_client.set(redis_key, json.dumps(context_list))


def get_langchain_memory(session_id):
    """
    Returns a LangChain ConversationBufferMemory object backed by Redis.
    This automatically handles message appending, retrieval, and formatting.
    """
    # Create Redis-backed chat history
    chat_history = RedisChatMessageHistory(
        url="redis://localhost:6379",
        session_id=session_id
    )
    
    # Wrap in LangChain memory
    memory = ConversationBufferMemory(
        chat_memory=chat_history,
        return_messages=False
    )
    return memory
