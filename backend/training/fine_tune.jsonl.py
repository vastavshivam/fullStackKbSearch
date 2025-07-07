import os
import json
import pandas as pd
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    pipeline,
)

SUPPORTED_EXT = ["csv", "xlsx", "json"]
SUMMARIZER_MODEL = "facebook/bart-large-cnn"  # or t5-small for local

def auto_detect_fields(df):
    prompt_col = next((col for col in df.columns if 'complaint' in col.lower() or 'text' in col.lower()), None)
    response_col = next((col for col in df.columns if 'response' in col.lower() or 'status' in col.lower()), None)
    if not prompt_col:
        raise ValueError("Prompt column not detected.")
    return prompt_col, response_col

def summarize_response(text):
    summarizer = pipeline("summarization", model=SUMMARIZER_MODEL)
    return summarizer(text[:1024], max_length=60, min_length=20, do_sample=False)[0]['summary_text']

def convert_to_jsonl(file_path, output_path="training/data/auto_parsed.jsonl"):
    ext = file_path.split('.')[-1].lower()
    if ext not in SUPPORTED_EXT:
        raise ValueError(f"Unsupported file extension: .{ext}")

    if ext == "csv":
        df = pd.read_csv(file_path)
    elif ext == "xlsx":
        df = pd.read_excel(file_path)
    else:  # JSON
        df = pd.read_json(file_path)

    prompt_col, response_col = auto_detect_fields(df)
    records = []

    for _, row in df.iterrows():
        prompt = str(row[prompt_col])
        raw_response = row[response_col] if response_col and pd.notna(row[response_col]) else None
        response = raw_response if raw_response else summarize_response(prompt)
        records.append({"prompt": prompt.strip(), "response": response.strip()})

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for r in records:
            json.dump(r, f)
            f.write("\n")
    return output_path

def fine_tune(
    model_name="mistralai/Mistral-7B-Instruct-v0.1",
    jsonl_path="training/data/auto_parsed.jsonl",
    output_dir="training/checkpoints/fine-tuned"
):
    with open(jsonl_path, "r", encoding="utf-8") as f:
        data = [json.loads(line) for line in f.readlines()]

    dataset = Dataset.from_list(data)
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(model_name, trust_remote_code=True)

    def tokenize(example):
        return tokenizer(
            f"<s>Prompt: {example['prompt']}\n\nResponse: {example['response']}</s>",
            truncation=True,
            padding="max_length",
            max_length=512,
        )

    tokenized_dataset = dataset.map(tokenize, batched=True)

    training_args = TrainingArguments(
        output_dir=output_dir,
        per_device_train_batch_size=2,
        num_train_epochs=3,
        logging_dir="./logs",
        logging_steps=20,
        save_strategy="epoch",
        save_total_limit=1,
        evaluation_strategy="no"
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset
    )

    trainer.train()
    print(f"✅ Model fine-tuned and saved at: {output_dir}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, required=True, help="Path to training .xlsx/.csv/.json file")
    parser.add_argument("--model", type=str, default="mistralai/Mistral-7B-Instruct-v0.1")
    parser.add_argument("--out", type=str, default="training/checkpoints/fine-tuned")
    args = parser.parse_args()

    jsonl_path = convert_to_jsonl(args.file)
    fine_tune(model_name=args.model, jsonl_path=jsonl_path, output_dir=args.out)
