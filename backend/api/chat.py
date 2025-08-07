from fastapi import APIRouter, WebSocket, HTTPException, UploadFile, File
from pydantic import BaseModel
from models.schemas import ChatMessage
from db.crud import save_chat_message, get_conversation_context
from services.rag import generate_response_with_rag
import logging
import base64
import io
from PIL import Image
import google.generativeai as genai
import os
from typing import Optional

# Optional: sentiment and embedding generators
from utils.nlp import analyze_sentiment, compute_embedding

logger = logging.getLogger(__name__)
router = APIRouter()

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    vision_model = genai.GenerativeModel('gemini-1.5-pro-vision-latest')
else:
    logger.warning("GEMINI_API_KEY not found. Advanced AI features will be disabled.")

# Widget chat message model
class WidgetChatMessage(BaseModel):
    message: str
    client_id: str
    session_id: str
    user_id: str = "anonymous"
    image_data: Optional[str] = None  # Base64 encoded image
    has_voice: bool = False

# Advanced widget chat message model
class AdvancedWidgetMessage(BaseModel):
    message: str
    client_id: str
    session_id: str
    user_id: str = "anonymous"
    message_type: str = "text"  # text, image, voice, mixed
    image_data: Optional[str] = None
    voice_data: Optional[str] = None

@router.post("/send")
async def send_message(msg: ChatMessage):
    try:
        # ✨ Compute sentiment & embedding
        sentiment = analyze_sentiment(msg.message)
        embedding = compute_embedding(msg.message)

        # ✨ Generate bot reply
        reply = await generate_response_with_rag(msg.message)

        # ✅ Save user message + bot reply in one MongoDB document
        save_chat_message(
            user_id=msg.user_id,
            session_id=msg.session_id,
            message=msg.message,
            sender="user",
            sentiment=sentiment,
            embedding=embedding,
            bot_reply=reply
        )

        return {"reply": reply}
    except Exception as e:
        print("❌ Chat error:", str(e))
        raise HTTPException(status_code=500, detail="Chat processing failed.")


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    while True:
        try:
            msg_text = await websocket.receive_text()

            # ✨ Compute sentiment & embedding
            sentiment = analyze_sentiment(msg_text)
            embedding = compute_embedding(msg_text)

            # ✨ Generate bot reply
            reply = await generate_response_with_rag(msg_text)

            # ✅ Save user message + bot reply in one document
            save_chat_message(
                user_id="anonymous",
                session_id="ws",
                message=msg_text,
                sender="user",
                sentiment=sentiment,
                embedding=embedding,
                bot_reply=reply
            )

            await websocket.send_text(reply)

        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            await websocket.send_text(f"❌ Error: {str(e)}")
            break

# Widget-specific chat endpoint
@router.post("/widget")
async def widget_chat(msg: WidgetChatMessage):
    """Handle chat messages from embedded widgets"""
    try:
        # ✨ Compute sentiment & embedding
        sentiment = analyze_sentiment(msg.message)
        embedding = compute_embedding(msg.message)

        # ✨ Generate bot reply using RAG
        reply = await generate_response_with_rag(msg.message)

        # ✅ Save widget chat message
        save_chat_message(
            user_id=msg.user_id,
            session_id=msg.session_id,
            message=msg.message,
            sender="user",
            sentiment=sentiment,
            embedding=embedding,
            bot_reply=reply,
            metadata={"client_id": msg.client_id, "source": "widget"}
        )

        return {"response": reply, "status": "success"}
    except Exception as e:
        logger.error(f"Widget chat error: {e}")
        raise HTTPException(status_code=500, detail="Chat processing failed.")


@router.post("/session")
async def create_chat_session(request: dict):
    """Create a new chat session"""
    user_id = request.get("user_id", "anonymous")
    # Generate a unique session ID
    import uuid
    session_id = str(uuid.uuid4())
    
    return {"session_id": session_id, "user_id": user_id, "status": "created"}

@router.post("/message")
async def store_chat_message(request: dict):
    """Store a chat message"""
    session_id = request.get("session_id")
    sender = request.get("sender")
    message = request.get("message")
    
    # Here you would typically save to database
    # For now, just return success
    return {"status": "stored", "session_id": session_id, "sender": sender}

@router.get("/history/{session_id}")
def get_history(session_id: str):
    try:
        return get_conversation_context(session_id)
    except Exception as e:
        logger.error(f"Failed to get chat history: {e}")
        # Return empty conversation instead of failing
        return []
