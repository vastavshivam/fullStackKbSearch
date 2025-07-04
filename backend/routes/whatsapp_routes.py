from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from backend.utils import whatsapp_api  # adjust import if needed

router = APIRouter()
CLIENT_CONFIG = {}  # Ideally move this to a service layer or database

class WhatsAppConfig(BaseModel):
    client_id: str
    phone_id: str
    token: str
    verify_token: str

class SendMessagePayload(BaseModel):
    client_id: str
    to: str
    message: str

@router.post("/configure-whatsapp")
def configure_whatsapp(config: WhatsAppConfig):
    CLIENT_CONFIG[config.client_id] = {
        "phone_id": config.phone_id,
        "token": config.token,
        "verify_token": config.verify_token
    }
    return {"message": "WhatsApp config saved successfully."}

@router.get("/webhook")
async def verify_webhook(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    return whatsapp_api.verify_webhook(mode, token, challenge)

@router.post("/webhook")
async def webhook_listener(request: Request):
    return await whatsapp_api.handle_incoming_message(request, CLIENT_CONFIG)

@router.post("/send-message")
def send_message(payload: SendMessagePayload):
    client = CLIENT_CONFIG.get(payload.client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client config not found")
    return whatsapp_api.send_whatsapp_message_dynamic(
        token=client["token"],
        phone_id=client["phone_id"],
        to=payload.to,
        message=payload.message
    )
