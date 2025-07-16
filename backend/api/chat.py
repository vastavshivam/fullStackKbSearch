from fastapi import APIRouter, WebSocket, HTTPException
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


@router.get("/history/{session_id}")
def get_history(session_id: str):
    return get_conversation_context(session_id)

# Load fine-tuned Mistral model
MODEL_PATH = os.path.abspath("training/training/checkpoints/fine-tuned-output")
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

