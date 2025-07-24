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
import httpx
import os
from fastapi import Request, HTTPException
from models.db_models import ChatHistory
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import dotenv

dotenv.load_dotenv()

CURRENT_API_VERSION = os.getenv("CURRENT_API_VERSION", "v23.0")  # Default to v23.0 if not set

BASE_URL = f"https://graph.facebook.com/{CURRENT_API_VERSION}"

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")

WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")
  # Replace with your actual phone ID
 # Update as needed
WHATSAPP_API_URL = f"https://graph.facebook.com/{CURRENT_API_VERSION}/{WHATSAPP_PHONE_ID}"

# ✅ Verify Webhook Token (GET)
def verify_webhook(mode: str, token: str, challenge: str):
    VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
    
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return int(challenge)
    raise HTTPException(status_code=403, detail="Webhook verification failed")

# 📩 Handle Incoming Webhook Messages (POST)
# def handle_incoming_message(req: Request):
#     payload = req.json()
#     entry = payload.get("entry", [])[0]
#     changes = entry.get("changes", [])[0]
#     value = changes.get("value", {})
#     messages = value.get("messages", [])

#     if messages:
#         message = messages[0]
#         from_id = message["from"]
#         text = message.get("text", {}).get("body")

#         # Log or store the message
#         print(f"Incoming WhatsApp message from {from_id}: {text}")
#         # Optional: save to DB and respond using AI or fallback

#     return {"status": "received"}

async def handle_incoming_message(req: Request, client_config: dict, db=None):
    payload = await req.json()
    entry = payload.get("entry", [])[0]
    changes = entry.get("changes", [])[0]
    value = changes.get("value", {})
    messages = value.get("messages", [])
    metadata = value.get("metadata", {})
    phone_id = metadata.get("phone_number_id")

    if messages:
        message = messages[0]
        from_id = message["from"]
        text = message.get("text", {}).get("body")
        client_id = None

        # Match the config for the right phone_id
        for cid, config in client_config.items():
            if config["phone_id"] == phone_id:
                client_id = cid
                break

        print(f" Message from {from_id}: {text}")

        # Save incoming message to DB
        if db and client_id:
            db.add(ChatHistory(
                client_id=client_id,
                sender="user",
                user_number=from_id,
                message=text,
                direction="incoming"
            ))
            db.commit()

        # Reply logic
        reply = f"🤖 Bot: You said '{text}'"

        # Send reply
        if client_id:
            config = client_config[client_id]
            whatsapp_response = send_whatsapp_message_dynamic(
                token=config["token"],
                phone_id=config["phone_id"],
                to=from_id,
                message=reply
            )

            # Save bot response
            if db:
                db.add(ChatHistory(
                    client_id=client_id,
                    sender="bot",
                    user_number=from_id,
                    message=reply,
                    direction="outgoing"
                ))
                db.commit()

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

def send_whatsapp_message_dynamic(token: str, phone_id: str, to: str, message: str):
    # url = f"https://graph.facebook.com/v18.0/{phone_id}/messages"
    url = f"{BASE_URL}/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    if response.status_code != 200:
        print("WhatsApp API Error:", response.text)
    return response.json()


async def send_whatsapp_message_dynamic(token, phone_id, to, message):
    url = f"{BASE_URL}/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        return response.json()

async def mark_message_as_read(token, message_id):
    url = f"{BASE_URL}/messages"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"messaging_product": "whatsapp", "status": "read", "message_id": message_id}
    async with httpx.AsyncClient() as client:
        return (await client.post(url, json=payload, headers=headers)).json()
    




async def send_template_message(token, phone_id, to, template_name, language_code, components=None):
    url = f"{BASE_URL}/{phone_id}/messages"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": language_code}
        }
    }
    async with httpx.AsyncClient() as client:
        return (await client.post(url, json=payload, headers=headers)).json()
    
async def get_message_status(token, message_id):
    url = f"{BASE_URL}/{message_id}"
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        return (await client.get(url, headers=headers)).json()

async def get_business_profile(token, phone_id):
    url = f"{BASE_URL}/{phone_id}/whatsapp_business_profile"
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        return (await client.get(url, headers=headers)).json()

async def subscribe_webhook(app_id, token, webhook_url, verify_token):
    url = f"https://graph.facebook.com/v19.0/{app_id}/subscriptions"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "object": "whatsapp_business_account",
        "callback_url": webhook_url,
        "verify_token": verify_token,
        "fields": "messages"
    }
    async with httpx.AsyncClient() as client:
        return (await client.post(url, data=payload, headers=headers)).json()
