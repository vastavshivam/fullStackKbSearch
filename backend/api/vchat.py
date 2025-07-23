from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from sentence_transformers import SentenceTransformer
import faiss, pickle, os, logging, torch
from jose.exceptions import ExpiredSignatureError
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.database import get_db
from models.db_models import User
from utils.auth_utils import decode_jwt_token

router = APIRouter()
auth_scheme = HTTPBearer()

MODEL_PATH = os.path.abspath("checkpoints/fine-tuned-output")
VECTOR_MODEL_NAME = "all-MiniLM-L6-v2"
VECTOR_DIR = "vector_stores"
REFRESH_URL = "http://localhost:8000/auth/refresh"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForCausalLM.from_pretrained(MODEL_PATH)
chatbot = pipeline("text-generation", model=model, tokenizer=tokenizer)
embedder = SentenceTransformer(VECTOR_MODEL_NAME)

class ChatRequest(BaseModel):
    query: str

def generate_clean_response(prompt, model, tokenizer):
    input_ids = tokenizer(prompt, return_tensors="pt").input_ids
    if torch.cuda.is_available():
        input_ids = input_ids.cuda()
        model = model.cuda()
    output_ids = model.generate(
        input_ids=input_ids,
        max_new_tokens=100,
        do_sample=False,
        eos_token_id=tokenizer.eos_token_id,
        pad_token_id=tokenizer.eos_token_id,
        repetition_penalty=1.5,
        no_repeat_ngram_size=3
    )
    output_text = tokenizer.decode(output_ids[0], skip_special_tokens=True)
    if "Agent:" in output_text:
        return output_text.split("Agent:")[-1].strip()
    return output_text.strip()

@router.post("/vchat")
async def chat(
    request: ChatRequest,
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
    refresh_token: str = Query(None),
    db: AsyncSession = Depends(get_db)
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
                    raise HTTPException(status_code=401, detail="Refresh token invalid.")
                new_token = res.json()["token"]
                payload = decode_jwt_token(new_token)

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload.")

        logger.info(f"👤 Authenticated user: {user_id}")

        # ✅ Use email instead of id if user_id is an email
        result = await db.execute(select(User).where(User.email == user_id))
        user = result.scalar_one_or_none()
        if not user or not user.file_id:
            raise HTTPException(status_code=404, detail="No file_id found for this user.")

        file_id = user.file_id
        query = request.query
        logger.info(f"🟢 Received query: {query} for file_id: {file_id}")

        index_path = os.path.join(VECTOR_DIR, f"{file_id}.index")
        docs_path = os.path.join(VECTOR_DIR, f"{file_id}_chunks.pkl")

        if not os.path.exists(index_path) or not os.path.exists(docs_path):
            return {"error": f"Vector index or chunk file not found for file_id: {file_id}"}

        index = faiss.read_index(index_path)
        with open(docs_path, "rb") as f:
            documents = pickle.load(f)

        query_vec = embedder.encode([query])
        distances, indices = index.search(query_vec, k=1)
        context = documents[indices[0][0]]
        logger.info(f"📄 Retrieved context: {context}")

        prompt = f"<s>Customer: {query}\nAgent:"
        response = generate_clean_response(prompt, model, tokenizer)
        logger.info(f"💬 Generated response: {response}")

        return {"response": response}

    except Exception as e:
        logger.error(f"❌ Chat error: {e}")
        raise HTTPException(status_code=500, detail="Chat processing failed.")
