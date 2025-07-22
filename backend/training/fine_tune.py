import os
import json
import asyncio
import logging
import redis
import uuid
import jwt
import pandas as pd

from datasets import Dataset, load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
    TextIteratorStreamer,
    pipeline
)
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import JSONResponse
from threading import Thread
from langchain_community.chat_message_histories import RedisChatMessageHistory

# Logging setup
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

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


@app.post("/auth/token")
async def generate_token(request: Request):
    log.info("Received request for token generation")
    body = await request.json()
    user_id = body.get("user_id")
    log.info(f"user_id received: {user_id}")
    if not user_id:
        return JSONResponse(status_code=400, content={"error": "Missing user_id"})
    token = jwt.encode({"user_id": user_id}, JWT_SECRET, algorithm="HS256")
    log.info(f"Generated token for user_id {user_id}")
    return {"token": token}


def auto_detect_fields(df):
    text_cols = [col for col in df.columns if 'complaint' in col.lower() or 'text' in col.lower()]
    response_cols = [col for col in df.columns if 'response' in col.lower() or 'status' in col.lower() or 'remark' in col.lower()]
    return text_cols[0], response_cols[0] if response_cols else None


def summarize_response(text):
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    result = summarizer(text[:1024], max_length=60, min_length=20, do_sample=False)
    return result[0]['summary_text']


def convert_to_jsonl(file_path, output_path):
    log.info(f"Converting {file_path} to {output_path}")
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
    log.info(f"Auto-detected prompt: {prompt_col}, response: {response_col}")

    records = []
    for _, row in df.iterrows():
        prompt = row[prompt_col]
        response = row[response_col] if response_col and pd.notna(row[response_col]) else summarize_response(str(row))
        records.append({"prompt": str(prompt), "response": str(response)})

    with open(output_path, "w") as f:
        for r in records:
            json.dump(r, f)
            f.write("\n")
    log.info("Conversion complete")
    return output_path


def fine_tune(model_name=MODEL_NAME, jsonl_path="training/data/fine_tune.jsonl"):
    """
    Standard Trainer-based fine-tuning
    """
    log.info(f"Starting fine-tuning with model: {model_name} and data: {jsonl_path}")
    with open(jsonl_path, 'r') as f:
        data = [json.loads(line) for line in f.readlines()]
    log.info(f"Loaded {len(data)} training records")

    dataset = Dataset.from_list(data)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name)
    log.info("Model and tokenizer loaded")

    def tokenize(example):
        return tokenizer("<s>" + example["prompt"] + "\n" + example["response"] + "</s>", truncation=True)

    tokenized = dataset.map(tokenize)
    log.info("Tokenization complete")

    args = TrainingArguments(
        output_dir="training/checkpoints",
        per_device_train_batch_size=2,
        num_train_epochs=2,
        logging_dir="./logs",
        logging_steps=10,
        save_total_limit=1,
        save_strategy="epoch",
        pad_token_id=tokenizer.eos_token_id
    )

    trainer = Trainer(model=model, args=args, train_dataset=tokenized)
    log.info("Trainer initialized. Starting training...")
    trainer.train()
    log.info("Training complete")


def fine_tune_with_ppo(model_name=MODEL_NAME, jsonl_path="training/data/fine_tune_reward.jsonl"):
    """
    PPO fine-tuning with TRL
    """
    log.info(f"Starting TRL PPO fine-tuning with model: {model_name} and data: {jsonl_path}")

    import torch
    from trl import PPOTrainer, PPOConfig, AutoModelForCausalLMWithValueHead

    dataset = load_dataset("json", data_files=jsonl_path)["train"]
    log.info(f"Loaded {len(dataset)} records")

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLMWithValueHead.from_pretrained(model_name)
    log.info("Tokenizer and model with value head loaded")

    config = PPOConfig(
        model_name=model_name,
        learning_rate=1.41e-5,
        batch_size=2,
        log_with=None,
    )

    ppo_trainer = PPOTrainer(
        model=model,
        tokenizer=tokenizer,
        config=config,
    )

    generation_kwargs = {
        "max_new_tokens": 50,
        "do_sample": True,
        "top_k": 50,
        "top_p": 0.95,
        "pad_token_id": tokenizer.eos_token_id,
    }

    log.info("Starting PPO training loop...")
    for record in dataset:
        prompt = record["prompt"]
        response = record["response"]
        reward = record.get("reward", 0.0)

        query_tensor = tokenizer(prompt, return_tensors="pt").input_ids.to(ppo_trainer.accelerator.device)

        response_tensor = ppo_trainer.model.generate(
            query_tensor,
            **generation_kwargs,
        )

        response_text = tokenizer.decode(response_tensor[0], skip_special_tokens=True)
        rewards = torch.tensor([reward]).to(ppo_trainer.accelerator.device)

        log.info("-----------")
        log.info(f"Prompt: {prompt}")
        log.info(f"Generated response: {response_text}")
        log.info(f"Reward: {reward}")

        ppo_trainer.step(
            queries=[query_tensor.squeeze(0)],
            responses=[response_tensor.squeeze(0)],
            rewards=rewards,
        )

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)

    log.info("PPO fine-tuning complete and model saved.")


@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    log.info("WebSocket connection initiated")
    token = websocket.query_params.get("token")
    user_id = verify_jwt(token)
    log.info(f"Authenticated user_id: {user_id}")
    await websocket.accept()
    session_id = str(uuid.uuid4())
    log.info(f"Session ID: {session_id}")

    try:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
        memory = RedisChatMessageHistory(session_id=session_id, url=REDIS_URL)
        log.info("Model, tokenizer, and Redis memory initialized")

        while True:
            user_input = await websocket.receive_text()
            log.info(f"User message: {user_input}")
            memory.add_user_message(user_input)

            history_msgs = memory.messages[-5:]
            history_text = "\n".join([f"{m.type.upper()}: {m.content}" for m in history_msgs])
            full_prompt = f"Here is the recent chat history:\n{history_text}\n\nUser: {user_input}\nAssistant:"
            log.info("Prompt constructed")

            inputs = tokenizer(full_prompt, return_tensors="pt")
            streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)

            def generate():
                log.info("Starting token generation")
                model.generate(**inputs, streamer=streamer, max_new_tokens=150, do_sample=True)

            thread = Thread(target=generate)
            thread.start()

            response_text = ""
            async for token in streamer:
                response_text += token
                await websocket.send_text(token)

            memory.add_ai_message(response_text)
            log.info(f"AI response: {response_text}")
            await websocket.send_text("[END]")

    except WebSocketDisconnect:
        log.warning("WebSocket disconnected")
    except Exception as e:
        log.error(f"Error: {str(e)}")
        await websocket.send_text(f"[ERROR]: {str(e)}")
        await websocket.close()


if __name__ == "__main__":
    # Uncomment whichever you want to run:
    # fine_tune()
    # fine_tune_with_ppo()
    pass
