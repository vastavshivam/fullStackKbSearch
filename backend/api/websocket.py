from fastapi import APIRouter, WebSocket, WebSocketDisconnect, FastAPI
from models.mistral_model import get_mistral_response


router = APIRouter()

clients = []


@router.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            response = get_mistral_response(data)
            await websocket.send_text(response)
    except WebSocketDisconnect:
        clients.remove(websocket)
