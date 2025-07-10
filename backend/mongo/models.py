from pymongo import MongoClient
from datetime import datetime
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client["chat_support"]
chat_logs_col = mongo_db["chat_logs"]
ticket_logs_col = mongo_db["ticket_logs"]


def save_chat_log_mongo(user_id, message, sender, session_id):
    chat_logs_col.insert_one({
        "user_id": user_id,
        "session_id": session_id,
        "sender": sender,
        "message": message,
        "timestamp": datetime.utcnow()
    })


def save_ticket_log_mongo(ticket_data):
    ticket_logs_col.insert_one({
        **ticket_data,
        "created_at": datetime.utcnow()
    })
