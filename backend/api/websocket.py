from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from models.mistral_model import get_mistral_response
from utils.auth_utils import decode_jwt_token

router = APIRouter()

clients = []

@router.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    # 🔐 Extract Bearer token from headers
    token_header = websocket.headers.get("Authorization")
    if token_header is None or not token_header.startswith("Bearer "):
        await websocket.close(code=1008, reason="Unauthorized: No token")
        return

    token = token_header[7:]  # Remove "Bearer "
    try:
        payload = decode_jwt_token(token)
        user_id = payload.get("sub", "anonymous")
    except Exception as e:
        await websocket.close(code=1008, reason="Unauthorized: Invalid token")
        return

    clients.append(websocket)
    try:
        while True:
            msg = await websocket.receive_text()
            response = get_mistral_response(msg)
            await websocket.send_text(response)
    except WebSocketDisconnect:
        clients.remove(websocket)