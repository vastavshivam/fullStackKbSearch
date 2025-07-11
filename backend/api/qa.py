# api/qa.py
from fastapi import APIRouter, HTTPException
from models.schemas import AskRequest, AskResponse
from utils.embed_store import load_index, embed_question,query_embeddings
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

from utils.embed_store import VECTOR_DIR
import os
import json
from fastapi import Request
from difflib import get_close_matches

router = APIRouter()

LLM_MODEL = "tiiuae/falcon-rw-1b"
tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL)
model = AutoModelForCausalLM.from_pretrained(LLM_MODEL)

STATIC_DATA_PATHS = [
    os.path.join("training", "data", "fine_tune.jsonl"),
    os.path.join("training", "data", "train.jsonl"),
]

def load_static_qa():
    qa_pairs = []
    for path in STATIC_DATA_PATHS:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        item = json.loads(line)
                        qa_pairs.append({
                            "prompt": item.get("prompt", ""),
                            "response": item.get("response", "")
                        })
                    except Exception:
                        continue
    return qa_pairs

@router.post("/ask", response_model=AskResponse)
async def ask_question(data: AskRequest):
    file_id = data.file_id
    question = data.question

    vector_path = os.path.join(VECTOR_DIR, f"{file_id}.index")
    if not os.path.exists(vector_path):
        raise HTTPException(status_code=404, detail="Vector index not found for this file")

    index, chunks = load_index(file_id)
    q_embedding = embed_question(question)
    D, I = index.search(q_embedding, k=3)

    retrieved = [chunks[i] for i in I[0]]
    context = "\n".join(retrieved)
    prompt = f"Context:\n{context}\n\nUser: {question}\nAI:"

    inputs = tokenizer(prompt, return_tensors="pt")
    output = model.generate(**inputs, max_new_tokens=150)
    answer = tokenizer.decode(output[0], skip_special_tokens=True)

    return AskResponse(answer=answer.split("AI:")[-1].strip())


@router.post("/v1/ask", response_model=AskResponse)
async def ask_question_v1(request: AskRequest):
    try:
        top_chunks = query_embeddings(request.file_id, request.question, top_k=5)
        context = "\n".join(top_chunks)
        prompt = f"Context:\n{context}\n\nUser: {request.question}\n\nAI:"

        inputs = tokenizer(prompt, return_tensors="pt")
        outputs = model.generate(**inputs, max_new_tokens=150, do_sample=True)
        answer = tokenizer.decode(outputs[0], skip_special_tokens=True)

        return {"answer": answer.split("AI:")[-1].strip()}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ Failed: {str(e)}")

@router.post("/static-chat")
async def static_chat(request: Request):
    data = await request.json()
    question = data.get("question", "")
    qa_pairs = load_static_qa()
    prompts = [q["prompt"] for q in qa_pairs]
    match = get_close_matches(question, prompts, n=1, cutoff=0.5)
    if match:
        for q in qa_pairs:
            if q["prompt"] == match[0]:
                return {"answer": q["response"]}
    return {"answer": "Sorry, I couldn't find an answer to that question."}
