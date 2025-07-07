import os

# HuggingFace model name or path to local directory
# MODEL_NAME = os.getenv("MODEL_NAME", "mistralai/Mistral-7B-Instruct-v0.1")
# MODEL_NAME = os.getenv("MODEL_NAME", "tiiuae/falcon-rw-1b")

MODEL_NAME = "tiiuae/falcon-rw-1b"  # or "distilgpt2"
OUTPUT_DIR = "vector_stores/falcon-rw-1b"

# Directory to store the fine-tuned model checkpoints
# OUTPUT_DIR = os.getenv("OUTPUT_DIR", "training/checkpoints/mistral-finetuned")

# Path to the structured JSONL training data
TRAIN_JSONL_PATH = os.getenv("TRAIN_JSONL_PATH", "training/data/train.jsonl")