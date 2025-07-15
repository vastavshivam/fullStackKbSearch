from fastapi import WebSocket, WebSocketDisconnect
from jose.exceptions import ExpiredSignatureError
from utils.auth_utils import decode_jwt_token
import httpx

REFRESH_URL = "http://localhost:8000/auth/refresh"

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    token = websocket.headers.get("Authorization")
    refresh_token = websocket.headers.get("X-Refresh-Token")

    if token is None or not token.startswith("Bearer "):
        await websocket.close(code=1008, reason="Missing access token")
        return

    try:
        try:
            payload = decode_jwt_token(token[7:])
        except ExpiredSignatureError:
            if not refresh_token:
                await websocket.close(code=1008, reason="Token expired and no refresh token")
                return
            async with httpx.AsyncClient() as client:
                res = await client.post(REFRESH_URL, json={"refresh_token": refresh_token})
                if res.status_code != 200:
                    await websocket.close(code=1008, reason="Invalid refresh token")
                    return
                new_token = res.json()["token"]
                payload = decode_jwt_token(new_token)

        user_id = payload.get("sub", "anonymous")

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
