# ==========================================
# 💡 Support Assistant Project .gitignore
# For FastAPI + PostgreSQL + React + Docker
# team: AppgBird
# Author: Shivam Srivastav
# ==========================================
# File: backend/utils/whatsapp_api.py
# This module handles WhatsApp Cloud API integration for sending and receiving messages. 
# ==========================================
import requests
import json
import os
from fastapi import Request, HTTPException

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")
WHATSAPP_API_URL = f"https://graph.facebook.com/v17.0/{WHATSAPP_PHONE_ID}/messages"

# ✅ Verify Webhook Token (GET)
def verify_webhook(mode: str, token: str, challenge: str):
    VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "my_secret_token")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return int(challenge)
    raise HTTPException(status_code=403, detail="Webhook verification failed")

# 📩 Handle Incoming Webhook Messages (POST)
def handle_incoming_message(req: Request):
    payload = req.json()
    entry = payload.get("entry", [])[0]
    changes = entry.get("changes", [])[0]
    value = changes.get("value", {})
    messages = value.get("messages", [])

    if messages:
        message = messages[0]
        from_id = message["from"]
        text = message.get("text", {}).get("body")

        # Log or store the message
        print(f"Incoming WhatsApp message from {from_id}: {text}")
        # Optional: save to DB and respond using AI or fallback

    return {"status": "received"}

# 📤 Send WhatsApp Message via Cloud API
def send_whatsapp_message(to: str, message: str):
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }
    response = requests.post(WHATSAPP_API_URL, headers=headers, data=json.dumps(payload))
    if response.status_code != 200:
        print("WhatsApp API Error:", response.text)
    return response.json()