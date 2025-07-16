import os
import subprocess
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_NAME = "tiiuae/falcon-rw-1b"
REQUIRED_MEMORY_MB = 4000

# 🛠 Dynamically resolve path to save model parallel to training/
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))              # training/
SAVE_PATH = os.path.abspath(os.path.join(CURRENT_DIR, "../vector_stores/falcon-rw-1b"))

def check_gpu_memory():
    if not torch.cuda.is_available():
        print("⚠️ CUDA GPU not available. Running in CPU mode.")
        return None
    try:
        result = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.free", "--format=csv,nounits,noheader"]
        )
        free_memory = int(result.decode("utf-8").strip().split('\n')[0])
        print(f"🧠 Free GPU Memory: {free_memory} MB")
        return free_memory
    except Exception as e:
        print(f"⚠️ Could not detect GPU memory: {e}")
        return None

def model_already_downloaded(save_path):
    return os.path.exists(os.path.join(save_path, "pytorch_model.bin"))

def download_model_locally(model_name=MODEL_NAME, save_path=SAVE_PATH):
    print(f"🔄 Checking if model exists at: {save_path}")

    if model_already_downloaded(save_path):
        print("✅ Model already exists locally. Skipping download.")
        return

    free_gpu_memory = check_gpu_memory()
    if free_gpu_memory is not None and free_gpu_memory < REQUIRED_MEMORY_MB:
        print(f"❌ Insufficient GPU memory ({free_gpu_memory} MB). Requires at least {REQUIRED_MEMORY_MB} MB.")
        return

    try:
        os.makedirs(save_path, exist_ok=True)

        tokenizer = AutoTokenizer.from_pretrained(model_name)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        model = AutoModelForCausalLM.from_pretrained(model_name)

        tokenizer.save_pretrained(save_path)
        model.save_pretrained(save_path)

        print(f"✅ Model and tokenizer saved to: {save_path}")

    except Exception as e:
        print(f"❌ Error downloading model: {e}")

# Run the download
if __name__ == "__main__":
    download_model_locally()
