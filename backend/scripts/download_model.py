from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_NAME = "tiiuae/falcon-rw-1b"
SAVE_PATH = "uploaded_kbs/falcon-rw-1b"

model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

model.save_pretrained(SAVE_PATH)
tokenizer.save_pretrained(SAVE_PATH)

print("✅ Model saved locally at", SAVE_PATH)
