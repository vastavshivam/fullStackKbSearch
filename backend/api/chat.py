from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models.schemas import ChatMessage
from db.crud import save_chat_message, get_conversation_context
from services.rag import generate_response_with_rag
from utils.auth_utils import decode_jwt_token
from utils.nlp import analyze_sentiment, compute_embedding

router = APIRouter()
auth_scheme = HTTPBearer()


# ✅ REST: POST /send (JWT Protected)
@router.post("/send")
async def send_message(
    msg: ChatMessage,
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)
):
    try:
        payload = decode_jwt_token(credentials.credentials)
        user_id = payload.get("sub", "anonymous")

        sentiment = analyze_sentiment(msg.message)
        embedding = compute_embedding(msg.message)
        reply = await generate_response_with_rag(msg.message)

        save_chat_message(
            user_id=user_id,
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


# ✅ WebSocket: /ws (JWT Protected via header)
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    # 🔐 Extract and verify JWT from Authorization header
    token = websocket.headers.get("Authorization")
    if token is None or not token.startswith("Bearer "):
        await websocket.close(code=1008, reason="Unauthorized: No token")
        return

    try:
        payload = decode_jwt_token(token[7:])
        user_id = payload.get("sub", "anonymous")
    except Exception as e:
        await websocket.close(code=1008, reason="Unauthorized: Invalid token")
        return

    try:
        while True:
            msg_text = await websocket.receive_text()

            sentiment = analyze_sentiment(msg_text)
            embedding = compute_embedding(msg_text)
            reply = await generate_response_with_rag(msg_text)

            save_chat_message(
                user_id=user_id,
                session_id="ws",
                message=msg_text,
                sender="user",
                sentiment=sentiment,
                embedding=embedding,
                bot_reply=reply
            )

            await websocket.send_text(reply)

    except WebSocketDisconnect:
        print(f"🔌 WebSocket disconnected: {user_id}")
    except Exception as e:
        print("❌ WebSocket error:", e)
        await websocket.send_text("Something went wrong.")
        await websocket.close(code=1011)


# ✅ GET: /history/{session_id} (JWT Protected)
@router.get("/history/{session_id}")
def get_history(
    session_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)
):
    payload = decode_jwt_token(credentials.credentials)
    return get_conversation_context(session_id)
