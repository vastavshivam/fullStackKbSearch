import os
import json
import asyncio
from datasets import load_dataset, Dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer, DataCollatorForLanguageModeling
from transformers import TextIteratorStreamer
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, Request, APIRouter, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import HTMLResponse, JSONResponse
from threading import Thread
import redis
import uuid
import jwt
from langchain.memory import RedisChatMessageHistory
from langchain.schema import messages_from_dict, messages_to_dict
from langchain.prompts import ChatPromptTemplate

import pandas as pd
import json
import os
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer
from datasets import Dataset
from transformers import pipeline
from utils.embed_store import chunk_text, save_embeddings, load_index, embed_question, query_embeddings
 

MODEL_NAME = os.getenv("MODEL_NAME", "tiiuae/falcon-rw-1b")
DATA_PATH = "training/data/train.jsonl"
OUTPUT_DIR = "training/checkpoints/fine-tuned-output"
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")

app = FastAPI()
redis_client = redis.Redis.from_url(REDIS_URL)

 
def verify_jwt(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload["user_id"]
    except jwt.ExpiredSignatureError:
        raise WebSocketDisconnect(code=4001)
    except jwt.InvalidTokenError:
        raise WebSocketDisconnect(code=4002)

# router = APIRouter()

@app.post("/auth/token")
async def generate_token(request: Request):
    body = await request.json()
    user_id = body.get("user_id")
    if not user_id:
        return JSONResponse(status_code=400, content={"error": "Missing user_id"})
    token = jwt.encode({"user_id": user_id}, JWT_SECRET, algorithm="HS256")
    return {"token": token}


def load_data():
    with open(DATA_PATH, 'r') as f:
        data = [json.loads(line) for line in f if line.strip()]
    formatted = [{"text": f"<s>[INST] {ex['prompt']} [/INST] {ex['response']} </s>"} for ex in data]
    return Dataset.from_list(formatted)


def tokenize(example, tokenizer):
    return tokenizer(example["text"], truncation=True, padding="max_length", max_length=512)


# def fine_tune():
#     tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, use_fast=True)
#     model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)

#     dataset = load_data()
#     tokenized_dataset = dataset.map(lambda x: tokenize(x, tokenizer), batched=True)
#     data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

#     training_args = TrainingArguments(
#         output_dir=OUTPUT_DIR,
#         per_device_train_batch_size=1,
#         gradient_accumulation_steps=2,
#         num_train_epochs=3,
#         save_steps=50,
#         logging_steps=25,
#         learning_rate=5e-5,
#         weight_decay=0.01,
#         save_total_limit=1,
#         report_to="none"
#     )

#     trainer = Trainer(
#         model=model,
#         args=training_args,
#         train_dataset=tokenized_dataset,
#         tokenizer=tokenizer,
#         data_collator=data_collator
#     )

#     trainer.train()
#     trainer.save_model(OUTPUT_DIR)
#     tokenizer.save_pretrained(OUTPUT_DIR)


def auto_detect_fields(df):
    text_cols = [col for col in df.columns if 'complaint' in col.lower() or 'text' in col.lower()]
    response_cols = [col for col in df.columns if 'response' in col.lower() or 'status' in col.lower() or 'remark' in col.lower()]
    return text_cols[0], response_cols[0] if response_cols else None

def summarize_response(text):
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    result = summarizer(text[:1024], max_length=60, min_length=20, do_sample=False)
    return result[0]['summary_text']

def convert_to_jsonl(file_path, output_path):
    ext = file_path.split('.')[-1]
    if ext == "csv":
        df = pd.read_csv(file_path)
    elif ext == "xlsx":
        df = pd.read_excel(file_path)
    elif ext == "json":
        df = pd.read_json(file_path)
    else:
        raise ValueError("Unsupported format")

    prompt_col, response_col = auto_detect_fields(df)
    records = []
    for _, row in df.iterrows():
        prompt = row[prompt_col]
        response = row[response_col] if response_col and pd.notna(row[response_col]) else summarize_response(str(row))
        records.append({"prompt": str(prompt), "response": str(response)})

    with open(output_path, "w") as f:
        for r in records:
            json.dump(r, f)
            f.write("\n")
    return output_path

# def fine_tune(model_name="tiiuae/falcon-7b-instruct", jsonl_path="training/data/fine_tune.jsonl"): 
def fine_tune(model_name=MODEL_NAME, jsonl_path="training/data/fine_tune.jsonl"): 
    print(f"Starting fine-tuning with model: {model_name} and data: {jsonl_path}")
    with open(jsonl_path, 'r') as f:
        data = [json.loads(line) for line in f.readlines()]

    dataset = Dataset.from_list(data)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name)

    def tokenize(example):
        return tokenizer("<s>" + example["prompt"] + "\n" + example["response"] + "</s>", truncation=True)

    tokenized = dataset.map(tokenize)
    args = TrainingArguments(
        output_dir="training/checkpoints",
        per_device_train_batch_size=2,
        num_train_epochs=2,
        logging_dir="./logs",
        logging_steps=10,
        save_total_limit=1,
        save_strategy="epoch",
        pad_token_id=tokenizer.eos_token_id # Use EOS token as padding

    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=tokenized
    )
    trainer.train()



# 🔁 Token-level streaming response over WebSocket with LangChain memory, JWT auth, and context injection
@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    token = websocket.query_params.get("token")
    user_id = verify_jwt(token)
    await websocket.accept()
    session_id = str(uuid.uuid4())
    try:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
        memory = RedisChatMessageHistory(session_id=session_id, url=REDIS_URL)

        while True:
            user_input = await websocket.receive_text()
            memory.add_user_message(user_input)

            # Inject last 5 messages as context
            history_msgs = memory.messages[-5:]  # list of BaseMessage
            history_text = "\n".join([f"{m.type.upper()}: {m.content}" for m in history_msgs])
            full_prompt = f"Here is the recent chat history:\n{history_text}\n\nUser: {user_input}\nAssistant:"

            inputs = tokenizer(full_prompt, return_tensors="pt")
            streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)

            def generate():
                model.generate(**inputs, streamer=streamer, max_new_tokens=150, do_sample=True)

            thread = Thread(target=generate)
            thread.start()

            response_text = ""
            async for token in streamer:
                response_text += token
                await websocket.send_text(token)

            memory.add_ai_message(response_text)
            await websocket.send_text("[END]")

    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        await websocket.send_text(f"[ERROR]: {str(e)}")
        await websocket.close()


if __name__ == "__main__":
    fine_tune()
