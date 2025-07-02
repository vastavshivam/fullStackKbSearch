import os
import json
from datasets import load_dataset, Dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer, DataCollatorForLanguageModeling

MODEL_NAME = "mistralai/Mistral-7B-Instruct-v0.1"  # or your own
DATA_PATH = "training/data/train.jsonl"
OUTPUT_DIR = "training/checkpoints/mistral-finetuned"

# Load and preprocess dataset
def load_data():
    with open(DATA_PATH, 'r') as f:
        data = [json.loads(line) for line in f if line.strip()]

    formatted = [{"text": f"<s>[INST] {ex['prompt']} [/INST] {ex['response']} </s>"} for ex in data]
    return Dataset.from_list(formatted)

# Tokenization function
def tokenize(example, tokenizer):
    return tokenizer(example["text"], truncation=True, padding="max_length", max_length=512)

def fine_tune():
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, use_fast=True)
    model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)

    dataset = load_data()
    tokenized_dataset = dataset.map(lambda x: tokenize(x, tokenizer), batched=True)

    data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        num_train_epochs=3,
        save_steps=100,
        logging_steps=50,
        learning_rate=5e-5,
        weight_decay=0.01,
        save_total_limit=2,
        report_to="none"
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset,
        tokenizer=tokenizer,
        data_collator=data_collator
    )

    trainer.train()
    trainer.save_model(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)

if __name__ == "__main__":
    fine_tune()
