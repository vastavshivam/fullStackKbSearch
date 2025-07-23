import os
import pickle
import logging
import faiss
import pickle
import numpy as np

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from sentence_transformers import SentenceTransformer
from jose.exceptions import ExpiredSignatureError
import httpx

from utils.auth_utils import decode_jwt_token
from utils.nlp import analyze_sentiment, compute_embedding
from models.schemas import ChatMessage
from db.crud import save_chat_message, get_conversation_context
from services.rag import generate_response_with_rag

# ───── CONFIG ─────
router = APIRouter()
auth_scheme = HTTPBearer()
REFRESH_URL = "http://localhost:8000/auth/refresh"

# ───── LOGGING ─────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ───── Load Vector Model and FAISS Index ─────
vector_model = SentenceTransformer("all-MiniLM-L6-v2")

try:
    index = faiss.read_index("vector_stores/test.json.index")
    with open("vector_stores/test.json_chunks.pkl", "rb") as f:
        documents = pickle.load(f)
    logger.info("✅ FAISS index and documents loaded")
except Exception as e:
    logger.error(f"❌ Failed to load vector DB: {e}")
    index = None
    documents = []

# ───── Load Language Model ─────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.abspath(os.path.join(BASE_DIR, "../vector_stores/falcon-rw-1b"))
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForCausalLM.from_pretrained(MODEL_PATH)
chatbot = pipeline("text-generation", model=model, tokenizer=tokenizer)


# ───── API Models ─────
class ChatRequest(BaseModel):
    query: str


# ───── CHAT ENDPOINT ─────
@router.post("/chat")
async def chat(
    msg: ChatMessage,
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
    refresh_token: str = Query(None)
):
    try:
        # Token decoding and refresh logic
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

        # Vector index check
        if index is None or not documents:
            raise HTTPException(status_code=500, detail="Vector index not loaded")

        query = msg.message
        logger.info(f"🟢 Received query: {query}")

        # Step 1: Embed query
        query_vector = vector_model.encode([query])
        query_vector = np.array(query_vector).astype("float32").reshape(1, -1)

        # Step 2: Search vector DB
        distances, indices = index.search(query_vector, k=1)
        top_context = documents[indices[0][0]]
        logger.info(f"📄 Retrieved context: {top_context[:200]}...")

        # Step 3: Prompt and generate
        prompt = f"<s>Context: {top_context}\nCustomer: {query}\nAgent:"
        response = chatbot(prompt, max_length=200, do_sample=True)[0]["generated_text"]
        reply = response.split("Agent:")[-1].strip()

        # Step 4: Save to DB
        sentiment = analyze_sentiment(query)
        embedding = compute_embedding(query)

        save_chat_message(
            user_id=user_id,
            session_id=msg.session_id,
            message=query,
            sender="user",
            sentiment=sentiment,
            embedding=embedding,
            bot_reply=reply
        )

        return {"reply": reply}

    except Exception as e:
        logger.error(f"❌ Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail="Chat processing failed.")



# ───── WebSocket API ─────
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
        logger.info(f"🔌 WebSocket disconnected: {user_id}")
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
        await websocket.send_text("Something went wrong.")
        await websocket.close(code=1011)


# ───── Conversation History ─────
@router.get("/history/{session_id}")
def get_history(
    session_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
    refresh_token: str = Query(None)
):
    try:
        try:
            payload = decode_jwt_token(credentials.credentials)
        except ExpiredSignatureError:
            if not refresh_token:
                raise HTTPException(status_code=401, detail="Token expired. Provide refresh_token.")
            with httpx.Client() as client:
                res = client.post(REFRESH_URL, json={"refresh_token": refresh_token})
                if res.status_code != 200:
                    raise HTTPException(status_code=401, detail="Refresh token invalid")
                new_token = res.json()["token"]
                payload = decode_jwt_token(new_token)

        # Optionally use user_id = payload.get("sub") to validate ownership
        return get_conversation_context(session_id)

    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Unauthorized: {str(e)}")

