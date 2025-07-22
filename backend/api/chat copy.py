from fastapi import APIRouter, WebSocket
from models.schemas import ChatMessage
from db.crud import save_chat_message
from services.rag import generate_response_with_rag

router = APIRouter()

@router.post("/send")
def send_message(msg: ChatMessage):
    save_chat_message(msg)
    reply = generate_response_with_rag(msg.message)
    return {"reply": reply}

# Optional: Live chat with WebSocket
@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    while True:
        msg = await ws.receive_text()
        await ws.send_text("Typing...")
        reply = generate_response_with_rag(msg)
        await ws.send_text(reply)