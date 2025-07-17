from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models.schemas import ChatMessage
from db.crud import save_chat_message, get_conversation_context
from services.rag import generate_response_with_rag
import os
import logging

from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from sentence_transformers import SentenceTransformer
import faiss, pickle
import logging

# Optional: sentiment and embedding generators
from utils.nlp import analyze_sentiment, compute_embedding
from jose.exceptions import ExpiredSignatureError
import httpx

router = APIRouter()
auth_scheme = HTTPBearer()

REFRESH_URL = "http://localhost:8000/auth/refresh"  # adjust as needed


# ✅ REST: POST /send (JWT with refresh token fallback)
@router.post("/send")
async def send_message(
    msg: ChatMessage,
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
    refresh_token: str = Query(None)
):
    try:
        try:
            payload = decode_jwt_token(credentials.credentials)
        except ExpiredSignatureError:
            if not refresh_token:
                raise HTTPException(status_code=401, detail="Token expired. Provide refresh_token.")

            async with httpx.AsyncClient() as client:
                res = await client.post(REFRESH_URL, json={"refresh_token": refresh_token})
                if res.status_code != 200:
                    raise HTTPException(status_code=401, detail="Refresh token invalid")
                new_token = res.json()["token"]
                payload = decode_jwt_token(new_token)

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


# ✅ WebSocket: /ws (JWT with refresh fallback in headers)
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    token = websocket.headers.get("Authorization")
    refresh_token = websocket.headers.get("X-Refresh-Token")

    if token is None or not token.startswith("Bearer "):
        await websocket.close(code=1008, reason="Missing or invalid Authorization header")
        return

    try:
        try:
            payload = decode_jwt_token(token[7:])
        except ExpiredSignatureError:
            if not refresh_token:
                await websocket.close(code=1008, reason="Token expired. No refresh token provided.")
                return
            async with httpx.AsyncClient() as client:
                res = await client.post(REFRESH_URL, json={"refresh_token": refresh_token})
                if res.status_code != 200:
                    await websocket.close(code=1008, reason="Refresh token invalid")
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


# ✅ GET: /history/{session_id} (JWT protected)
@router.get("/history/{session_id}")
def get_history(session_id: str):
    return get_conversation_context(session_id)

# Load fine-tuned Mistral model
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.abspath(os.path.join(BASE_DIR, "../vector_stores/falcon-rw-1b")) 
# MODEL_PATH = os.path.abspath("training/training/checkpoints/fine-tuned-output")
print(f"model path in chat.py file =======>{MODEL_PATH}")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForCausalLM.from_pretrained(MODEL_PATH)
chatbot = pipeline("text-generation", model=model, tokenizer=tokenizer)

# Load vector DB
# vector_model = SentenceTransformer("all-MiniLM-L6-v2")
# index = faiss.read_index("kb.index")  # built from your KB
# with open("kb_docs.pkl", "rb") as f:
#     documents = pickle.load(f)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatRequest(BaseModel):
    query: str

@router.post("/chat/")
def chat(request: ChatRequest):
    query = request.query
    logger.info(f"🟢 Received query: {query}")

    # [1] Embed query
    query_vector = vector_model.encode([query])

    # [2] Search vector DB (top-1 result)
    distances, indices = index.search(query_vector, k=1)
    top_context = documents[indices[0][0]]
    logger.info(f"📄 Retrieved context: {top_context}")

    # [3] Build prompt for Mistral
    prompt = f"<s>Context: {top_context}\nCustomer: {query}\nAgent:"

    # [4] Generate using fine-tuned model
    response = chatbot(prompt, max_length=200, do_sample=True)[0]["generated_text"]
    reply = response.split("Agent:")[-1].strip()

    # [5] Return response
    return {"response": reply}

