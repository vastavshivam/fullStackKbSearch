from fastapi import APIRouter, WebSocket, HTTPException
from models.schemas import ChatMessage
from db.crud import save_chat_message, get_conversation_context
from services.rag import generate_response_with_rag

# Optional: sentiment and embedding generators
from utils.nlp import analyze_sentiment, compute_embedding

router = APIRouter()

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
            print("❌ WebSocket error:", e)
            await websocket.send_text("Something went wrong.")
            break


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
    return get_conversation_context(session_id)
