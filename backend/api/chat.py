# api/chat.py

from fastapi import APIRouter, WebSocket, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from typing import List

from models.schemas import ChatMessage, ConversationCreate, ConversationResponse
from db.crud import save_chat_message, save_conversation, get_user_conversations
from services.rag import generate_response_with_rag
from database.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.post("/send")
async def send_message(
    msg: ChatMessage,
    db: AsyncSession = Depends(get_db),
):
    try:
        # offload the sync save_chat_message(db, msg)
        await save_chat_message(db, msg)

        # # offload your existing RAG function
        # # reply =run_in_threadpool(generate_response_with_rag, msg.message)
        # # If you need to await the result, use:
        reply = await generate_response_with_rag(msg.message)
        print("🤖 Reply generated:", type(reply))
        return {"reply": reply}
    except Exception as e:
        print(" Chat error:", str(e))
        raise HTTPException(status_code=500, detail="Chat processing failed.")


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db),
):
    await websocket.accept()
    while True:
        msg_text = await websocket.receive_text()

        # Persist user message
        dummy_msg = ChatMessage(session_id="ws", message=msg_text)
        await run_in_threadpool(save_chat_message, db, dummy_msg)

        # Inform client we're working…
        await websocket.send_text("Typing…")

        # Get the response
        reply = await run_in_threadpool(generate_response_with_rag, msg_text)

        # Send it back
        await websocket.send_text(reply)


@router.post(
    "/conversations",
    response_model=ConversationResponse,
)
async def create_conversation(
    conversation: ConversationCreate, db: AsyncSession = Depends(get_db)
):
    return await save_conversation(db, conversation)


@router.get(
    "/conversations/{user_id}",
    response_model=List[ConversationResponse],
)
async def list_conversations(user_id: int, db: AsyncSession = Depends(get_db)):
    return await get_user_conversations(db, user_id)
