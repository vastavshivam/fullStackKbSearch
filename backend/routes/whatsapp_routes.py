from fastapi import APIRouter, Depends, HTTPException, Request , status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from utils import whatsapp_api
from models.db_models import ClientConfig
from database.database import get_db
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from typing import Optional, Literal



router = APIRouter()


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
def configure_whatsapp(config: WhatsAppConfig, db: Session = Depends(get_db)):
    existing = db.query(ClientConfig).filter(ClientConfig.client_id == config.client_id).first()
    if existing:
        existing.phone_id = config.phone_id
        existing.token = config.token
        existing.verify_token = config.verify_token
    else:
        new_config = ClientConfig(
            client_id=config.client_id,
            phone_id=config.phone_id,
            token=config.token,
            verify_token=config.verify_token
        )
        db.add(new_config)
    db.commit()
    return {"message": "WhatsApp config saved/updated successfully."}


@router.get("/webhook")
async def verify_webhook(request: Request, db: Session = Depends(get_db)):
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    # 🔐 Match token with DB
    config = db.query(ClientConfig).filter(ClientConfig.verify_token == token).first()
    if config:
        return whatsapp_api.verify_webhook(mode, token, challenge)
    raise HTTPException(status_code=403, detail="Invalid verify_token")


@router.post("/webhook")
async def webhook_listener(request: Request, db: Session = Depends(get_db)):
    configs = db.query(ClientConfig).all()
    config_dict = {c.client_id: {
        "token": c.token,
        "phone_id": c.phone_id
    } for c in configs}

    return await whatsapp_api.handle_incoming_message(request, config_dict, db)


@router.post("/send-message")
def send_message(payload: SendMessagePayload, db: Session = Depends(get_db)):
    config = db.query(ClientConfig).filter(ClientConfig.client_id == payload.client_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Client config not found")

    return whatsapp_api.send_whatsapp_message_dynamic(
        token=config.token,
        phone_id=config.phone_id,
        to=payload.to,
        message=payload.message
    )

#tested 
@router.post("/send-template")
async def send_template_message(
    payload: TemplateMessagePayload,
    db: AsyncSession = Depends(get_db)
):  
    try:
        token, phone_id = await get_token_and_phone_id(payload.client_id, db)

        return await whatsapp_api.send_template_message(
            token=token,
            phone_id=phone_id,
            to=payload.to,
            template_name=payload.template_name,
            language_code=payload.language_code,
            components=payload.components
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    

@router.post("/mark-as-read")
async def mark_as_read(payload: MarkReadPayload, db: AsyncSession = Depends(get_db)):
    config = await db.get(ClientConfig, payload.client_id)
    return await whatsapp_api.mark_message_as_read(config.token, payload.message_id)

# @router.get("/profile")
# async def get_business_profile(client_id: str, db: AsyncSession = Depends(get_db)):
#     ...
#     return await whatsapp_api.get_profile(token=ClientConfig.token)

# @router.post("/profile/update")
# async def update_profile(payload: UpdateProfilePayload, db: AsyncSession = Depends(get_db)):
#     ...
#     return await whatsapp_api.update_profile(token=ClientConfig.token, profile_data=payload.dict())

# @router.post("/send-media")
# async def send_media_message(payload: MediaMessagePayload, db: AsyncSession = Depends(get_db)):
#     ...
#     return await whatsapp_api.send_media_message(
#         token=config.token,
#         phone_id=config.phone_id,
#         to=payload.to,
#         media_id=payload.media_id,
#         media_type=payload.media_type,
#         caption=payload.caption
#     )
